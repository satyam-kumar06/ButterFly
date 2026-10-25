"""Fine Print pack (task B5): claim engine clause by clause, then the template model."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from forklib import PolicyState, apply_policy_to_claim, eligible_amount
from forklib.insurance import CATARACT, PREEXISTING
from mocks.demo_data import POLICIES
from packs.fine_print.golden.checks import MODEL_CHECKS, check_claim_examples
from packs.fine_print.template_model import simulate, story_lines

PACK = Path(__file__).resolve().parents[1] / "packs" / "fine_print"
A, B = POLICIES["A"], POLICIES["B"]


def one(policy, bill, room, days, day=800, condition=0, state=None, accident=False):
    st = state or PolicyState.new(policy, 1)
    pay = apply_policy_to_claim(
        np.array([bill], float),
        np.array([room], float),
        np.array([days], float),
        policy,
        st,
        admission_day=np.array([day]),
        condition=condition,
        accident=accident,
    )
    return float(pay[0]), st


def test_worked_examples_from_the_wordings():
    check_claim_examples()


@pytest.mark.parametrize("check", MODEL_CHECKS, ids=lambda c: c.__name__)
def test_template_passes_model_checks(check):
    check(simulate)


# --- one test per clause ----------------------------------------------------------


def test_initial_wait_boundary_and_accident_exemption():
    assert one(B, 50_000, 4000, 2, day=29)[0] == 0
    assert one(B, 50_000, 4000, 2, day=30)[0] == 50_000  # cover starts at the boundary
    assert one(B, 50_000, 4000, 2, day=5, accident=True)[0] == 50_000


def test_specific_and_preexisting_waits():
    day_23m, day_25m = int(23 * 365 / 12), int(25 * 365 / 12)
    assert one(B, 50_000, 4000, 2, day=day_23m, condition=CATARACT)[0] == 0
    assert one(B, 50_000, 4000, 2, day=day_25m, condition=CATARACT)[0] == 50_000
    assert one(A, 50_000, 4000, 2, day=day_25m, condition=PREEXISTING)[0] == 0  # A waits 36m
    assert one(B, 50_000, 4000, 2, day=day_25m, condition=PREEXISTING)[0] == 50_000


def test_cataract_sublimit_before_room_rule():
    # B: 75,000 per eye cap, no deductible/co-pay
    assert one(B, 120_000, 4000, 1, day=900, condition=CATARACT)[0] == 75_000
    # A: cap 40,000, then room ratio 5000/8000, then deductible 10,000, then 20% co-pay
    expected = (40_000 * 0.625 - 10_000) * 0.8
    assert one(A, 120_000, 8000, 1, day=900, condition=CATARACT)[0] == pytest.approx(expected)


def test_order_matters_deductible_after_room_rule():
    # if the deductible came first: (100000-10000)*0.625*0.8 = 45,000 (wrong)
    assert one(A, 100_000, 8000, 4)[0] == 42_000


def test_sum_insured_cap_and_restoration_only_for_later_claims():
    st = PolicyState.new(B, 1)
    p1, st = one(B, 480_000, 4000, 5, state=st)
    p2, st = one(B, 80_000, 4000, 2, state=st)  # exhausts the pool: only 20,000 left
    assert (p1, p2) == (480_000, 20_000)
    p3, st = one(B, 60_000, 4000, 2, state=st)  # later claim: restored base cover pays
    assert p3 == 60_000
    p4, st = one(B, 500_000, 4000, 2, state=st)  # restoration used once this year
    assert p4 == 440_000


def test_no_claim_bonus_and_reset():
    st = PolicyState.new(A, 1)
    st.renew(A)  # claim-free year 1
    assert st.remaining[0] == 550_000
    for _ in range(10):
        st.renew(A)
    assert st.remaining[0] == 750_000  # capped at 50%
    one(A, 20_000, 4000, 1, state=st)
    st.renew(A)
    assert st.remaining[0] == 500_000  # any paid claim resets NCB


def test_eligible_amount_is_vectorised():
    out = eligible_amount(
        np.array([100_000, 100_000]),
        np.array([8000, 4000]),
        np.array([4, 4]),
        A,
        admission_day=np.array([800, 800]),
    )
    assert out.tolist() == [42_000, 72_000]


def test_story_and_pack_files():
    spec = json.loads(
        (Path(__file__).resolve().parents[1] / "mocks" / "spec_fine_print.json").read_text()
    )
    r = simulate("A", spec, np.random.default_rng(0), 50)
    assert story_lines(r["story"], 0, "Harbor")[-1].startswith("out of pocket")
    q = json.loads((PACK / "questions.json").read_text())
    assert len(q["questions"]) <= q["max_questions"] == 5
    w = json.loads((PACK / "widgets.json").read_text())
    assert w["primary_metric"] == spec["metrics"]["primary"] and w["objective"] == "minimize"
