"""State professional tax on salaries (task B3).

Only the demo states are stored. Month numbers are calendar months (2 = February).

Karnataka (from 1 Apr 2025): nil below Rs 25,000 gross a month; Rs 200 a month,
Rs 300 in February (Rs 2,500 a year).
Maharashtra: men - nil up to Rs 7,500, Rs 175 for Rs 7,501-10,000, Rs 200 above
(Rs 300 in February); women - nil up to Rs 25,000, then Rs 200 (Rs 300 in February).

Example:
    >>> float(professional_tax("karnataka", 110_000, 2))
    300.0
    >>> float(professional_tax("karnataka", 110_000, 4))
    200.0
"""

from __future__ import annotations

import numpy as np

RULE_SOURCE = {
    "karnataka": {
        "rule": "Karnataka Tax on Professions (Amendment) Act 2025, effective 2025-04-01",
        "sources": [
            "https://ptax.karnataka.gov.in/ptemployer/FAQ",
            "https://ksandk.com/newsletter/karnataka-professional-tax-higher-income/",
        ],
    },
    "maharashtra": {
        "rule": "Maharashtra State Tax on Professions schedule, entry 1",
        "sources": [
            "https://www.mahagst.gov.in/public/uploads/menufiles/PT%20Rate%20Schedule%20updated%20upto%2031.03.2025%20%281%29%20%281%29.pdf",
        ],
        "still_to_do": "Reopen the official PDF (timed out in Phase 0) and confirm.",
    },
    "checked": "2026-10-25",
}

_ALIASES = {"ka": "karnataka", "bengaluru": "karnataka", "mh": "maharashtra", "pune": "maharashtra"}


def _state(state: str) -> str:
    s = state.strip().lower()
    for part in [s, *[p.strip() for p in s.split(",")]]:
        if part in ("karnataka", "maharashtra"):
            return part
        if part in _ALIASES:
            return _ALIASES[part]
    raise ValueError(f"professional tax for {state!r} is not stored yet")


def professional_tax(state: str, gross_monthly, calendar_month, *, female: bool = False):
    """Professional tax deducted in one month."""
    s = _state(state)
    g = np.asarray(gross_monthly, float)
    feb = np.asarray(calendar_month) == 2
    top = np.where(feb, 300.0, 200.0)
    if s == "karnataka":
        return np.where(g >= 25_000, top, 0.0)
    if female:
        return np.where(g > 25_000, top, 0.0)
    return np.where(g > 10_000, top, np.where(g > 7_500, 175.0, 0.0))


def annual_professional_tax(state: str, gross_monthly, *, female: bool = False) -> np.ndarray:
    months = np.arange(1, 13)
    g = np.asarray(gross_monthly, float)
    return sum(professional_tax(state, g, m, female=female) for m in months)
