"""Rules with receipts (task B3): forklib must reproduce the hand-worked payroll
oracle in mocks/expected_payroll.json to the rupee. The oracle is literal data,
written by hand; never regenerate it from this code."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from forklib import clawback_due, esop_value, vested_units
from forklib.rules import gratuity, pf_contribution, professional_tax
from forklib.rules.india_tax import income_tax, slab_tax, tax_before_cess, taxable_income
from mocks.demo_data import OFFERS

ROOT = Path(__file__).resolve().parents[1]
PAYROLL = json.loads((ROOT / "mocks" / "expected_payroll.json").read_text())
FY = PAYROLL["financial_year"]


def fixed_gross(option: str) -> float:
    o = OFFERS[option]
    return o["annual_basic"] + o["annual_hra"] + o["annual_special_allowance"]


@pytest.mark.parametrize("case", PAYROLL["annual_cases"], ids=lambda c: c["id"])
def test_annual_tax_matches_oracle(case):
    o = OFFERS[case["option"]]
    gross = fixed_gross(case["option"]) + case["payout_fraction"] * o["annual_variable_target"]
    assert gross == pytest.approx(case["annual_gross"], abs=1)
    taxable = taxable_income(case["annual_gross"], "new", FY)
    assert taxable == case["taxable_rounded"]
    assert slab_tax(taxable, "new", FY) == pytest.approx(case["slab_tax"])
    assert tax_before_cess(taxable, "new", FY) == pytest.approx(case["tax_after_rebate_relief"])
    tax = income_tax(taxable, "new", FY)
    assert tax == case["annual_tax"]
    net = (
        case["annual_gross"]
        - tax
        - PAYROLL["annual_employee_pf"]
        - PAYROLL["annual_professional_tax"]
    )
    assert net == pytest.approx(case["annual_net"], abs=0.01)


STATE = {"A": "karnataka", "B": "maharashtra"}
MONTH = {"April": 4, "February": 2, "March": 3}


@pytest.mark.parametrize("slip", PAYROLL["monthly_slips"], ids=lambda s: s["id"])
def test_monthly_slip_pf_and_pt(slip):
    o = OFFERS[slip["option"]]
    pf = pf_contribution(o["annual_basic"] / 12, ceiling=15_000)
    assert pf == slip["employee_pf"] == o["employee_pf_monthly"]
    pt = professional_tax(STATE[slip["option"]], slip["gross"], MONTH[slip["month"]])
    assert pt == slip["professional_tax"]
    net = slip["gross"] - pf - pt - slip["tds"]
    assert net == pytest.approx(slip["net"], abs=0.01)


def test_twelve_slips_reconcile_to_annual_target_net():
    # 10 ordinary months + February + March reproduce the 100%-variable annual net
    for opt in ("A", "B"):
        slips = {s["month"]: s for s in PAYROLL["monthly_slips"] if s["option"] == opt}
        total = 10 * slips["April"]["net"] + slips["February"]["net"] + slips["March"]["net"]
        target = next(
            c for c in PAYROLL["annual_cases"] if c["option"] == opt and c["payout_fraction"] == 1
        )
        assert total == pytest.approx(target["annual_net"], abs=0.05)


@pytest.mark.parametrize("case", PAYROLL["clawback_cases"], ids=str)
def test_clawback_oracle(case):
    o = OFFERS[case["option"]]
    due = clawback_due(o["joining_bonus"], o["clawback_months"], np.array([case["exit_month"]]))
    assert due[0] == case["expected_repayment"]


@pytest.mark.parametrize("case", PAYROLL["equity_cases"], ids=str)
def test_equity_oracle(case):
    o = OFFERS[case["option"]]
    args = (o["equity_units"], o["equity_cliff_months"], o["equity_vesting_months"])
    exit_m = np.array([case["exit_month"]])
    assert vested_units(*args, exit_m)[0] == case["vested_units"]
    value = esop_value(
        o["equity_units"],
        o["equity_strike_price"],
        o["equity_cliff_months"],
        o["equity_vesting_months"],
        exit_m,
        case["exit_price"],
    )
    assert value[0] == pytest.approx(case["expected_gross_value"])


# --- independent edge cases ----------------------------------------------------


@pytest.mark.parametrize(
    ("taxable", "expected"),
    [
        (0, 0),
        (400_000, 0),
        (1_200_000, 0),  # exactly at the rebate limit
        (1_200_010, 10),  # relief caps tax at 10; x 1.04 = 10.4 -> nearest Rs 10 = 10
        (1_250_000, 52_000),  # relief binds: min(67,500, 50,000) x 1.04
        (1_300_000, 78_000),  # 75,000 x 1.04; relief cap 100,000 does not bind
        # 20k + 40k + 60k + 80k + 100k + 30% of 1L = 3,30,000; x 1.04
        (2_500_000, 343_200),
    ],
)
def test_new_regime_boundaries(taxable, expected):
    assert income_tax(taxable, "new", "2026-27") == expected


def test_old_regime_and_years():
    assert income_tax(500_000, "old", "2025-26") == 0  # 87A old regime
    assert income_tax(1_000_000, "old", "2025-26") == round(112_500 * 1.04 / 10) * 10
    assert income_tax(1_300_000, "new", "2025-26") == income_tax(1_300_000, "new", "2026-27")
    with pytest.raises(ValueError):
        income_tax(1_000_000, "new", "2019-20")


@pytest.mark.parametrize(
    ("taxable", "expected"),
    [
        # 60L: 3,00,000 + 30% of 36L = 13,80,000; +10% surcharge = 15,18,000; x 1.04
        (6_000_000, 1_578_720),
        # 50.1L: 10,83,000 + 10% = 11,91,300, but relief caps it at
        # tax at 50L (10,80,000) + 10,000 over = 10,90,000; x 1.04
        (5_010_000, 1_133_600),
        (5_000_000, 1_123_200),  # exactly at the threshold: no surcharge
    ],
)
def test_surcharge_and_marginal_relief(taxable, expected):
    assert income_tax(taxable, "new", "2026-27") == expected


def test_tax_is_monotonic_in_income():
    incomes = np.arange(0, 30_000_000, 1_000)
    tax = income_tax(incomes, "new", "2026-27")
    assert np.all(np.diff(tax) >= 0)
    # and never takes more than the extra income just above the rebate limit
    near = np.arange(1_200_000, 1_300_000, 10)
    assert np.all(tax_before_cess(near, "new", "2026-27") <= near - 1_200_000)


def test_professional_tax_states():
    assert professional_tax("Bengaluru, Karnataka", 24_999, 4) == 0
    assert professional_tax("karnataka", 25_000, 4) == 200
    assert professional_tax("Pune, Maharashtra", 9_000, 4) == 175
    assert professional_tax("maharashtra", 20_000, 4, female=True) == 0
    assert professional_tax("maharashtra", 30_000, 2, female=True) == 300
    assert professional_tax_annual_both() == (2500, 2500)
    with pytest.raises(ValueError):
        professional_tax("goa", 50_000, 4)


def professional_tax_annual_both():
    from forklib.rules import annual_professional_tax

    return (
        int(annual_professional_tax("karnataka", 110_000)),
        int(annual_professional_tax("maharashtra", 105_000)),
    )


def test_gratuity_rules():
    assert gratuity(55_000, 59) == 0
    assert round(float(gratuity(55_000, 60))) == 158_654
    assert float(gratuity(55_000, 67)) == float(gratuity(55_000, 72))  # 5y7m counts as 6y
    assert float(gratuity(55_000, 13, fixed_term=True)) == pytest.approx(15 / 26 * 55_000)


def test_every_rule_module_has_a_source():
    import importlib

    names = ["india_tax", "pf", "professional_tax", "gratuity"]
    for mod in (importlib.import_module(f"forklib.rules.{n}") for n in names):
        assert mod.RULE_SOURCE
        assert "2026-10-25" in json.dumps(mod.RULE_SOURCE)
