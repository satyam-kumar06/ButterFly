"""Golden and invariant checks for ANY Offer X-ray model (template or Ultra-written).

Each check takes a `simulate` function. They are run:
  * against the template model in this repo (tests/test_offer_xray_pack.py), and
  * against Ultra's model.py inside the sandbox (test_golden.py is copied in
    next to it automatically; Ultra never writes or edits these).

Golden values come from the hand-worked oracle mocks/expected_payroll.json.
"""

from __future__ import annotations

import copy
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
# In the sandbox the files sit next to each other; in the repo they live in mocks/.
_CANDIDATES = [HERE, HERE.parents[2] / "mocks"]


def _load(name: str) -> dict:
    for d in _CANDIDATES:
        if (d / name).exists():
            return json.loads((d / name).read_text(encoding="utf-8"))
    raise FileNotFoundError(name)


def base_spec() -> dict:
    return _load("spec_offer_xray.json")


def payroll() -> dict:
    return _load("expected_payroll.json")


def set_var(spec: dict, name: str, value) -> dict:
    """Replace a variable with a fixed value (adds it if missing)."""
    for v in spec["variables"]:
        if v["name"] == name:
            v.clear()
            v.update(
                name=name,
                kind="fixed",
                value=value,
                unit="x",
                source="user",
                source_ref="golden test",
                confirmed=True,
                editable=True,
                sweep_range=None,
            )
            return spec
    spec["variables"].append(
        dict(
            name=name,
            kind="fixed",
            value=value,
            unit="x",
            source="user",
            source_ref="golden test",
            confirmed=True,
            editable=True,
            sweep_range=None,
        )
    )
    return spec


def zero_volatility(spec: dict | None = None, *, years: int = 1) -> dict:
    """Everything certain: stay the whole horizon, no hikes, no layoffs, full payout."""
    s = copy.deepcopy(spec or base_spec())
    s["horizon_years"] = years
    s["events"] = [dict(e, prob_per_year=0.0) for e in s.get("events", [])] or [
        {
            "name": "layoff",
            "prob_per_year": 0.0,
            "effect": "none",
            "source": "user",
            "source_ref": "golden test",
            "confirmed": True,
        }
    ]
    for name, value in [
        ("tenure_months", 999),
        ("annual_hike", 0.0),
        ("A.variable_payout", 1.0),
        ("B.variable_payout", 1.0),
        ("A.joining_bonus", 0.0),
        ("A.equity_units", 0.0),
        ("financial_year", payroll()["financial_year"]),
        ("tax_regime", "new"),
    ]:
        set_var(s, name, value)
    return s


def _run(simulate, spec, option, n=200, seed=1):
    return simulate(option, spec, np.random.default_rng(seed), n)


# ---------------------------------------------------------------------------
# Golden: reproduce the hand-worked payroll to the rupee
# ---------------------------------------------------------------------------


def check_year_one_net_matches_oracle(simulate) -> None:
    oracle = {
        c["option"]: c["annual_net"] for c in payroll()["annual_cases"] if c["payout_fraction"] == 1
    }
    spec = zero_volatility()
    for opt in ("A", "B"):
        r = _run(simulate, spec, opt)
        got = r["cash_in_hand"][:, -1]
        assert np.allclose(got, oracle[opt], atol=1.0), (opt, got[0], oracle[opt])
        assert np.allclose(r["metrics"]["cumulative_in_hand"], oracle[opt], atol=1.0)


def check_monthly_slip_quarters(simulate) -> None:
    """First quarter = three ordinary months from the oracle's April slip."""
    slips = {(s["option"], s["month"]): s for s in payroll()["monthly_slips"]}
    spec = zero_volatility()
    for opt in ("A", "B"):
        q1 = _run(simulate, spec, opt)["cash_in_hand"][:, 0]
        assert np.allclose(q1, 3 * slips[(opt, "April")]["net"], atol=1.0), (opt, q1[0])


def check_clawback_cases(simulate) -> None:
    for case in payroll()["clawback_cases"]:
        spec = zero_volatility(years=2)
        set_var(spec, "A.joining_bonus", 150_000.0)
        set_var(spec, "tenure_months", float(case["exit_month"]))
        r = _run(simulate, spec, case["option"])
        assert np.allclose(r["metrics"]["clawback_paid"], case["expected_repayment"]), case


def check_equity_cases(simulate) -> None:
    for case in payroll()["equity_cases"]:
        spec = zero_volatility(years=2)
        set_var(spec, "A.equity_units", 400.0)
        set_var(spec, "A.equity_reference_price", float(case["exit_price"]))
        set_var(spec, "A.equity_zero_chance", 0.0)
        set_var(spec, "A.equity_price_sigma", 0.0)
        set_var(spec, "tenure_months", float(case["exit_month"]))
        r = _run(simulate, spec, case["option"])
        assert np.allclose(r["metrics"]["equity_value"], case["expected_gross_value"]), case


# ---------------------------------------------------------------------------
# Invariants (from the spec doc's fixed checklist)
# ---------------------------------------------------------------------------


def check_shapes_and_finite(simulate) -> None:
    spec = base_spec()
    q = spec["horizon_years"] * 4
    for opt in ("A", "B"):
        r = _run(simulate, spec, opt, n=500)
        assert r["cash_in_hand"].shape == (500, q)
        assert np.isfinite(r["cash_in_hand"]).all()
        for name, arr in r["metrics"].items():
            assert arr.shape == (500,), name
            assert np.isfinite(arr).all(), name
        assert spec["metrics"]["primary"] in r["metrics"]


def check_higher_salary_never_lowers_cash(simulate) -> None:
    spec = zero_volatility(years=2)
    low = _run(simulate, spec, "B")["metrics"]["cumulative_in_hand"]
    rich = copy.deepcopy(spec)
    for v in rich["variables"]:
        if v["name"] == "B.annual_special_allowance":
            v["value"] = float(v["value"]) + 100_000
    high = _run(simulate, rich, "B")["metrics"]["cumulative_in_hand"]
    assert np.all(high >= low)


def check_common_random_numbers(simulate) -> None:
    """Same seed => the shared tenure draw is identical for both options."""
    spec = base_spec()
    set_var(spec, "tenure_months", 0.0)  # placeholder, replaced below
    for v in spec["variables"]:
        if v["name"] == "tenure_months":
            v.update(kind="distribution", dist={"type": "uniform", "low": 6, "high": 40})
            v.pop("value", None)
    a = _run(simulate, spec, "A", n=300, seed=9)["story"]
    b = _run(simulate, spec, "B", n=300, seed=9)["story"]
    no_layoff = (a["layoff_month"] == 0) & (b["layoff_month"] == 0)
    assert np.array_equal(a["exit_month"][no_layoff], b["exit_month"][no_layoff])


def check_speed(simulate) -> None:
    spec = base_spec()
    t = time.perf_counter()
    for opt in ("A", "B"):
        _run(simulate, spec, opt, n=10_000)
    assert time.perf_counter() - t < 5.0


ALL_CHECKS = [
    check_year_one_net_matches_oracle,
    check_monthly_slip_quarters,
    check_clawback_cases,
    check_equity_cases,
    check_shapes_and_finite,
    check_higher_salary_never_lowers_cash,
    check_common_random_numbers,
    check_speed,
]
