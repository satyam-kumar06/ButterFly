"""Seeded random-walk fixtures, never finance predictions or live sandbox results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from pydantic import TypeAdapter

from apps.api.contracts import Branch, DecisionSpec, Results, StreamEvent, Term
from mocks.demo_data import OFFERS, POLICIES, term_sentence

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261025
N_PATHS = 10000
SAMPLES = 1000
YEARS = 4


def fixed(name, value, unit="INR", source="user", ref="demo interview", sweep=None):
    return {
        "kind": "fixed",
        "name": name,
        "value": value,
        "unit": unit,
        "source": source,
        "source_ref": ref,
        "confirmed": source == "user",
        "editable": True,
        "sweep_range": sweep,
    }


def distribution(name, dist, unit):
    return {
        "kind": "distribution",
        "name": name,
        "dist": dist,
        "unit": unit,
        "source": "default",
        "source_ref": "illustrative default",
        "confirmed": False,
        "editable": True,
    }


def make_spec(pack: str) -> DecisionSpec:
    offer = pack == "offer_xray"
    terms = OFFERS if offer else POLICIES
    variables = []
    for option, data in terms.items():
        for name, value in data.items():
            if name not in {"document_id", "filename", "company", "product"}:
                variables.append(
                    fixed(
                        f"{option}.{name}",
                        value,
                        "see document",
                        "data",
                        data["document_id"],
                    )
                )
    variables.extend(
        [
            fixed("tenure_months", 24, "months", sweep={"low": 6, "high": 48}),
            fixed("A.monthly_rent", 22000, sweep={"low": 15000, "high": 35000}),
            fixed("B.monthly_rent", 16000),
            distribution(
                "A.variable_payout",
                {"type": "triangular", "low": 0.4, "mode": 0.8, "high": 1.0},
                "share",
            ),
            distribution("annual_hike", {"type": "normal", "mean": 0.08, "std": 0.03}, "share"),
            fixed("tax_regime", "new", "regime"),
            fixed("financial_year", "2025-26", "FY", "data", "historical demo worksheet"),
        ]
        if offer
        else [
            fixed("room_cost_per_day", 8000, sweep={"low": 3000, "high": 12000}),
            fixed("hospital_days", 4, "days", sweep={"low": 1, "high": 10}),
            fixed("member_1_age", 35, "years"),
            fixed("member_2_age", 32, "years"),
            fixed("city", "Pune", "city"),
            distribution(
                "medical_inflation", {"type": "uniform", "low": 0.05, "high": 0.12}, "share"
            ),
        ]
    )
    return DecisionSpec.model_validate(
        {
            "decision_id": f"demo_{pack}",
            "title": "18 LPA vs 14 LPA" if offer else "Essential Family vs Flexible Family",
            "pack": pack,
            "horizon_years": YEARS,
            "options": [{"id": key, "label": value["company"]} for key, value in terms.items()],
            "variables": variables,
            "events": [
                {
                    "name": "layoff",
                    "prob_per_year": 0.06,
                    "effect": "income stops for two to five months",
                    "source": "default",
                    "source_ref": "illustrative default",
                }
            ]
            if offer
            else [],
            "metrics": {
                "primary": "cumulative_in_hand" if offer else "out_of_pocket",
                "direction": "maximize" if offer else "minimize",
                "others": ["savings_after_rent"] if offer else ["total_cost"],
            },
        }
    )


def path_arrays(pack: str):
    rng = np.random.default_rng(SEED + (pack == "fine_print"))
    common = rng.normal(0, 16000, (N_PATHS, YEARS * 4))
    if pack == "offer_xray":
        b = np.cumsum(270000 + common + rng.normal(0, 12000, common.shape), axis=1)
        noise = rng.normal(0, 90000, N_PATHS)
        difference = 35000 + noise  # synthetic gap at tenure=24, payout=.8
        a = b + difference[:, None] * np.arange(1, YEARS * 4 + 1) / (YEARS * 4)
    else:
        claims = rng.poisson(0.15, common.shape) * rng.lognormal(9.1, 0.7, common.shape)
        base = np.cumsum(claims, axis=1)
        noise = rng.normal(0, 12000, N_PATHS)
        # Extra room expense becomes an OOP gap. At 3000/day the cheaper room favors A.
        difference = 6000 + noise
        a = base + np.maximum(difference, 0)[:, None] * np.arange(1, YEARS * 4 + 1) / 16
        b = base + np.maximum(-difference, 0)[:, None] * np.arange(1, YEARS * 4 + 1) / 16
    return a, b, noise


def stats(values: np.ndarray) -> dict:
    counts, edges = np.histogram(values, bins=24)
    return {
        "median": round(float(np.median(values)), 2),
        "unit": "INR",
        "hist": {"edges": edges.round(2).tolist(), "counts": counts.tolist()},
    }


def make_results(pack: str) -> Results:
    spec = make_spec(pack)
    a, b, noise = path_arrays(pack)
    offer = pack == "offer_xray"
    # Matching samples spread across the joint outcome distribution, including both tails.
    ranking = np.argsort((a[:, -1] + b[:, -1]) / 2, kind="stable")
    indices = ranking[np.linspace(0, N_PATHS - 1, SAMPLES, dtype=int)]
    options = {}
    for option, paths in (("A", a), ("B", b)):
        pcts = np.percentile(paths, [5, 10, 25, 50, 75, 90, 95], axis=0).round(2)
        others = (
            paths[:, -1] - (22000 if option == "A" else 16000) * 48
            if offer
            else (paths[:, -1] + POLICIES[option]["annual_premium_inclusive"] * YEARS)
        )
        options[option] = {
            "label": next(o.label for o in spec.options if o.id == option),
            "percentiles": dict(
                zip(["p5", "p10", "p25", "p50", "p75", "p90", "p95"], pcts.tolist(), strict=True)
            ),
            "sampled_paths": paths[indices].round(2).tolist(),
            "path_stories": [
                {
                    "id": int(i),
                    "events": [
                        "Synthetic random-walk fixture; not a financial projection.",
                        f"Final {spec.metrics.primary}: INR {paths[i, -1]:.2f}",
                    ],
                }
                for i in indices
            ],
            "metrics": {
                spec.metrics.primary: stats(paths[:, -1]),
                spec.metrics.others[0]: stats(others),
            },
        }

    x_name, y_name = (
        ("tenure_months", "A.variable_payout") if offer else ("room_cost_per_day", "hospital_days")
    )
    x_lo, x_hi = (6, 48) if offer else (3000, 12000)
    y_lo, y_hi = (0.4, 1) if offer else (1, 10)
    x_current, y_current = (24, 0.8) if offer else (8000, 4)

    def win(x, y):
        gap = (x - 17) * 5000 + (y - 0.8) * 300000 if offer else (x - 6500) * y
        return float(np.mean(gap + noise > 0 if offer else gap + noise < 0))

    x_values, y_values = np.linspace(x_lo, x_hi, 12), np.linspace(y_lo, y_hi, 12)
    sensitivities = []
    for var, unit, low, high, axis in [
        (x_name, "months" if offer else "INR/day", x_lo, x_hi, "x"),
        (y_name, "share" if offer else "days", y_lo, y_hi, "y"),
    ]:
        points = [
            {"value": float(v), "p_win_A": win(v, y_current) if axis == "x" else win(x_current, v)}
            for v in np.linspace(low, high, 5)
        ]
        swing = max(p["p_win_A"] for p in points) - min(p["p_win_A"] for p in points)
        sensitivities.append({"variable": var, "unit": unit, "swing": swing, "points": points})
    sensitivities.sort(key=lambda s: s["swing"], reverse=True)
    p_a = float(np.mean(a[:, -1] > b[:, -1] if offer else a[:, -1] < b[:, -1]))
    p_b = float(np.mean(b[:, -1] > a[:, -1] if offer else b[:, -1] < a[:, -1]))
    # Exact empirical crossover of this toy mechanism, not a hand-planted claim about finance.
    threshold = (
        17 - float(np.median(noise)) / 5000
        if offer
        else (6500 - float(np.median(noise)) / y_current)
    )
    return Results.model_validate(
        {
            "branch_id": f"br_{pack}_root",
            "pack": pack,
            "data_kind": "mock",
            "horizon_years": YEARS,
            "path_count": N_PATHS,
            "seed": SEED + (not offer),
            "x_points": [f"Q{q}-Y{y}" for y in range(1, YEARS + 1) for q in range(1, 5)],
            "primary_metric": spec.metrics.primary,
            "objective": spec.metrics.direction,
            "options": options,
            "p_win": {"A": p_a, "B": p_b, "tie": float(np.mean(a[:, -1] == b[:, -1]))},
            "sensitivities": sensitivities,
            "flip_points": [
                {
                    "variable": x_name,
                    "threshold": threshold,
                    "unit": "months" if offer else "INR/day",
                    "direction": "below" if offer else "above",
                    "winner_after": "B",
                    "swing": next(s["swing"] for s in sensitivities if s["variable"] == x_name),
                    "bracket": {"low": x_lo, "high": x_hi},
                }
            ],
            "frontier": {
                "x_var": x_name,
                "y_var": y_name,
                "x_values": x_values.tolist(),
                "y_values": y_values.tolist(),
                "grid": [[win(x, y) for x in x_values] for y in y_values],
            },
            "story": f"MOCK DATA: Option A wins in {p_a:.1%} of synthetic paths. "
            "These fixtures test the interface; they are not decision advice.",
            "assumptions": [v.model_dump() for v in spec.variables],
        }
    )


def extracted_terms(pack: str) -> list[dict]:
    output = []
    for option, data in (OFFERS if pack == "offer_xray" else POLICIES).items():
        for field, value in data.items():
            if field in {"document_id", "filename"}:
                continue
            output.append(
                Term.model_validate(
                    {
                        "option_id": option,
                        "field": field,
                        "value": value,
                        "unit": "see document",
                        "confidence": 1.0,
                        "evidence": {
                            "document_id": data["document_id"],
                            "page": 1,
                            "quote": term_sentence(field, value),
                            "matched": True,
                        },
                    }
                ).model_dump()
            )
    return output


def make_events() -> list[dict]:
    events = []
    adapter = TypeAdapter(StreamEvent)

    def emit(ms, event, data):
        sequence = len(events) + 1
        events.append(
            adapter.validate_python(
                {
                    "id": f"demo_offer_xray:{sequence}",
                    "session_id": "demo_offer_xray",
                    "branch_id": "br_offer_xray_root",
                    "sequence": sequence,
                    "elapsed_ms": ms,
                    "data_kind": "mock",
                    "event": event,
                    "data": data,
                }
            ).model_dump()
        )

    emit(0, "agent.status", {"status": "extracting", "text": "MOCK replay: extracting offers"})
    for index, option in enumerate(("A", "B")):
        emit(
            200 + index * 200,
            "extract.done",
            {
                "document_id": OFFERS[option]["document_id"],
                "terms": [t for t in extracted_terms("offer_xray") if t["option_id"] == option],
            },
        )
    emit(500, "llm.call", {"tier": "nano", "tokens_in": 850, "tokens_out": 420, "ms": 400})
    emit(650, "agent.status", {"status": "interviewing", "text": "Demo answers confirmed"})
    emit(850, "llm.call", {"tier": "super", "tokens_in": 600, "tokens_out": 240, "ms": 200})
    emit(1000, "agent.status", {"status": "building", "text": "Writing a model (mock)"})
    emit(1100, "sandbox.fork", {"fork_id": "test_1", "parent": "demo_base", "purpose": "test"})
    emit(
        1300,
        "code.chunk",
        {
            "file": "model.py",
            "attempt": 1,
            "reset": True,
            "text": "# MOCK DISPLAY ONLY - never execute\n",
        },
    )
    emit(
        1600,
        "code.chunk",
        {
            "file": "model.py",
            "attempt": 1,
            "text": "def clawback(exit_month, amount):\n    return 0\n",
        },
    )
    emit(
        1900,
        "code.chunk",
        {
            "file": "test_model.py",
            "attempt": 1,
            "reset": True,
            "text": "def test_clawback():\n    assert clawback(6, 150000) == 150000\n",
        },
    )
    emit(
        2200,
        "test.result",
        {
            "name": "test_clawback",
            "passed": False,
            "message": "Expected 150000; got 0 (scripted fixture)",
            "attempt": 1,
        },
    )
    emit(2400, "agent.status", {"status": "building", "text": "Discarding failed attempt; fixing"})
    emit(2700, "sandbox.fork", {"fork_id": "test_2", "parent": "demo_base", "purpose": "test"})
    emit(
        3000,
        "code.chunk",
        {
            "file": "model.py",
            "attempt": 2,
            "reset": True,
            "text": "# MOCK DISPLAY ONLY\ndef clawback(exit_month, amount):\n"
            "    return amount if exit_month < 12 else 0\n",
        },
    )
    emit(
        3300,
        "test.result",
        {
            "name": "test_clawback",
            "passed": True,
            "message": "Passed (scripted fixture)",
            "attempt": 2,
        },
    )
    emit(
        3500,
        "test.result",
        {
            "name": "test_finite_outputs",
            "passed": True,
            "message": "Passed (scripted fixture)",
            "attempt": 2,
        },
    )
    emit(3700, "llm.call", {"tier": "ultra", "tokens_in": 1800, "tokens_out": 600, "ms": 2500})
    emit(4000, "agent.status", {"status": "simulating", "text": "Forking eight synthetic shards"})
    shards = [f"{option}_{i}" for option in ("A", "B") for i in range(4)]
    for i, shard in enumerate(shards):
        emit(
            4100 + i * 100,
            "sandbox.fork",
            {"fork_id": shard, "parent": "demo_model_v1", "purpose": "main", "option_id": shard[0]},
        )
    for step in range(1, 5):
        for i, shard in enumerate(shards):
            emit(
                5000 + step * 600 + i * 20,
                "sim.progress",
                {"fork_id": shard, "done": step * 625, "total": 2500},
            )
    emit(7800, "agent.status", {"status": "analyzing", "text": "Preparing mock flip points"})
    emit(9000, "results.ready", {"branch_id": "br_offer_xray_root"})
    emit(9200, "flip.ready", {"branch_id": "br_offer_xray_root"})
    emit(9400, "agent.status", {"status": "ready", "text": "Mock results ready"})
    return events


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n"


def artifacts() -> dict[str, str]:
    files = {}
    for pack in ("offer_xray", "fine_print"):
        spec = make_spec(pack)
        files[f"spec_{pack}.json"] = dumps(spec.model_dump())
        files[f"results_{pack}.json"] = dumps(make_results(pack).model_dump())
        files[f"terms_{pack}.json"] = dumps(extracted_terms(pack))
        branch = Branch(
            id=f"br_{pack}_root",
            session_id=f"demo_{pack}",
            parent_id=None,
            label="Original scenario",
            status="ready",
            change_type="root",
            spec=spec,
            model_version_id="demo_model_v1",
            checkpoint_id="demo_checkpoint",
            model_status="passed",
        )
        files[f"branches_{pack}.json"] = dumps({"branches": [branch.model_dump()]})
    files["events_build.jsonl"] = "".join(dumps(e) for e in make_events())
    return files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, content in artifacts().items():
        path = ROOT / "mocks" / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Stale mock: {name}")
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
    print("Mock fixtures verified" if args.check else "Generated mock fixtures")


if __name__ == "__main__":
    main()
