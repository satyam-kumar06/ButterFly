"""Money building blocks, vectorised over futures (n paths x months).

Example:
    >>> round(emi(1_000_000, 0.09, 120), 2)
    12667.58
    >>> emi(120_000, 0.0, 12)
    10000.0
"""

from __future__ import annotations

import numpy as np


def emi(principal: float, annual_rate: float, months: int) -> float:
    """Equated monthly instalment. Correct at 0% interest too."""
    if months <= 0:
        raise ValueError("months must be positive")
    r = annual_rate / 12
    if r == 0:
        return principal / months
    f = (1 + r) ** months
    return principal * r * f / (f - 1)


def inflate(amount: float | np.ndarray, rate: float | np.ndarray, years: float) -> np.ndarray:
    """amount x (1 + rate) ** years."""
    return np.asarray(amount, float) * (1 + np.asarray(rate, float)) ** years


def salary_path(
    monthly_gross: float | np.ndarray,
    yearly_hike: float | np.ndarray,
    months: int,
    *,
    first_hike_month: int = 13,
) -> np.ndarray:
    """Monthly gross for each future, rising by that future's hike once a year.

    yearly_hike may be one value per path (shape (n,)) or per path per year
    (shape (n, years)). Month numbers are 1-based; the first hike lands in
    first_hike_month (month 13 = start of year 2).

    >>> salary_path(100.0, np.array([0.10]), 25)[0, [0, 12, 24]].round(2).tolist()
    [100.0, 110.0, 121.0]
    """
    hike = np.atleast_1d(np.asarray(yearly_hike, float))
    n = hike.shape[0]
    base = np.broadcast_to(np.asarray(monthly_gross, float), (n,)).astype(float)
    m = np.arange(1, months + 1)
    hikes_done = np.where(m >= first_hike_month, (m - first_hike_month) // 12 + 1, 0)
    if hike.ndim == 1:
        factor = (1 + hike[:, None]) ** hikes_done[None, :]
    else:
        cum = np.concatenate([np.ones((n, 1)), np.cumprod(1 + hike, axis=1)], axis=1)
        idx = np.minimum(hikes_done, cum.shape[1] - 1)
        factor = cum[:, idx]
    return base[:, None] * factor


def clawback_due(amount: float, clawback_months: float, exit_month: np.ndarray) -> np.ndarray:
    """Repayment owed when employment ends before the clawback period.

    exit_month is the last month worked (1-based). Leaving in month 11 of a
    12-month clawback repays in full; leaving at month 12 or later repays nothing.
    No clawback period (0) means nothing is ever repaid.
    """
    exit_month = np.asarray(exit_month, float)
    if clawback_months <= 0 or amount <= 0:
        return np.zeros_like(exit_month)
    return np.where(exit_month < clawback_months, float(amount), 0.0)


def cumulative_quarterly(monthly: np.ndarray) -> np.ndarray:
    """(n, months) monthly flows -> (n, quarters) running totals at quarter ends."""
    monthly = np.asarray(monthly, float)
    months = monthly.shape[1]
    if months % 3:
        raise ValueError("months must be a whole number of quarters")
    return np.cumsum(monthly, axis=1)[:, 2::3]


def fy_month(month_index: np.ndarray | int, start_month: int = 4) -> np.ndarray:
    """Calendar month (1-12) of simulation month 1..N when month 1 is `start_month`.
    Default start is April, the first month of the Indian financial year."""
    return (np.asarray(month_index) - 1 + start_month - 1) % 12 + 1
