"""Run 10,000 futures across sandbox forks (task B6).

    results = await run_simulation(mgr, checkpoint_id, spec, branch_id="br_01", emit=emit)

`checkpoint_id` is a tested model checkpoint (model.py inside /work). Each shard
is its own fork of that checkpoint: shard k of option A and shard k of option B
use the same seed, so futures line up across options (common random numbers).

`emit(event_name, data)` is the orchestrator's hook for the SSE stream; data
dicts match SandboxForkData / SimProgressData in apps/api/contracts.py.
"""

from __future__ import annotations

import asyncio
import base64
import inspect
import io
import json
from collections.abc import Callable
from typing import Any

import numpy as np

from apps.api.engine.aggregate import build_results
from apps.api.sandbox.manager import SandboxError, SandboxManager

Emit = Callable[[str, dict], Any] | None


async def _emit(emit: Emit, name: str, data: dict) -> None:
    if emit is None:
        return
    r = emit(name, data)
    if inspect.isawaitable(r):
        await r


def split(n: int, shards: int) -> list[int]:
    base, extra = divmod(n, shards)
    return [base + (1 if k < extra else 0) for k in range(shards)]


def _decode(text: str) -> dict[str, np.ndarray]:
    with np.load(io.BytesIO(base64.b64decode(text))) as z:
        return {k: z[k] for k in z.files}


async def run_shard(
    mgr: SandboxManager,
    checkpoint: str,
    spec: dict,
    option: str,
    shard: int,
    n: int,
    seed: int,
    *,
    emit: Emit = None,
    timeout_s: int = 120,
) -> dict[str, np.ndarray]:
    sb = await mgr.fork(checkpoint)
    await _emit(
        emit,
        "sandbox.fork",
        {"fork_id": sb.id, "parent": checkpoint, "purpose": "main", "option_id": option},
    )
    try:
        mgr.write(sb, "spec.json", json.dumps(spec))
        res = await mgr.run(
            sb,
            f"python run_shard.py paths --option {option} --shard {shard} "
            f"--paths {n} --seed {seed}",
            timeout_s=timeout_s,
        )
        if not res.ok:
            raise SandboxError(f"shard {option}{shard} failed: {res.stderr[-800:]}")
        out = _decode(await mgr.read(sb, f"out/shard_{option}_{shard}.npz.b64"))
        await _emit(emit, "sim.progress", {"fork_id": sb.id, "done": n, "total": n})
        return out
    finally:
        mgr.discard(sb)


def _merge(parts: list[dict[str, np.ndarray]]) -> dict[str, Any]:
    cum = np.concatenate([p["cumulative"] for p in parts])
    metrics = {
        k[7:]: np.concatenate([p[k] for p in parts]) for k in parts[0] if k.startswith("metric_")
    }
    story = {
        k[6:]: np.concatenate([p[k] for p in parts]) for k in parts[0] if k.startswith("story_")
    }
    return {"cumulative": cum, "metrics": metrics, "story": story}


async def simulate_paths(
    mgr: SandboxManager,
    checkpoint: str,
    spec: dict,
    *,
    n_paths: int = 10_000,
    shards_per_option: int = 4,
    seed: int = 20261025,
    emit: Emit = None,
) -> dict[str, dict]:
    """All shards in parallel (the manager's semaphore caps concurrency)."""
    sizes = split(n_paths, shards_per_option)
    jobs = {
        (opt, k): run_shard(mgr, checkpoint, spec, opt, k, sizes[k], seed, emit=emit)
        for opt in ("A", "B")
        for k in range(shards_per_option)
    }
    done = await asyncio.gather(*jobs.values())
    by = dict(zip(jobs.keys(), done, strict=True))
    return {opt: _merge([by[(opt, k)] for k in range(shards_per_option)]) for opt in ("A", "B")}


async def run_simulation(
    mgr: SandboxManager,
    checkpoint: str,
    spec: dict,
    *,
    branch_id: str,
    n_paths: int = 10_000,
    shards_per_option: int = 4,
    seed: int = 20261025,
    emit: Emit = None,
) -> dict:
    """Main run for one branch: Results JSON without flip points (see flips.py)."""
    data = await simulate_paths(
        mgr,
        checkpoint,
        spec,
        n_paths=n_paths,
        shards_per_option=shards_per_option,
        seed=seed,
        emit=emit,
    )
    return build_results(spec=spec, branch_id=branch_id, seed=seed, data=data)


TEMPLATE_MODEL = "from packs.{pack}.template_model import simulate  # noqa: F401\n"


async def template_checkpoint(mgr: SandboxManager, pack: str, label: str = "model-template") -> str:
    """Fallback: a checkpoint whose model.py is the pack's hand-written template."""
    sb = await mgr.fork(await mgr.base())
    mgr.write(sb, "model.py", TEMPLATE_MODEL.format(pack=pack))
    res = await mgr.run(sb, 'python -c "import model; print(model.simulate.__module__)"', 60)
    if not res.ok:
        raise SandboxError(f"template model for {pack} does not import: {res.stderr[-500:]}")
    return await mgr.checkpoint(sb, label)
