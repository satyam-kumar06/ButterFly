"""forklib primitives (task B2): known answers, vectorisation and the docstring examples."""

from __future__ import annotations

import doctest
import importlib

import numpy as np
import pytest

import forklib
from forklib import (
    clawback_due,
    cumulative_quarterly,
    emi,
    esop_value,
    event_mask,
    fy_month,
    inflate,
    monthly_probability,
    salary_path,
    sample,
    sample_variable,
    stream,
    vested_units,
)

MODULES = [
    "forklib.sampling",
    "forklib.finance",
    "forklib.events",
    "forklib.esop",
    "forklib.rules.india_tax",
    "forklib.rules.pf",
    "forklib.rules.professional_tax",
    "forklib.rules.gratuity",
]


@pytest.mark.parametrize("name", MODULES)
def test_docstring_examples(name):
    mod = importlib.import_module(name)
    failed, attempted = doctest.testmod(mod, optionflags=doctest.ELLIPSIS)
    assert attempted > 0, f"{name} needs a worked example"
    assert failed == 0


# --- sampling ---------------------------------------------------------------

DISTS = [
    ({"type": "normal", "mean": 5, "std": 2}, 5, 2),
    ({"type": "uniform", "low": 0, "high": 10}, 5, 10 / 12**0.5),
    ({"type": "triangular", "low": 0, "mode": 3, "high": 6}, 3, (6**2 / 24) ** 0.5),
    ({"type": "bernoulli", "p": 0.3}, 0.3, (0.21) ** 0.5),
    ({"type": "discrete", "values": [1, 2, 3], "probs": [0.2, 0.5, 0.3]}, 2.1, 0.7),
    ({"type": "lognormal", "mu": 0.0, "sigma": 0.5}, np.exp(0.125), None),
]


@pytest.mark.parametrize(("dist", "mean", "sd"), DISTS)
def test_sample_moments(dist, mean, sd):
    x = sample(dist, np.random.default_rng(1), 200_000)
    assert x.shape == (200_000,)
    assert abs(x.mean() - mean) < 0.02 * max(1, abs(mean))
    if sd is not None:
        assert abs(x.std() - sd) < 0.02 * max(1, sd)


def test_sample_accepts_contract_models_and_shapes():
    from apps.api.contracts import Triangular

    d = Triangular(type="triangular", low=0.4, mode=0.8, high=1.0)
    x = sample(d, np.random.default_rng(0), (100, 4))
    assert x.shape == (100, 4) and x.min() >= 0.4 and x.max() <= 1.0


def test_sample_clip_and_unknown_type():
    x = sample({"type": "normal", "mean": 0, "std": 5}, np.random.default_rng(0), 1000, clip_low=0)
    assert x.min() == 0
    with pytest.raises(ValueError):
        sample({"type": "pareto"}, np.random.default_rng(0), 3)


def test_sample_variable_fixed_and_text():
    rng = np.random.default_rng(0)
    assert sample_variable({"kind": "fixed", "value": 22000.0}, rng, 3).tolist() == [22000.0] * 3
    assert sample_variable({"kind": "fixed", "value": "new"}, rng, 3) == "new"
    assert sample_variable({"kind": "fixed", "value": True}, rng, 3) is True


def test_streams_are_reproducible_and_independent():
    a1 = stream(42, "layoff").random(5)
    a2 = stream(42, "layoff").random(5)
    b = stream(42, "hike").random(5)
    assert np.array_equal(a1, a2)
    assert not np.array_equal(a1, b)


# --- finance -----------------------------------------------------------------


def test_emi_known_answers():
    assert emi(120_000, 0, 12) == 10_000
    assert round(emi(1_000_000, 0.09, 120), 2) == 12667.58
    with pytest.raises(ValueError):
        emi(1, 0.1, 0)


def test_inflate_and_salary_path():
    assert inflate(100, 0.1, 2) == pytest.approx(121)
    path = salary_path(100.0, np.array([0.1, 0.0]), 36)
    assert path.shape == (2, 36)
    assert (
        path[0, 11] == 100
        and path[0, 12] == pytest.approx(110)
        and path[0, 35] == pytest.approx(121)
    )
    assert np.all(path[1] == 100)
    yearly = salary_path(100.0, np.array([[0.1, 0.2]]), 36)
    assert yearly[0, 24] == pytest.approx(132)


def test_higher_hike_never_lowers_salary():
    p = salary_path(1000.0, np.array([0.05, 0.08]), 60)
    assert np.all(p[1] >= p[0])


def test_clawback_boundaries_match_fixture_rule():
    exits = np.array([1, 11, 12, 30])
    assert clawback_due(150_000, 12, exits).tolist() == [150000, 150000, 0, 0]
    assert clawback_due(0, 12, exits).tolist() == [0, 0, 0, 0]
    assert clawback_due(150_000, 0, exits).tolist() == [0, 0, 0, 0]


def test_cumulative_quarterly_and_fy_month():
    m = np.ones((2, 12))
    assert cumulative_quarterly(m).tolist() == [[3, 6, 9, 12]] * 2
    assert fy_month(np.arange(1, 13)).tolist() == [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]


# --- events ------------------------------------------------------------------


def test_monthly_probability_preserves_yearly_total():
    p = monthly_probability(0.06)
    assert 1 - (1 - p) ** 12 == pytest.approx(0.06)


def test_event_rate_and_durations():
    mask, first = event_mask(0.06, stream(7, "layoff"), 100_000, 12, duration=(1, 1), max_events=1)
    assert abs((first > 0).mean() - 0.06) < 0.005
    mask, first = event_mask(0.5, stream(7, "x"), 2000, 48, duration=(2, 5), max_events=1)
    lengths = mask.sum(axis=1)[first > 0]
    tail_ok = first[first > 0] + lengths - 1 <= 48
    assert lengths[tail_ok & (first[first > 0] <= 44)].min() >= 2
    assert lengths.max() <= 5


def test_zero_probability_means_no_events():
    mask, first = event_mask(0.0, stream(1, "none"), 100, 24)
    assert not mask.any() and not first.any()


# --- equity ------------------------------------------------------------------


def test_vesting_schedule():
    months = np.array([0, 11, 12, 13, 24, 48, 60])
    assert vested_units(400, 12, 48, months).tolist() == [0, 0, 100, 400 * 13 / 48, 200, 400, 400]
    assert vested_units(0, 12, 48, months).sum() == 0


def test_esop_value_zero_price_and_strike():
    exits = np.array([12, 12, 48])
    prices = np.array([1537.85, 0.0, 100.0])
    assert esop_value(400, 0, 12, 48, exits, prices).round(2).tolist() == [153785.0, 0.0, 40000.0]
    assert esop_value(400, 150, 12, 48, np.array([48]), 100.0).tolist() == [0.0]


def test_api_reference_lists_every_public_function():
    ref = forklib.api_reference()
    for name in forklib.__all__:
        assert f"forklib.{name}(" in ref
