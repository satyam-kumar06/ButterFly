"""forklib: the trusted, hand-tested building blocks every Fork simulation is made of.

Agent-written models compose these functions instead of inventing finance maths.
Every function is vectorised over simulated futures (no Python loops over paths)
and has a docstring with a worked example; those docstrings become the API
reference in the model-writing prompt (see api_reference()).
"""

from forklib.esop import esop_value, exit_price, vested_units
from forklib.events import event_mask, monthly_probability, poisson_counts
from forklib.finance import (
    clawback_due,
    cumulative_quarterly,
    emi,
    fy_month,
    inflate,
    salary_path,
)
from forklib.rules import (
    annual_professional_tax,
    gratuity,
    income_tax,
    pf_contribution,
    professional_tax,
    tax_on_salary,
    taxable_income,
)
from forklib.sampling import dist_quantiles, sample, sample_variable, stream

__all__ = [
    "annual_professional_tax",
    "clawback_due",
    "cumulative_quarterly",
    "dist_quantiles",
    "emi",
    "esop_value",
    "event_mask",
    "exit_price",
    "fy_month",
    "gratuity",
    "income_tax",
    "inflate",
    "monthly_probability",
    "pf_contribution",
    "poisson_counts",
    "professional_tax",
    "salary_path",
    "sample",
    "sample_variable",
    "stream",
    "tax_on_salary",
    "taxable_income",
    "vested_units",
]


def api_reference() -> str:
    """Signature + docstring of every public function, for Ultra's prompt (task A5)."""
    import inspect

    parts = []
    for name in __all__:
        fn = globals()[name]
        parts.append(f"### forklib.{name}{inspect.signature(fn)}\n{inspect.getdoc(fn) or ''}")
    return "\n\n".join(parts)
