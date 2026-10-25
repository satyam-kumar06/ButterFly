"""Flip-point search (task B7): which assumptions change the winner, and where.

1. Tornado sweep: each candidate variable is fixed at 5 values across its range
   (p10..p90 for distributions, its sweep_range, or +-20% for a fixed number), with
   2,000 futures per point. Variables are ranked by how far P(A wins) swings.
2. Threshold: for the top 3, bisection (6 steps) inside the sweep interval where
   the lead changes hands, giving "Offer A wins unless tenure is below 17 months".
3. Frontier: a 12 x 12 grid of P(A wins) over the top 2 variables, one fork per row.

Every point runs BOTH options on the same futures inside one fork (run_shard.py
"points" mode), so the comparison uses common random numbers.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any

import numpy as np

from apps.api.engine.simulation import Emit, _emit
from apps.api.sandbox.manager import SandboxError, SandboxManager
from forklib.sampling import dist_quantiles

MAX_VARIABLES = 8
SWEEP_QUANTILES = [0.1, 0.3, 0.5, 0.7, 0.9]


def cache_key(spec: dict, checkpoint: str) -> str:
    """Results depend only on the spec and the model checkpoint (for the demo cache)."""
    blob = json.dumps(spec, sort_keys=True) + "|" + checkpoint
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _numeric(v: dict) -> bool:
    val = v.get("value")
    return v["kind"] == "distribution" or (
        isinstance(val, int | float) and not isinstance(val, bool)
    )


def sweep_values(v: dict) -> list[float]:
    """Five test values for one variable, strictly increasing (duplicates dropped)."""
    if v.get("sweep_range"):
        vals = np.linspace(v["sweep_range"]["low"], v["sweep_range"]["high"], 5)
    elif v["kind"] == "distribution":
        vals = np.array(dist_quantiles(v["dist"], SWEEP_QUANTILES))
    else:
        x = float(v["value"])
        if x == 0:
            return []
        vals = np.linspace(0.8 * x, 1.2 * x, 5)
        if x < 0:
            vals = vals[::-1]
    vals = np.unique(np.round(vals, 6))
    return [float(x) for x in vals]


def candidates(spec: dict) -> list[dict]:
    """Up to 8 editable numeric variables, most decision-relevant first:
    explicit sweep ranges, then uncertain (distribution) inputs, then numbers the
    user gave us. Document terms are only swept when given a sweep_range."""
    ranked = []
    for v in spec["variables"]:
        if not v.get("editable", True) or not _numeric(v):
            continue
        if v.get("sweep_range"):
            pri = 0
        elif v["kind"] == "distribution":
            pri = 1
        elif v.get("source") == "user":
            pri = 2
        else:
            continue
        if len(sweep_values(v)) >= 2:
            ranked.append((pri, v))
    ranked.sort(key=lambda t: t[0])
    return [v for _, v in ranked[:MAX_VARIABLES]]


async def run_points(
    mgr: SandboxManager,
    checkpoint: str,
    spec: dict,
    points: list[dict],
    *,
    n: int,
    seed: int,
    purpose: str,
    emit: Emit = None,
    tag: str = "p",
) -> list[dict]:
    """One fork evaluates a list of override sets; returns [{p_win_A, tie, overrides}]."""
    sb = await mgr.fork(checkpoint)
    await _emit(emit, "sandbox.fork", {"fork_id": sb.id, "parent": checkpoint, "purpose": purpose})
    try:
        mgr.write(sb, "spec.json", json.dumps(spec))
        mgr.write(sb, "points.json", json.dumps(points))
        res = await mgr.run(
            sb, f"python run_shard.py points --paths {n} --seed {seed} --tag {tag}", timeout_s=180
        )
        if not res.ok:
            raise SandboxError(f"{purpose} fork failed: {res.stderr[-800:]}")
        out = json.loads(await mgr.read(sb, f"out/points_{tag}.json"))
        await _emit(
            emit, "sim.progress", {"fork_id": sb.id, "done": len(points), "total": len(points)}
        )
        return out
    finally:
        mgr.discard(sb)


def _lead(point: dict) -> float:
    """P(A wins) - P(B wins); positive means A is ahead."""
    pa, tie = point["p_win_A"], point.get("tie", 0.0)
    return pa - (1 - pa - tie)


async def run_flip_search(
    mgr: SandboxManager,
    checkpoint: str,
    spec: dict,
    *,
    baseline_p_win: dict | None = None,
    n_paths: int = 2000,
    seed: int = 20261025,
    emit: Emit = None,
    frontier_size: int = 12,
    bisection_steps: int = 6,
) -> dict[str, Any]:
    """Returns {"sensitivities": [...], "flip_points": [...], "frontier": {...} | None}."""
    cands = candidates(spec)
    if not cands:
        return {"sensitivities": [], "flip_points": [], "frontier": None}

    # 1. tornado: one fork per (variable, value)
    jobs, keys = [], []
    for v in cands:
        for x in sweep_values(v):
            keys.append((v["name"], x))
            jobs.append(
                run_points(
                    mgr,
                    checkpoint,
                    spec,
                    [{v["name"]: x}],
                    n=n_paths,
                    seed=seed,
                    purpose="sweep",
                    emit=emit,
                    tag=f"s{len(jobs)}",
                )
            )
    outs = await asyncio.gather(*jobs)
    sweep: dict[str, list[tuple[float, dict]]] = {}
    for (name, x), out in zip(keys, outs, strict=True):
        sweep.setdefault(name, []).append((x, out[0]))
    units = {v["name"]: v["unit"] for v in spec["variables"]}
    sens = []
    for name, pts in sweep.items():
        pws = [p["p_win_A"] for _, p in pts]
        sens.append(
            {
                "variable": name,
                "unit": units[name],
                "swing": float(max(pws) - min(pws)),
                "points": [{"value": x, "p_win_A": p["p_win_A"]} for x, p in pts],
            }
        )
    sens.sort(key=lambda s: -s["swing"])

    # 2. thresholds for the top 3 variables whose lead changes sign
    base_lead = None
    if baseline_p_win:
        base_lead = baseline_p_win["A"] - baseline_p_win["B"]

    async def threshold(name: str) -> dict | None:
        pts = sweep[name]
        leads = [_lead(p) for _, p in pts]
        crossing = next(
            (i for i in range(len(pts) - 1) if leads[i] == 0 or leads[i] * leads[i + 1] < 0),
            None,
        )
        if crossing is None:
            return None
        x0, x1, l0 = pts[crossing][0], pts[crossing + 1][0], leads[crossing]
        lo, hi, l_lo = x0, x1, l0
        for step in range(bisection_steps):
            mid = (lo + hi) / 2
            out = await run_points(
                mgr,
                checkpoint,
                spec,
                [{name: mid}],
                n=n_paths,
                seed=seed,
                purpose="threshold",
                emit=emit,
                tag=f"t{step}",
            )
            l_mid = _lead(out[0])
            if l_lo * l_mid <= 0:
                hi = mid
            else:
                lo, l_lo = mid, l_mid
        thr = (lo + hi) / 2
        below_winner = "A" if _lead(pts[0][1]) > 0 else "B"
        above_winner = "B" if below_winner == "A" else "A"
        overall = None if base_lead is None else ("A" if base_lead >= 0 else "B")
        if overall == below_winner:
            direction, winner = "above", above_winner
        else:
            direction, winner = "below", below_winner
        swing = next(s["swing"] for s in sens if s["variable"] == name)
        return {
            "variable": name,
            "threshold": float(thr),
            "unit": units[name],
            "direction": direction,
            "winner_after": winner,
            "swing": swing,
            "bracket": {"low": float(x0), "high": float(x1)},
        }

    flips = [f for f in await asyncio.gather(*[threshold(s["variable"]) for s in sens[:3]]) if f]

    # 3. frontier over the top two variables
    frontier = None
    if len(sens) >= 2 and sens[0]["swing"] > 0:
        xv, yv = sens[0], sens[1]
        xs = np.linspace(xv["points"][0]["value"], xv["points"][-1]["value"], frontier_size)
        ys = np.linspace(yv["points"][0]["value"], yv["points"][-1]["value"], frontier_size)
        rows = await asyncio.gather(
            *[
                run_points(
                    mgr,
                    checkpoint,
                    spec,
                    [{xv["variable"]: float(x), yv["variable"]: float(y)} for x in xs],
                    n=max(200, n_paths // 2),
                    seed=seed,
                    purpose="frontier",
                    emit=emit,
                    tag=f"f{i}",
                )
                for i, y in enumerate(ys)
            ]
        )
        frontier = {
            "x_var": xv["variable"],
            "y_var": yv["variable"],
            "x_values": [float(x) for x in xs],
            "y_values": [float(y) for y in ys],
            "grid": [[float(p["p_win_A"]) for p in row] for row in rows],
        }
    return {"sensitivities": sens, "flip_points": flips, "frontier": frontier}
