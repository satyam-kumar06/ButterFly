"""Indian income tax for resident individuals on salary income (task B3).

Rules are law: they are written and checked by people, never guessed by a model.
Every year's parameters carry their source. Vectorised over paths.

Method (matches docs/demo-payroll.md, the team's hand-worked oracle):
    taxable = gross salary - standard deduction, rounded to the nearest Rs 10 (s.288A)
    slab tax on taxable
    rebate u/s 87A: nil tax up to the rebate limit; just above the new-regime limit,
        marginal relief caps tax at (taxable - limit)
    + 4% health and education cess
    final tax rounded to the nearest Rs 10 (s.288B)

Out of scope (raise or document, never silently approximate): surcharge (income
above Rs 50 lakh), special-rate income, HRA and other old-regime exemptions beyond
the standard deduction, senior-citizen slabs.

Example:
    >>> int(income_tax(1_590_000 - 75_000))      # Nimbus at 100% variable
    111540
    >>> int(income_tax(taxable_income(1_304_777)))  # Kestrel at 50%: marginal relief
    30970
"""

from __future__ import annotations

import numpy as np

INF = float("inf")

# (lower, upper, rate) on taxable income
_NEW_SLABS = [
    (0, 400_000, 0.00),
    (400_000, 800_000, 0.05),
    (800_000, 1_200_000, 0.10),
    (1_200_000, 1_600_000, 0.15),
    (1_600_000, 2_000_000, 0.20),
    (2_000_000, 2_400_000, 0.25),
    (2_400_000, INF, 0.30),
]
_OLD_SLABS = [
    (0, 250_000, 0.00),
    (250_000, 500_000, 0.05),
    (500_000, 1_000_000, 0.20),
    (1_000_000, INF, 0.30),
]

_NEW = {
    "slabs": _NEW_SLABS,
    "standard_deduction": 75_000,
    "rebate_limit": 1_200_000,
    "rebate_max": 60_000,
    "marginal_relief": True,
    "cess": 0.04,
}
_OLD = {
    "slabs": _OLD_SLABS,
    "standard_deduction": 50_000,
    "rebate_limit": 500_000,
    "rebate_max": 12_500,
    "marginal_relief": False,
    "cess": 0.04,
}

RULES = {
    # Finance Act 2025 set these; Budget 2026 made no change to slabs, standard
    # deduction or the 87A rebate, so FY 2026-27 carries them forward.
    ("2025-26", "new"): _NEW,
    ("2025-26", "old"): _OLD,
    ("2026-27", "new"): _NEW,
    ("2026-27", "old"): _OLD,
}

SURCHARGE_THRESHOLD = 5_000_000

RULE_SOURCE = {
    "rule": "Income tax on salary, resident individual below 60",
    "financial_years": ["2025-26", "2026-27"],
    "sources": [
        "https://www.incometaxindia.gov.in/w/computation-of-tax-for-individual-1",
        "https://www.incometaxindia.gov.in/w/deductions-allowable-to-tax-payer",
    ],
    "notes": "Budget 2026 left slabs, Rs 75,000 standard deduction and the Rs 12 lakh "
    "87A limit unchanged for FY 2026-27 (checked 2026-10-25). Rounding per s.288A/288B.",
    "checked": "2026-10-25",
    "still_to_do": "Cross-check at least five incomes against the official tax calculator.",
}


def _rules(fy: str, regime: str) -> dict:
    try:
        return RULES[(fy, regime)]
    except KeyError:
        raise ValueError(f"no tax rules stored for FY {fy}, {regime} regime") from None


def round10(x: np.ndarray | float) -> np.ndarray:
    """Nearest multiple of 10, halves rounded up (s.288A / s.288B)."""
    return np.floor(np.asarray(x, float) / 10 + 0.5) * 10


def taxable_income(gross_salary, regime: str = "new", fy: str = "2025-26") -> np.ndarray:
    """Gross salary minus standard deduction, floored at 0 and rounded to Rs 10."""
    r = _rules(fy, regime)
    return round10(np.maximum(np.asarray(gross_salary, float) - r["standard_deduction"], 0))


def slab_tax(taxable, regime: str = "new", fy: str = "2025-26") -> np.ndarray:
    t = np.asarray(taxable, float)
    tax = np.zeros_like(t)
    for lo, hi, rate in _rules(fy, regime)["slabs"]:
        tax += np.clip(t - lo, 0, hi - lo) * rate
    return tax


def tax_before_cess(taxable, regime: str = "new", fy: str = "2025-26") -> np.ndarray:
    """Slab tax after the 87A rebate and, in the new regime, marginal relief."""
    r = _rules(fy, regime)
    t = np.asarray(taxable, float)
    tax = slab_tax(t, regime, fy)
    within = t <= r["rebate_limit"]
    tax = np.where(within, np.maximum(tax - r["rebate_max"], 0), tax)
    if r["marginal_relief"]:
        tax = np.where(~within, np.minimum(tax, t - r["rebate_limit"]), tax)
    return tax


def income_tax(taxable, regime: str = "new", fy: str = "2025-26") -> np.ndarray:
    """Final annual tax on already-computed taxable income, rounded to Rs 10."""
    t = np.asarray(taxable, float)
    if np.any(t > SURCHARGE_THRESHOLD):
        raise ValueError("income above Rs 50 lakh needs surcharge, which is out of scope")
    r = _rules(fy, regime)
    return round10(tax_before_cess(t, regime, fy) * (1 + r["cess"]))


def tax_on_salary(gross_salary, regime: str = "new", fy: str = "2025-26") -> np.ndarray:
    """Convenience: annual tax straight from gross salary."""
    return income_tax(taxable_income(gross_salary, regime, fy), regime, fy)
