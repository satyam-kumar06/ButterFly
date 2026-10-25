"""Helpers shared by pack template models: read a Decision Spec as arrays.

Common random numbers: every uncertain input is drawn from forklib.stream(seed,
<variable name>). The runner hands options A and B generators with the same seed,
so a shared variable (no "A."/"B." prefix, e.g. tenure_months) takes the same
value in future #i for both options.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from forklib.sampling import sample, sample_variable, stream


class SpecView:
    """Read-only view of a Decision Spec dict with pack defaults as fallback."""

    def __init__(self, spec: dict, defaults: dict | None, rng: np.random.Generator, n: int):
        self.spec = spec
        self.vars = {v["name"]: v for v in spec["variables"]}
        self.events = {e["name"]: e for e in spec.get("events", [])}
        self.defaults = defaults or {}
        self.n = n
        # one seed per call; identical for A and B when the runner seeds them alike
        self.seed = int(rng.integers(0, 2**31 - 1))

    @property
    def months(self) -> int:
        return int(self.spec["horizon_years"]) * 12

    @property
    def years(self) -> int:
        return int(self.spec["horizon_years"])

    def rng(self, name: str) -> np.random.Generator:
        return stream(self.seed, name)

    def has(self, name: str) -> bool:
        return name in self.vars or name in self.defaults.get("variables", {})

    def scalar(self, name: str, default: Any = None) -> Any:
        """A fixed value (number, text or flag). Distributions are not allowed here."""
        v = self.vars.get(name)
        if v is None:
            d = self.defaults.get("variables", {}).get(name)
            if d is None:
                if default is None:
                    raise KeyError(f"spec has no variable {name!r}")
                return default
            v = d
        if v["kind"] != "fixed":
            raise ValueError(f"{name} must be a fixed value")
        return v["value"]

    def draw(self, name: str, size=None, *, clip: tuple[float, float] | None = None) -> np.ndarray:
        """Spec value (fixed or distribution), else the pack default, as an array."""
        size = self.n if size is None else size
        v = self.vars.get(name) or self.defaults.get("variables", {}).get(name)
        if v is None:
            raise KeyError(f"spec and defaults have no variable {name!r}")
        if v["kind"] == "fixed":
            x = np.full(size, float(v["value"]))
        else:
            x = sample(v["dist"], self.rng(name), size)
        if clip is not None:
            x = np.clip(x, *clip)
        return x

    def event(self, name: str) -> dict | None:
        if name in self.events:
            return self.events[name]
        return self.defaults.get("events", {}).get(name)


def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


__all__ = ["SpecView", "load_json", "sample_variable"]
