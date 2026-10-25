"""Golden and invariant checks for ANY Fine Print model (template or Ultra-written).

Claim golden values come from the policy wordings' own worked examples
(mocks/expected_claims.json). Ultra never writes or edits these.
"""

from __future__ import annotations

import copy
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
_CANDIDATES = [HERE, HERE.parents[2] / "mocks"]


def _load(name: str) -> dict:
    for d in _CANDIDATES:
        if (d / name).exists():
            return json.loads((d / name).read_text(encoding="utf-8"))
    raise FileNotFoundError(name)


def base_spec() -> dict:
    return _load("spec_fine_print.json")


def set_var(spec: dict, name: str, value) -> dict:
    new = dict(
        name=name,
        kind="fixed",
        value=value,
        unit="x",
        source="user",
        source_ref="golden test",
        confirmed=True,
        editable=True,
        sweep_range=None,
    )
    for i, v in enumerate(spec["variables"]):
        if v["name"] == name:
            spec["variables"][i] = new
            return spec
    spec["variables"].append(new)
    return spec


def _run(simulate, spec, option, n=300, seed=1):
    return simulate(option, spec, np.random.default_rng(seed), n)


def no_hospital(spec: dict | None = None) -> dict:
    s = copy.deepcopy(spec or base_spec())
    set_var(s, "hosp_rate_multiplier", 0.0)
    return s


# ---------------------------------------------------------------------------
# Golden claim settlement (policy wording examples)
# ---------------------------------------------------------------------------


def check_claim_examples() -> None:
    """forklib's claim engine reproduces every worked example in the wordings."""
    from forklib import PolicyState, apply_policy_to_claim

    try:
        from mocks.demo_data import POLICIES
    except ImportError:  # inside the sandbox: policies come from the spec
        POLICIES = _policies_from_spec(base_spec())
    for case in _load("expected_claims.json")["cases"]:
        pol = POLICIES[case["option"]]
        st = PolicyState.new(pol, 1)
        pay = apply_policy_to_claim(
            np.array([case["bill"]], float),
            np.array([case["room_per_day"]], float),
            np.array([case["days"]], float),
            pol,
            st,
            admission_day=np.array([case["admission_day"]]),
        )
        assert pay[0] == case["expected_insurer"], case["id"]
        assert case["bill"] - pay[0] == case["expected_oop"], case["id"]


def _policies_from_spec(spec: dict) -> dict:
    out = {"A": {}, "B": {}}
    for v in spec["variables"]:
        if v["name"][:2] in ("A.", "B.") and v["kind"] == "fixed":
            out[v["name"][0]][v["name"][2:]] = v["value"]
    return out


# ---------------------------------------------------------------------------
# Invariants for the model
# ---------------------------------------------------------------------------


def check_shapes_and_finite(simulate) -> None:
    spec = base_spec()
    q = spec["horizon_years"] * 4
    for opt in ("A", "B"):
        r = _run(simulate, spec, opt, n=500)
        assert r["cumulative"].shape == (500, q)
        assert np.isfinite(r["cumulative"]).all()
        assert spec["metrics"]["primary"] in r["metrics"]
        for name, arr in r["metrics"].items():
            assert arr.shape == (500,) and np.isfinite(arr).all(), name


def check_no_hospital_means_premiums_only(simulate) -> None:
    spec = no_hospital()
    for v in spec["variables"]:
        if v["name"].endswith("premium_increase"):
            v.update(kind="fixed", value=0.0)
            v.pop("dist", None)
    set_var(spec, "A.premium_increase", 0.0)
    set_var(spec, "B.premium_increase", 0.0)
    for opt in ("A", "B"):
        r = _run(simulate, spec, opt)
        prem = next(
            v["value"] for v in spec["variables"] if v["name"] == f"{opt}.annual_premium_inclusive"
        )
        assert np.all(r["metrics"]["out_of_pocket"] == 0)
        assert np.allclose(r["metrics"]["total_cost"], prem * spec["horizon_years"])


def check_pricier_room_never_costs_less(simulate) -> None:
    spec = base_spec()
    set_var(spec, "hosp_rate_multiplier", 2.0)
    cheap = copy.deepcopy(spec)
    set_var(cheap, "room_cost_per_day", 3000.0)
    dear = copy.deepcopy(spec)
    set_var(dear, "room_cost_per_day", 12000.0)
    for opt in ("A", "B"):
        lo = _run(simulate, cheap, opt)["metrics"]["out_of_pocket"]
        hi = _run(simulate, dear, opt)["metrics"]["out_of_pocket"]
        assert np.all(hi >= lo - 1e-6), opt


def check_common_random_numbers(simulate) -> None:
    spec = base_spec()
    a = _run(simulate, spec, "A", n=1000, seed=4)["story"]["stays"]
    b = _run(simulate, spec, "B", n=1000, seed=4)["story"]["stays"]
    assert np.array_equal(a, b)


def check_speed(simulate) -> None:
    spec = base_spec()
    t = time.perf_counter()
    for opt in ("A", "B"):
        _run(simulate, spec, opt, n=10_000)
    assert time.perf_counter() - t < 5.0


MODEL_CHECKS = [
    check_shapes_and_finite,
    check_no_hospital_means_premiums_only,
    check_pricier_room_never_costs_less,
    check_common_random_numbers,
    check_speed,
]
