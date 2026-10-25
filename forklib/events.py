"""Random events (layoffs, hospital stays) as monthly on/off masks.

Example:
    >>> import numpy as np
    >>> from forklib.sampling import stream
    >>> mask, starts = event_mask(0.06, stream(1, "layoff"), 1000, 48, duration=(2, 5))
    >>> mask.shape, mask.dtype.name
    ((1000, 48), 'bool')
"""

from __future__ import annotations

import numpy as np

from forklib.sampling import sample


def monthly_probability(prob_per_year: float) -> float:
    """Convert a yearly chance into the monthly chance with the same yearly total:
    1 - (1 - p_year) ** (1/12)."""
    if not 0 <= prob_per_year <= 1:
        raise ValueError("probability must be between 0 and 1")
    return 1 - (1 - prob_per_year) ** (1 / 12)


def event_mask(
    prob_per_year: float,
    rng: np.random.Generator,
    n: int,
    months: int,
    *,
    duration: tuple[int, int] | dict = (1, 1),
    max_events: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (mask, first_start).

    mask[i, m] is True while path i is inside an event in month m+1.
    first_start[i] is the 1-based month the first event began, or 0 if none.
    duration is an inclusive (low, high) range of whole months or a distribution
    dict. A new event can only start once the previous one has ended.
    """
    p = monthly_probability(prob_per_year)
    starts = rng.random((n, months)) < p
    if isinstance(duration, dict):
        lengths = np.maximum(1, np.round(sample(duration, rng, (n, months)))).astype(int)
    else:
        lo, hi = duration
        lengths = rng.integers(lo, hi + 1, (n, months))
    mask = np.zeros((n, months), bool)
    remaining = np.zeros(n, int)
    count = np.zeros(n, int)
    first = np.zeros(n, int)
    for m in range(months):  # loop over months, never over paths
        can_start = remaining == 0
        if max_events is not None:
            can_start &= count < max_events
        new = can_start & starts[:, m]
        remaining = np.where(new, lengths[:, m], remaining)
        first = np.where(new & (first == 0), m + 1, first)
        count += new
        mask[:, m] = remaining > 0
        remaining = np.maximum(remaining - 1, 0)
    return mask, first


def poisson_counts(rate_per_year: np.ndarray | float, rng: np.random.Generator, size) -> np.ndarray:
    """Number of events in a year, e.g. hospital admissions for each member."""
    return rng.poisson(np.broadcast_to(np.asarray(rate_per_year, float), size))
