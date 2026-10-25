"""Fixed shard runner, owned by the team, never by the agent (task B6).

Runs inside a sandbox fork whose /work holds:
    spec.json        the Decision Spec (a branch's spec; may differ per what-if)
    model.py         Ultra's model, or `from packs.<pack>.template_model import simulate`
    forklib/, packs/ trusted code from the base checkpoint

Two modes:

  paths   simulate a block of futures for one option and save every array
          python run_shard.py paths --option A --shard 2 --paths 2500 --seed 7
          -> out/shard_A_2.npz.b64   (base64 .npz: cumulative, metric_*, story_*)

  points  for a list of spec overrides, run both options on the same futures and
          report P(A wins) for each (used by the tornado sweep, threshold search
          and frontier). Overrides come from points.json: [{"var": value, ...}, ...]
          python run_shard.py points --paths 2000 --seed 7 --tag sweep_03
          -> out/points_sweep_03.json

Common random numbers: the generator for shard k is default_rng([seed, k]) for
BOTH options, so future #i means the same layoffs, tenure, illnesses for A and B.
"""

from __future__ import annotations

import argparse
import base64
import copy
import io
import json
import sys
import time
from pathlib import Path

import numpy as np

WORK = Path(__file__).resolve().parent


def load_spec(overrides: dict | None = None) -> dict:
    spec = json.loads((WORK / "spec.json").read_text(encoding="utf-8"))
    for name, value in (overrides or {}).items():
        for v in spec["variables"]:
            if v["name"] == name:
                v["kind"] = "fixed"
                v["value"] = value
                v.pop("dist", None)
                break
        else:
            raise KeyError(f"override for unknown variable {name!r}")
    return spec


def simulate_fn():
    sys.path.insert(0, str(WORK))
    from model import simulate  # noqa: PLC0415 - the model under test

    return simulate


def rng_for(seed: int, shard: int) -> np.random.Generator:
    return np.random.default_rng([seed, shard])


def p_win_a(a: np.ndarray, b: np.ndarray, objective: str) -> tuple[float, float]:
    better = a > b if objective == "maximize" else a < b
    tie = np.isclose(a, b, rtol=0, atol=0.5)
    return float((better & ~tie).mean()), float(tie.mean())


def run_paths(option: str, shard: int, n: int, seed: int) -> Path:
    spec = load_spec()
    t = time.perf_counter()
    out = simulate_fn()(option, spec, rng_for(seed, shard), n)
    arrays = {"cumulative": np.asarray(out["cumulative"], float)}
    for k, v in out.get("metrics", {}).items():
        arrays[f"metric_{k}"] = np.asarray(v, float)
    for k, v in out.get("story", {}).items():
        arrays[f"story_{k}"] = np.asarray(v, float)
    arrays["seconds"] = np.array([time.perf_counter() - t])
    buf = io.BytesIO()
    np.savez_compressed(buf, **arrays)
    dest = WORK / "out" / f"shard_{option}_{shard}.npz.b64"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(base64.b64encode(buf.getvalue()).decode())
    return dest


def run_points(n: int, seed: int, tag: str, shard: int = 0) -> Path:
    points = json.loads((WORK / "points.json").read_text(encoding="utf-8"))
    simulate = simulate_fn()
    results = []
    for overrides in points:
        spec = load_spec(overrides)
        primary = spec["metrics"]["primary"]
        objective = spec["metrics"]["direction"]
        a = simulate("A", copy.deepcopy(spec), rng_for(seed, shard), n)["metrics"][primary]
        b = simulate("B", copy.deepcopy(spec), rng_for(seed, shard), n)["metrics"][primary]
        pa, tie = p_win_a(np.asarray(a, float), np.asarray(b, float), objective)
        results.append({"overrides": overrides, "p_win_A": pa, "tie": tie})
    dest = WORK / "out" / f"points_{tag}.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(results))
    return dest


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["paths", "points"])
    ap.add_argument("--option", choices=["A", "B"])
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--paths", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--tag", default="points")
    a = ap.parse_args(argv)
    if a.mode == "paths":
        if not a.option:
            ap.error("--option is required in paths mode")
        print(run_paths(a.option, a.shard, a.paths, a.seed))
    else:
        print(run_points(a.paths, a.seed, a.tag, a.shard))


if __name__ == "__main__":
    main()
