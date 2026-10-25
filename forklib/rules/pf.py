"""Provident Fund contributions (task B3).

Employee and employer each contribute 12% of PF wages. Many employers cap PF
wages at the statutory wage ceiling of Rs 15,000 a month, giving Rs 1,800; others
contribute on full basic. Which one applies is a term of the offer, so callers
pass the ceiling (or None) from the offer letter rather than forklib guessing.

Labour codes (in force 21 Nov 2025): "wages" must be at least 50% of total
remuneration; if allowances push basic below that, the excess counts as wages.
`wages_under_codes` computes that base for callers who need it.

Example:
    >>> float(pf_contribution(60_000, ceiling=15_000))
    1800.0
    >>> float(pf_contribution(60_000))
    7200.0
"""

from __future__ import annotations

import numpy as np

RATE = 0.12
WAGE_CEILING = 15_000

RULE_SOURCE = {
    "rule": "EPF contribution 12% of PF wages; statutory wage ceiling Rs 15,000/month",
    "sources": [
        "https://www.india-briefing.com/news/salary-structure-india-labor-code-compliance-guide-44332.html",
    ],
    "law": "Employees' Provident Funds Scheme 1952 (rate and wage ceiling)",
    "checked": "2026-10-25",
    "notes": "Demo offers state Rs 1,800/month explicitly (12% of the Rs 15,000 ceiling).",
}


def pf_contribution(basic_monthly, *, rate: float = RATE, ceiling: float | None = None):
    """Monthly employee (or employer) PF on basic salary, optionally capped."""
    wages = np.asarray(basic_monthly, float)
    if ceiling is not None:
        wages = np.minimum(wages, ceiling)
    return wages * rate


def wages_under_codes(basic_plus_da, total_remuneration, excluded_allowances):
    """PF/gratuity wage base under the labour codes' 50% rule.

    If excluded allowances (HRA, conveyance, bonus, etc.) exceed half of total
    remuneration, the excess is added back to wages.
    """
    basic = np.asarray(basic_plus_da, float)
    excess = np.maximum(
        np.asarray(excluded_allowances, float) - 0.5 * np.asarray(total_remuneration, float), 0
    )
    return basic + excess
