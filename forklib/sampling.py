"""Draw values for spec variables, vectorised over simulated futures.

Distribution parameter names match apps/api/contracts.py exactly:

    normal      mean, std
    lognormal   mu, sigma          (of log X; median = exp(mu))
    uniform     low, high
    triangular  low, mode, high
    bernoulli   p                  (returns 0.0 / 1.0)
    discrete    values, probs

Example:
    >>> import numpy as np
    >>> rng = np.random.default_rng(0)
    >>> x = sample({"type": "triangular", "low": 0.4, "mode": 0.8, "high": 1.0}, rng, 5)
    >>> x.shape, bool((x >= 0.4).all() and (x <= 1.0).all())
    ((5,), True)
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

import numpy as np

Shape = int | tuple[int, ...]


def _as_dict(dist: Any) -> dict:
    if isinstance(dist, Mapping):
        return dict(dist)
    if hasattr(dist, "model_dump"):  # a pydantic contract model
        return dist.model_dump()
    raise TypeError(f"not a distribution: {dist!r}")


def sample(
    dist: Any,
    rng: np.random.Generator,
    size: Shape,
    *,
    clip_low: float | None = None,
    clip_high: float | None = None,
) -> np.ndarray:
    """Draw `size` samples. Optional clipping keeps values physically meaningful
    (for example a payout share between 0 and 1)."""
    d = _as_dict(dist)
    t = d["type"]
    if t == "normal":
        x = rng.normal(d["mean"], d["std"], size)
    elif t == "lognormal":
        x = rng.lognormal(d["mu"], d["sigma"], size)
    elif t == "uniform":
        x = rng.uniform(d["low"], d["high"], size)
    elif t == "triangular":
        lo, mo, hi = d["low"], d["mode"], d["high"]
        x = np.full(size, float(lo)) if lo == hi else rng.triangular(lo, mo, hi, size)
    elif t == "bernoulli":
        x = (rng.random(size) < d["p"]).astype(float)
    elif t == "discrete":
        x = rng.choice(np.asarray(d["values"], float), size=size, p=np.asarray(d["probs"], float))
    else:
        raise ValueError(f"unknown distribution type {t!r}")
    if clip_low is not None or clip_high is not None:
        x = np.clip(
            x,
            -np.inf if clip_low is None else clip_low,
            np.inf if clip_high is None else clip_high,
        )
    return np.asarray(x, dtype=float)


def sample_variable(variable: Any, rng: np.random.Generator, size: Shape) -> np.ndarray | Any:
    """A spec Variable as an array: fixed numbers are broadcast, distributions drawn.
    Non-numeric fixed values (a city, a tax regime) are returned unchanged."""
    v = _as_dict(variable)
    if v["kind"] == "fixed":
        value = v["value"]
        if isinstance(value, bool) or not isinstance(value, int | float):
            return value
        return np.full(size, float(value))
    return sample(v["dist"], rng, size)


def dist_quantiles(dist: Any, qs: list[float], *, n: int = 200_000, seed: int = 0) -> list[float]:
    """Quantiles of a distribution (used by the sweep to pick p10..p90 test points)."""
    x = sample(dist, np.random.default_rng(seed), n)
    return [float(v) for v in np.quantile(x, qs)]


def stream(seed: int, name: str) -> np.random.Generator:
    """A generator dedicated to one named source of uncertainty.

    Common random numbers: both options draw a shared variable (for example
    "layoff") from stream(seed, "layoff"), so they see the same layoffs and the
    difference between options comes from the options, not from luck.
    """
    key = np.frombuffer(hashlib.sha256(name.encode()).digest()[:16], dtype=np.uint32)
    return np.random.default_rng([seed, *key.tolist()])
