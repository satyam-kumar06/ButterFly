"""Turn raw simulated futures into the Results contract (task B6).

Pure functions over NumPy arrays, so they are tested without any sandbox.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np

PCTS = (5, 10, 25, 50, 75, 90, 95)
DISPLAY_PATHS = 1000
UNITS = {
    "cumulative_in_hand": "INR",
    "savings_after_rent": "INR",
    "worst_month": "INR",
    "clawback_paid": "INR",
    "equity_value": "INR",
    "tax_paid": "INR",
    "out_of_pocket": "INR",
    "total_cost": "INR",
    "premiums_paid": "INR",
    "worst_year_cost": "INR",
    "any_year_over_1_lakh": "share",
}


def x_points(horizon_years: int) -> list[str]:
    return [f"Q{q}-Y{y}" for y in range(1, horizon_years + 1) for q in range(1, 5)]


def p_win(a: np.ndarray, b: np.ndarray, objective: str) -> dict[str, float]:
    """P(A wins), P(B wins), P(tie) on matched futures. Ties within half a rupee."""
    tie = np.isclose(a, b, rtol=0, atol=0.5)
    a_better = (a > b) if objective == "maximize" else (a < b)
    pa = float((a_better & ~tie).mean())
    pt = float(tie.mean())
    return {"A": pa, "B": max(0.0, 1.0 - pa - pt), "tie": pt}


def histogram(x: np.ndarray, bins: int = 30) -> dict[str, list]:
    x = np.asarray(x, float)
    lo, hi = float(x.min()), float(x.max())
    if hi - lo < 1e-9:  # every future identical: one bin around the value
        return {"edges": [lo - 0.5, lo + 0.5], "counts": [int(x.size)]}
    counts, edges = np.histogram(x, bins=bins, range=(lo, hi))
    return {"edges": [float(e) for e in edges], "counts": [int(c) for c in counts]}


def percentiles(cum: np.ndarray) -> dict[str, list[float]]:
    q = np.percentile(cum, PCTS, axis=0)
    q = np.maximum.accumulate(q, axis=0)  # guard against float noise breaking the order
    return {f"p{p}": [float(v) for v in row] for p, row in zip(PCTS, q, strict=True)}


def display_ids(rank_by: np.ndarray, k: int = DISPLAY_PATHS) -> np.ndarray:
    """Pick k futures spread evenly over the whole range of `rank_by`, so extremes
    still appear in the 3D view; returned in increasing id order (same for A and B)."""
    n = rank_by.size
    if n <= k:
        return np.arange(n)
    order = np.argsort(rank_by, kind="stable")
    picks = order[np.linspace(0, n - 1, k).round().astype(int)]
    return np.unique(picks)


def stories(
    pack: str,
    story: dict[str, np.ndarray],
    ids: np.ndarray,
    label: str,
    cumulative_final: np.ndarray,
) -> list[dict]:
    """Event logs for hover cards: the pack's own story_lines (trusted code), or a
    plain fallback if an agent-written model returned different story fields."""
    fn = None
    try:
        fn = importlib.import_module(f"packs.{pack}.template_model").story_lines
    except (ImportError, AttributeError):
        pass
    out = []
    for i in ids:
        lines = None
        if fn is not None:
            try:
                lines = fn(story, int(i), label)
            except (KeyError, IndexError, TypeError, ValueError):
                lines = None
        if not lines:
            lines = [f"ends at Rs {cumulative_final[i] / 1e5:.1f}L"]
        out.append({"id": int(i), "events": [str(x) for x in lines]})
    return out


def build_results(
    *,
    spec: dict,
    branch_id: str,
    seed: int,
    data: dict[str, dict[str, Any]],
    data_kind: str = "simulation",
) -> dict:
    """data[opt] = {"cumulative": (n,Q), "metrics": {name: (n,)}, "story": {name: (n,)}}."""
    primary = spec["metrics"]["primary"]
    objective = spec["metrics"]["direction"]
    n = data["A"]["cumulative"].shape[0]
    if data["B"]["cumulative"].shape[0] != n:
        raise ValueError("options must be simulated on the same number of futures")
    xs = x_points(spec["horizon_years"])
    gap = data["A"]["metrics"][primary] - data["B"]["metrics"][primary]
    ids = display_ids(gap)
    labels = {o["id"]: o["label"] for o in spec["options"]}
    options = {}
    for opt in ("A", "B"):
        d = data[opt]
        cum = np.asarray(d["cumulative"], float)
        if cum.shape[1] != len(xs):
            raise ValueError(f"{opt}: model returned {cum.shape[1]} quarters, expected {len(xs)}")
        metrics = {
            name: {
                "median": float(np.median(v)),
                "unit": UNITS.get(name, "INR"),
                "hist": histogram(v),
            }
            for name, v in d["metrics"].items()
        }
        options[opt] = {
            "label": labels[opt],
            "percentiles": percentiles(cum),
            "sampled_paths": [[float(x) for x in cum[i]] for i in ids],
            "path_stories": stories(spec["pack"], d.get("story", {}), ids, labels[opt], cum[:, -1]),
            "metrics": metrics,
        }
    return {
        "branch_id": branch_id,
        "pack": spec["pack"],
        "data_kind": data_kind,
        "horizon_years": spec["horizon_years"],
        "currency": "INR",
        "path_count": int(n),
        "seed": int(seed),
        "x_points": xs,
        "primary_metric": primary,
        "objective": objective,
        "options": options,
        "p_win": p_win(data["A"]["metrics"][primary], data["B"]["metrics"][primary], objective),
        "sensitivities": [],
        "flip_points": [],
        "frontier": None,
        "story": "",
        "assumptions": spec["variables"],
    }
