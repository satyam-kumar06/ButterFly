"""Gratuity on leaving (task B3).

Payment of Gratuity Act, carried into the Code on Social Security 2020 (in force
21 Nov 2025): permanent employees qualify after 5 years of continuous service;
fixed-term employees qualify pro rata after 1 year. Amount = 15/26 x last monthly
wages (basic + DA) x completed years, where a final part-year above 6 months
counts as a full year.

No payout cap is applied: the Rs 20 lakh figure often quoted is the income-tax
exemption limit for private-sector gratuity, not a cap on what is paid.
At Fork's horizons (1-20 years, salaried offers) this never binds for the demo.

Example:
    >>> round(float(gratuity(55_000, 60)))
    158654
    >>> float(gratuity(55_000, 48))
    0.0
"""

from __future__ import annotations

import numpy as np

RULE_SOURCE = {
    "rule": "Gratuity: 15/26 x last wages x years; 5 years for permanent staff, "
    "1 year for fixed-term employees under the Code on Social Security 2020",
    "sources": [
        "https://www.setindiabiz.com/blog/how-labour-codes-2025-affect-pf-gratuity-and-salary",
    ],
    "law": "Payment of Gratuity Act 1972, s.4; Code on Social Security 2020, s.53",
    "checked": "2026-10-25",
    "still_to_do": "Confirm the section numbers against the official gazette text.",
}


def service_years(months_of_service) -> np.ndarray:
    """Completed years, with a final part-year of more than 6 months rounded up."""
    m = np.asarray(months_of_service, float)
    years, rest = np.divmod(m, 12)
    return years + (rest > 6)


def gratuity(last_monthly_wages, months_of_service, *, fixed_term: bool = False) -> np.ndarray:
    m = np.asarray(months_of_service, float)
    qualifies = m >= (12 if fixed_term else 60)
    amount = 15 / 26 * np.asarray(last_monthly_wages, float) * service_years(m)
    return np.where(qualifies, amount, 0.0)
