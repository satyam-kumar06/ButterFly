"""Copied into the sandbox next to Ultra's model.py and run with pytest.
Ultra never writes or edits this file."""

import pytest
from model import simulate  # the agent-written model under test

try:
    from checks import ALL_CHECKS
except ImportError:  # running from the repo instead of the sandbox
    from packs.offer_xray.golden.checks import ALL_CHECKS


@pytest.mark.parametrize("check", ALL_CHECKS, ids=lambda c: c.__name__)
def test_golden(check):
    check(simulate)
