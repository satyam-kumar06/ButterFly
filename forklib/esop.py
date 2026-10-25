"""Stock options and RSUs: what has vested at exit, and what it is worth.

Vesting rule used by the demo offers: nothing before the cliff; at the cliff,
the cliff's share vests at once; after that, equal monthly instalments until
fully vested. 400 units, 12-month cliff, 48 months total -> 100 at month 12,
200 at month 24, 400 at month 48. RSUs are options with strike 0.

Example:
    >>> vested_units(400, 12, 48, np.array([11, 12, 30, 60])).tolist()
    [0.0, 100.0, 250.0, 400.0]
"""

from __future__ import annotations

import numpy as np


def vested_units(
    units: float, cliff_months: float, vesting_months: float, exit_month: np.ndarray
) -> np.ndarray:
    """Units vested by `exit_month` (months of service completed)."""
    exit_month = np.asarray(exit_month, float)
    if units <= 0 or vesting_months <= 0:
        return np.zeros_like(exit_month)
    months_vested = np.clip(np.floor(exit_month), 0, vesting_months)
    vested = units * months_vested / vesting_months
    return np.where(exit_month < cliff_months, 0.0, vested)


def esop_value(
    units: float,
    strike: float,
    cliff_months: float,
    vesting_months: float,
    exit_month: np.ndarray,
    price_at_exit: np.ndarray | float,
) -> np.ndarray:
    """Gross pre-tax value of vested units at exit: vested x max(price - strike, 0).
    A price of 0 (company worth nothing) gives 0. Perquisite tax is not modelled."""
    vested = vested_units(units, cliff_months, vesting_months, exit_month)
    gain = np.maximum(np.asarray(price_at_exit, float) - strike, 0.0)
    return vested * gain


def exit_price(
    reference_price: float,
    rng: np.random.Generator,
    n: int,
    *,
    p_zero: float = 0.3,
    sigma: float = 0.8,
) -> np.ndarray:
    """Share price at exit: zero with probability p_zero (illustrative default for
    private companies), otherwise lognormal around the reference price."""
    alive = rng.random(n) >= p_zero
    price = reference_price * rng.lognormal(0.0, sigma, n)
    return np.where(alive, price, 0.0)
