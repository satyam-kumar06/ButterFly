"""Copied into the sandbox next to Ultra's model.py and run with pytest.
Ultra never writes or edits this file."""

import pytest
from model import simulate  # the agent-written model under test

try:
    from checks import MODEL_CHECKS, check_claim_examples
except ImportError:  # running from the repo instead of the sandbox
    from packs.fine_print.golden.checks import MODEL_CHECKS, check_claim_examples


def test_claim_examples():
    check_claim_examples()


@pytest.mark.parametrize("check", MODEL_CHECKS, ids=lambda c: c.__name__)
def test_model(check):
    check(simulate)
