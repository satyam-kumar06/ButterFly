"""Real-world rules (tax, PF, professional tax, gratuity). Each module has a RULE_SOURCE."""

from forklib.rules.gratuity import gratuity, service_years
from forklib.rules.india_tax import income_tax, slab_tax, tax_on_salary, taxable_income
from forklib.rules.pf import pf_contribution, wages_under_codes
from forklib.rules.professional_tax import annual_professional_tax, professional_tax

__all__ = [
    "annual_professional_tax",
    "gratuity",
    "income_tax",
    "pf_contribution",
    "professional_tax",
    "service_years",
    "slab_tax",
    "tax_on_salary",
    "taxable_income",
    "wages_under_codes",
]
