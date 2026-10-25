"""Readiness and opt-in live probes. Never logs keys or runs model-generated code."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from datetime import datetime, timedelta, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOKEN_URL = "https://api.tokenfactory.nebius.com/v1/"
DEFAULT_SANDBOX_URL = "https://api.tokenfactory.nebius.com/sandboxes"


def config_status(env) -> dict:
    required = {
        "token_factory": ["TOKEN_FACTORY_API_KEY", "MODEL_NANO", "MODEL_SUPER", "MODEL_ULTRA"],
        "sandboxes": ["SANDBOX_API_KEY", "NEBIUS_PROJECT_ID"],
    }
    result = {
        service: {
            "status": "configured" if all(env.get(k) for k in keys) else "pending",
            "missing": [k for k in keys if not env.get(k)],
        }
        for service, keys in required.items()
    }
    try:
        result["contree_sdk"] = {"status": "installed", "version": version("contree-sdk")}
    except PackageNotFoundError:
        result["contree_sdk"] = {"status": "missing", "install": "pip install -e .[platform]"}
    return result


def token_probe(env, client: httpx.Client) -> dict:
    headers = {"Authorization": f"Bearer {env['TOKEN_FACTORY_API_KEY']}"}
    base = env.get("TOKEN_FACTORY_BASE_URL", DEFAULT_TOKEN_URL).rstrip("/")
    response = client.get(f"{base}/models", headers=headers)
    response.raise_for_status()
    available = {m["id"] for m in response.json()["data"]}
    results = {}
    for tier in ("nano", "super", "ultra"):
        model = env[f"MODEL_{tier.upper()}"]
        if model not in available:
            results[tier] = {"model": model, "status": "model_not_in_catalog"}
            continue
        started = time.perf_counter()
        try:
            completion = client.post(
                f"{base}/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Reply only FORK_OK."}],
                    "max_tokens": 256,
                },
            )
            completion.raise_for_status()
            payload = completion.json()
            content = payload["choices"][0]["message"].get("content")
            results[tier] = {
                "model": model,
                "status": "passed" if content else "empty_response",
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "usage": payload.get("usage", {}),
            }
        except Exception as exc:
            results[tier] = safe_failure(exc)
    return {
        "status": "passed" if all(r["status"] == "passed" for r in results.values()) else "failed",
        "models": results,
        "nemotron_catalog_ids": sorted(m for m in available if "nemotron" in m.lower()),
    }


def safe_failure(exc: Exception) -> dict:
    result = {"status": "failed", "error_type": type(exc).__name__}
    if isinstance(exc, httpx.HTTPStatusError):
        result["http_status"] = exc.response.status_code
    # Do not include exception messages, request headers, bodies or SDK object reprs.
    return result


async def sandbox_probe(env) -> dict:
    from contree_sdk import Contree
    from contree_sdk.auth import IAMAuth
    from contree_sdk.config import ContreeConfig

    base_url = env.get("SANDBOX_BASE_URL", DEFAULT_SANDBOX_URL).rstrip("/")
    headers = {
        "Authorization": f"Bearer {env['SANDBOX_API_KEY']}",
        "Project": env["NEBIUS_PROJECT_ID"],
    }
    async with httpx.AsyncClient(timeout=20) as http:
        response = await http.get(f"{base_url}/v1/whoami", headers=headers)
        response.raise_for_status()
        limits = response.json().get("limits", {})
    client = Contree(
        config=ContreeConfig(
            auth=IAMAuth(
                token=env["SANDBOX_API_KEY"], project_id=env["NEBIUS_PROJECT_ID"], base_url=base_url
            ),
            operation_timeout=60,
        )
    )
    started = time.perf_counter()
    base = await client.images.use(env.get("SANDBOX_BASE_IMAGE", "alpine:3.19"), strict=True)
    checkpoint = await base.run(
        shell="printf 'FORK_OK\\n' > /tmp/fork-phase0.txt", disposable=False, timeout=20
    )
    if checkpoint.exit_code != 0 or checkpoint.uuid is None:
        return {"status": "failed", "stage": "save_checkpoint"}
    # Two independent operations read the same immutable filesystem checkpoint.
    children = await asyncio.gather(
        *[
            checkpoint.run(shell="cat /tmp/fork-phase0.txt", disposable=True, timeout=20)
            for _ in range(2)
        ]
    )
    passed = all(r.exit_code == 0 and r.stdout.strip() == "FORK_OK" for r in children)
    return {
        "status": "passed" if passed else "failed",
        "limits": limits,
        "checkpoint_id": str(checkpoint.uuid),
        "parallel_reads": 2,
        "latency_ms": round((time.perf_counter() - started) * 1000),
        "note": "Saved one tiny checkpoint; no packages installed or maximum load tested.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live", action="store_true", help="Run metered hello calls and sandbox jobs"
    )
    parser.add_argument("--service", choices=["all", "token_factory", "sandboxes"], default="all")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/platform-check.local.json")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env", override=False)
    report = {
        "checked_at": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        "mode": "live" if args.live else "configuration_only",
        **config_status(os.environ),
    }
    if args.live:
        for service in ("token_factory", "sandboxes"):
            if args.service not in ("all", service) or report[service]["status"] != "configured":
                continue
            try:
                if service == "token_factory":
                    with httpx.Client(timeout=60) as client:
                        report[service] = token_probe(os.environ, client)
                else:
                    report[service] = asyncio.run(asyncio.wait_for(sandbox_probe(os.environ), 150))
            except Exception as exc:
                report[service] = safe_failure(exc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    services = ("token_factory", "sandboxes") if args.service == "all" else (args.service,)
    expected = "passed" if args.live else "configured"
    if any(report[s]["status"] != expected for s in services):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
