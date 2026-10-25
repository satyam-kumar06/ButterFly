import copy
import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from apps.api.contracts import (
    DecisionSpec,
    Distribution,
    Frontier,
    InterviewNextResponse,
    Results,
    SimProgressData,
    StreamEvent,
    WhatIfResponse,
    WinProbability,
)

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / "mocks" / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("pack", ["offer_xray", "fine_print"])
def test_complete_fixture_contract(pack):
    spec = DecisionSpec.model_validate(read(f"spec_{pack}.json"))
    result = Results.model_validate(read(f"results_{pack}.json"))
    assert result.primary_metric == spec.metrics.primary
    assert result.objective == spec.metrics.direction
    assert result.data_kind == "mock"
    assert result.path_count == 10000
    assert len(result.x_points) == 16
    for option in (result.options.A, result.options.B):
        assert len(option.sampled_paths) == 1000
        assert len(option.path_stories) == 1000
    assert len(result.frontier.grid) == 12
    assert len(result.frontier.grid[0]) == 12


@pytest.mark.parametrize(
    "distribution",
    [
        {"type": "normal", "mean": 0, "std": -1},
        {"type": "normal", "mean": float("nan"), "std": 1},
        {"type": "lognormal", "mu": 0, "sigma": -1},
        {"type": "uniform", "low": 4, "high": 4},
        {"type": "triangular", "low": 1, "mode": 5, "high": 2},
        {"type": "bernoulli", "p": 1.1},
        {"type": "discrete", "values": [1, 2], "probs": [0.2, 0.2]},
        {"type": "discrete", "values": [1, 1], "probs": [0.5, 0.5]},
        {"type": "discrete", "values": [1, 2], "probs": [1]},
        {"type": "normal", "mean": 0, "std": 1, "invented_parameter": 4},
    ],
)
def test_reject_invalid_distributions(distribution):
    with pytest.raises(ValidationError):
        TypeAdapter(Distribution).validate_python(distribution)


def test_reject_ambiguous_variable_and_duplicate_names():
    spec = read("spec_offer_xray.json")
    bad = copy.deepcopy(spec)
    bad["variables"][0]["dist"] = {"type": "bernoulli", "p": 0.5}
    with pytest.raises(ValidationError):
        DecisionSpec.model_validate(bad)
    spec["variables"].append(spec["variables"][0])
    with pytest.raises(ValidationError):
        DecisionSpec.model_validate(spec)


@pytest.mark.parametrize(
    "mutation",
    [
        "truncated_path",
        "story_order",
        "crossed_percentile",
        "hist_count",
        "nonfinite",
        "quarter",
        "missing_option",
    ],
)
def test_reject_misaligned_results(mutation):
    result = read("results_offer_xray.json")
    a = result["options"]["A"]
    if mutation == "truncated_path":
        a["sampled_paths"][0].pop()
    elif mutation == "story_order":
        a["path_stories"].reverse()
    elif mutation == "crossed_percentile":
        a["percentiles"]["p5"][0] = a["percentiles"]["p95"][0] + 1
    elif mutation == "hist_count":
        a["metrics"]["cumulative_in_hand"]["hist"]["counts"][0] += 1
    elif mutation == "nonfinite":
        a["sampled_paths"][0][0] = float("inf")
    elif mutation == "quarter":
        result["x_points"][0] = "Y1"
    else:
        del result["options"]["B"]
    with pytest.raises(ValidationError):
        Results.model_validate(result)


def test_ties_and_probability_validation():
    assert WinProbability(A=0, B=0, tie=1).tie == 1
    with pytest.raises(ValidationError):
        WinProbability(A=0.8, B=0.3)


def test_frontier_orientation_and_progress():
    with pytest.raises(ValidationError):
        Frontier(
            x_var="x",
            y_var="y",
            x_values=[0, 1, 2],
            y_values=[0, 1],
            grid=[[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]],
        )
    with pytest.raises(ValidationError):
        SimProgressData(fork_id="one", done=1001, total=1000)


def test_response_state_consistency():
    with pytest.raises(ValidationError):
        InterviewNextResponse(done=False, question=None)
    with pytest.raises(ValidationError):
        WhatIfResponse(type="out_of_scope", branch_id="unexpected")


def test_replay_lifecycle_and_matched_shard_counts():
    lines = (ROOT / "mocks/events_build.jsonl").read_text().splitlines()
    events = [TypeAdapter(StreamEvent).validate_json(line) for line in lines]
    assert [e.sequence for e in events] == list(range(1, len(events) + 1))
    assert len({e.id for e in events}) == len(events)
    assert [e.elapsed_ms for e in events] == sorted(e.elapsed_ms for e in events)
    assert all(e.data_kind == "mock" for e in events)
    forks = [e for e in events if e.event == "sandbox.fork" and e.data.purpose == "main"]
    assert len(forks) == 8
    progress = {}
    for e in events:
        if e.event == "sim.progress":
            assert e.data.done >= progress.get(e.data.fork_id, 0)
            progress[e.data.fork_id] = e.data.done
    assert set(progress) == {e.data.fork_id for e in forks}
    for option in ("A", "B"):
        assert sum(progress[e.data.fork_id] for e in forks if e.data.option_id == option) == 10000
    tests = [e for e in events if e.event == "test.result" and e.data.name == "test_clawback"]
    assert [(e.data.attempt, e.data.passed) for e in tests] == [(1, False), (2, True)]
    repaired = next(e.sequence for e in tests if e.data.passed)
    assert all(f.sequence > repaired for f in forks)
    assert next(e.sequence for e in events if e.event == "results.ready") > max(
        e.sequence for e in events if e.event == "sim.progress"
    )
