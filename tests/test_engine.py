"""Simulation runner, aggregation and flip search (tasks B6, B7), run end to end
through LocalManager with trusted models only."""

from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path

import numpy as np
import pytest

from apps.api.contracts import Results, SandboxForkData, SimProgressData
from apps.api.engine.aggregate import display_ids, histogram, p_win, percentiles
from apps.api.engine.flips import cache_key, candidates, run_flip_search, sweep_values
from apps.api.engine.simulation import run_simulation, split, template_checkpoint
from apps.api.sandbox import LocalManager

ROOT = Path(__file__).resolve().parents[1]


def spec_of(pack: str) -> dict:
    return json.loads((ROOT / "mocks" / f"spec_{pack}.json").read_text())


@pytest.fixture()
def mgr(tmp_path):
    return LocalManager(tmp_path / "sbx", max_parallel=8)


# A toy, trusted model with a known flip: A's primary metric is 1000 x (x - 20),
# B's is 0, so A wins exactly when x > 20.
TOY_MODEL = """
import numpy as np
from packs.common import SpecView

def simulate(option_id, spec, rng, n):
    s = SpecView(spec, None, rng, n)
    x = s.draw("x")
    noise = s.draw("noise")
    q = spec["horizon_years"] * 4
    value = 1000.0 * (x - 20) + noise if option_id == "A" else np.zeros(n)
    return {"cumulative": np.tile(value[:, None], (1, q)),
            "metrics": {"gain": value}, "story": {}}
"""


def toy_spec() -> dict:
    var = dict(source="user", source_ref="test", confirmed=True, editable=True, sweep_range=None)
    return {
        "schema_version": "1.0.0",
        "decision_id": "toy",
        "title": "toy",
        "pack": "open",
        "horizon_years": 1,
        "step": "month",
        "currency": "INR",
        "options": [{"id": "A", "label": "A"}, {"id": "B", "label": "B"}],
        "variables": [
            dict(
                var,
                name="x",
                unit="u",
                kind="distribution",
                dist={"type": "uniform", "low": 10, "high": 34},
            ),
            dict(
                var,
                name="noise",
                unit="INR",
                kind="distribution",
                dist={"type": "normal", "mean": 0, "std": 1},
            ),
        ],
        "events": [],
        "metrics": {"primary": "gain", "direction": "maximize", "others": []},
    }


async def toy_checkpoint(mgr):
    sb = await mgr.fork(await mgr.base())
    mgr.write(sb, "model.py", TOY_MODEL)
    return await mgr.checkpoint(sb, "toy")


# --- pure aggregation -----------------------------------------------------------------


def test_p_win_with_ties_and_direction():
    a, b = np.array([1.0, 2.0, 3.0, 3.0]), np.array([2.0, 1.0, 3.0, 0.0])
    assert p_win(a, b, "maximize") == {"A": 0.5, "B": 0.25, "tie": 0.25}
    assert p_win(a, b, "minimize") == {"A": 0.25, "B": 0.5, "tie": 0.25}


def test_histogram_counts_every_path_even_if_identical():
    h = histogram(np.zeros(500))
    assert sum(h["counts"]) == 500 and h["edges"][0] < h["edges"][1]
    h = histogram(np.arange(1000.0))
    assert sum(h["counts"]) == 1000


def test_percentiles_ordered_and_display_ids_spread():
    cum = np.random.default_rng(0).normal(size=(5000, 8)).cumsum(axis=1)
    p = percentiles(cum)
    for col in zip(*p.values(), strict=True):
        assert list(col) == sorted(col)
    gap = np.arange(5000.0)
    ids = display_ids(gap, 1000)
    assert len(ids) == 1000 and ids[0] == 0 and ids[-1] == 4999
    assert split(10_000, 4) == [2500] * 4 and sum(split(10, 3)) == 10


# --- runner end to end ------------------------------------------------------------------


@pytest.mark.parametrize("pack", ["offer_xray", "fine_print"])
def test_run_simulation_produces_valid_results(mgr, pack):
    events = []

    async def go():
        ck = await template_checkpoint(mgr, pack)
        return await run_simulation(
            mgr,
            ck,
            spec_of(pack),
            branch_id="br_t",
            n_paths=4000,
            shards_per_option=4,
            emit=lambda n, d: events.append((n, d)),
        )

    r = asyncio.run(go())
    model = Results.model_validate(r)
    assert model.path_count == 4000 and model.data_kind == "simulation"
    forks = [d for n, d in events if n == "sandbox.fork"]
    assert len(forks) == 8
    for n, d in events:
        (SandboxForkData if n == "sandbox.fork" else SimProgressData).model_validate(d)


def test_shards_line_up_across_options(mgr):
    """Same seed + shard => identical futures for both options (CRN through the runner)."""
    spec = spec_of("fine_print")

    async def go():
        ck = await template_checkpoint(mgr, "fine_print")
        from apps.api.engine.simulation import simulate_paths

        return await simulate_paths(mgr, ck, spec, n_paths=2000, shards_per_option=2)

    d = asyncio.run(go())
    assert np.array_equal(d["A"]["story"]["stays"], d["B"]["story"]["stays"])


def test_runner_is_reproducible(mgr):
    async def go():
        ck = await template_checkpoint(mgr, "offer_xray")
        r1 = await run_simulation(mgr, ck, spec_of("offer_xray"), branch_id="a", n_paths=1000)
        r2 = await run_simulation(mgr, ck, spec_of("offer_xray"), branch_id="a", n_paths=1000)
        return r1, r2

    r1, r2 = asyncio.run(go())
    assert r1["options"]["A"]["percentiles"] == r2["options"]["A"]["percentiles"]


# --- flip search ---------------------------------------------------------------------------


def test_candidates_and_sweep_values():
    spec = toy_spec()
    names = [v["name"] for v in candidates(spec)]
    assert names == ["x", "noise"]
    vals = sweep_values(spec["variables"][0])
    assert len(vals) == 5 and vals == sorted(vals)
    assert sweep_values({"kind": "fixed", "value": 0.0}) == []
    assert len(sweep_values({"kind": "fixed", "value": 100.0})) == 5


def test_flip_search_finds_the_known_threshold(mgr):
    spec = toy_spec()

    async def go():
        ck = await toy_checkpoint(mgr)
        base = await run_simulation(
            mgr, ck, spec, branch_id="toy", n_paths=2000, shards_per_option=2
        )
        flips = await run_flip_search(
            mgr, ck, spec, baseline_p_win=base["p_win"], n_paths=400, frontier_size=4
        )
        return base, flips

    base, flips = asyncio.run(go())
    assert flips["sensitivities"][0]["variable"] == "x"
    fp = flips["flip_points"][0]
    assert fp["variable"] == "x"
    assert abs(fp["threshold"] - 20) < 0.5
    # baseline: x ~ U(10, 34) so A usually wins; the flip is "below 20, B wins"
    assert base["p_win"]["A"] > 0.5
    assert fp["direction"] == "below" and fp["winner_after"] == "B"
    # merged results still satisfy the contract
    merged = dict(base, **flips)
    Results.model_validate(merged)
    assert flips["frontier"]["x_var"] == "x"


def test_cache_key_changes_with_spec_and_model():
    spec = toy_spec()
    k1 = cache_key(spec, "ck1")
    other = copy.deepcopy(spec)
    other["variables"][0]["dist"]["high"] = 40
    assert k1 == cache_key(copy.deepcopy(spec), "ck1")
    assert k1 != cache_key(other, "ck1") and k1 != cache_key(spec, "ck2")
