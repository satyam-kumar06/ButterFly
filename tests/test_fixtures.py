import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import numpy as np
import pytest
from pypdf import PdfReader

from mocks.demo_data import OFFERS, POLICIES
from mocks.make_mocks import make_results, path_arrays

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("pack,records", [("offer_xray", OFFERS), ("fine_print", POLICIES)])
def test_every_extraction_quote_exists_on_claimed_page(pack, records):
    terms = json.loads((ROOT / f"mocks/terms_{pack}.json").read_text())
    pages = {}
    for data in records.values():
        pdf = PdfReader(ROOT / "output/pdf" / data["filename"])
        assert len(pdf.pages) == 2
        pages[data["document_id"]] = [p.extract_text() for p in pdf.pages]
        assert all("FICTIONAL DEMO DOCUMENT" in text for text in pages[data["document_id"]])
    for term in terms:
        evidence = term["evidence"]
        text = pages[evidence["document_id"]][evidence["page"] - 1]
        assert evidence["quote"] in text
        assert term["value"] == records[term["option_id"]][term["field"]]


def test_ctc_reconciles_and_equity_reference_is_not_cash():
    components = [
        "annual_basic",
        "annual_hra",
        "annual_special_allowance",
        "annual_variable_target",
        "annual_employer_pf",
        "annual_gratuity_provision",
        "annual_equity_reference",
    ]
    for offer in OFFERS.values():
        assert sum(offer[k] for k in components) == offer["annual_ctc"]
    a = OFFERS["A"]
    assert a["equity_units"] * a["equity_reference_price"] / 4 == a["annual_equity_reference"]


def test_literal_payroll_oracle_arithmetic():
    data = json.loads((ROOT / "mocks/expected_payroll.json").read_text())
    for case in data["annual_cases"]:
        offer = OFFERS[case["option"]]
        gross = sum(offer[k] for k in ["annual_basic", "annual_hra", "annual_special_allowance"])
        gross += offer["annual_variable_target"] * case["payout_fraction"]
        assert gross == case["annual_gross"]
        net = (
            gross
            - case["annual_tax"]
            - data["annual_employee_pf"]
            - data["annual_professional_tax"]
        )
        assert net == case["annual_net"]
        assert round(net / 12, 2) == case["average_monthly_net"]
        taxable = (Decimal(gross - data["standard_deduction"]) / 10).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * 10
        assert taxable == case["taxable_rounded"]
        # Independently verify the hand-entered slab worksheet, not production finance code.
        slab = sum(
            max(Decimal(0), min(taxable - low, Decimal(400000))) * rate
            for low, rate in [
                (400000, Decimal(".05")),
                (800000, Decimal(".10")),
                (1200000, Decimal(".15")),
            ]
        )
        assert slab == Decimal(str(case["slab_tax"]))
        relief = 0 if taxable <= 1200000 else min(slab, taxable - 1200000)
        assert relief == case["tax_after_rebate_relief"]
        tax = (Decimal(relief) * Decimal("1.04") / 10).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * 10
        assert tax == case["annual_tax"]
    for slip in data["monthly_slips"]:
        net = Decimal(str(slip["gross"])) - sum(
            Decimal(str(slip[k])) for k in ["employee_pf", "professional_tax", "tds"]
        )
        assert net == Decimal(str(slip["net"]))
    for option in ("A", "B"):
        slips = [s for s in data["monthly_slips"] if s["option"] == option]
        annual = next(
            c["annual_net"] for c in data["annual_cases"] if c["id"] == f"{option}_target"
        )
        assert (
            sum(Decimal(str(s["net"])) * (10 if s["month"] == "April" else 1) for s in slips)
            == annual
        )


def test_claim_references_match_the_written_examples():
    data = json.loads((ROOT / "mocks/expected_claims.json").read_text())
    for case in data["cases"]:
        assert case["expected_insurer"] + case["expected_oop"] == case["bill"]
    assert (100000 * 5000 / 8000 - 10000) * 0.8 == 42000
    assert 100000 - (12000 - 10000) * 4 == 92000


@pytest.mark.parametrize("pack", ["offer_xray", "fine_print"])
def test_mock_statistics_come_from_all_paths(pack):
    a, b, _ = path_arrays(pack)
    result = make_results(pack)
    win_a = a[:, -1] > b[:, -1] if result.objective == "maximize" else a[:, -1] < b[:, -1]
    assert result.p_win.A == float(np.mean(win_a))
    assert result.options.A.percentiles.p50 == np.median(a, axis=0).round(2).tolist()
    for option_id, paths in (("A", a), ("B", b)):
        option = getattr(result.options, option_id)
        sample_ids = [s.id for s in option.path_stories]
        assert option.sampled_paths == paths[sample_ids].round(2).tolist()
