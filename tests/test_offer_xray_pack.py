"""Offer X-ray pack (task B4): the template model passes every golden check."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from packs.offer_xray.golden.checks import ALL_CHECKS, base_spec, set_var, zero_volatility
from packs.offer_xray.template_model import simulate, story_lines

PACK = Path(__file__).resolve().parents[1] / "packs" / "offer_xray"


@pytest.mark.parametrize("check", ALL_CHECKS, ids=lambda c: c.__name__)
def test_template_passes_golden(check):
    check(simulate)


def test_early_exit_story_mentions_clawback():
    spec = zero_volatility(years=2)
    set_var(spec, "A.joining_bonus", 150_000.0)
    set_var(spec, "tenure_months", 8.0)
    r = simulate("A", spec, np.random.default_rng(0), 5)
    lines = story_lines(r["story"], 0, "Nimbus")
    assert any("switched jobs in month 8" in x for x in lines)
    assert any("repaid a Rs 1.5L joining bonus" in x for x in lines)


def test_layoff_is_not_a_voluntary_exit():
    spec = base_spec()
    for e in spec["events"]:
        e["prob_per_year"] = 0.9
    r = simulate("A", spec, np.random.default_rng(3), 2000)["story"]
    laid = r["layoff_month"] > 0
    assert laid.any()
    assert np.all(r["voluntary_exit"][laid] == 0)
    assert np.all(r["clawback_paid"][laid] == 0)


def test_pack_files_are_valid():
    questions = json.loads((PACK / "questions.json").read_text())
    assert 1 <= len(questions["questions"]) <= questions["max_questions"] == 5
    defaults = json.loads((PACK / "defaults.json").read_text())
    for name, v in defaults["variables"].items():
        assert v["source_ref"], name
    widgets = json.loads((PACK / "widgets.json").read_text())
    assert widgets["primary_metric"] == base_spec()["metrics"]["primary"]
