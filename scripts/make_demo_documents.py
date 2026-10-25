"""Build four deterministic, visibly fictional PDF fixtures using ReportLab."""

import argparse
import io
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from mocks.demo_data import OFFERS, POLICIES, term_sentence

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"
rl_config.invariant = True
INK = colors.HexColor("#17283A")
TEAL = colors.HexColor("#007E87")
PALE = colors.HexColor("#EEF5F6")
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="DocTitle",
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=29,
        textColor=INK,
        spaceAfter=10,
    )
)
styles.add(ParagraphStyle(name="DocSub", fontSize=10, leading=14, textColor=TEAL, spaceAfter=12))
styles.add(ParagraphStyle(name="Text", fontSize=9, leading=13, textColor=INK, spaceAfter=7))
styles.add(ParagraphStyle(name="Row", fontSize=8.5, leading=12, textColor=INK, alignment=TA_LEFT))
styles.add(
    ParagraphStyle(
        name="Section",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=TEAL,
        spaceBefore=9,
        spaceAfter=8,
    )
)


def p(text, style="Text"):
    return Paragraph(escape(text), styles[style])


def footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(TEAL)
    canvas.rect(0, h - 6 * mm, w, 6 * mm, stroke=0, fill=1)
    canvas.setStrokeColor(colors.HexColor("#D8E3E8"))
    canvas.line(20 * mm, 17 * mm, w - 20 * mm, 17 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(INK)
    canvas.drawString(20 * mm, 12 * mm, "FORK / FICTIONAL DEMO DOCUMENT / NOT VALID FOR USE")
    canvas.drawRightString(w - 20 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


def term_table(data):
    fields = [(k, v) for k, v in data.items() if k not in {"document_id", "filename"}]
    # Single text cell preserves complete sentence evidence during PDF extraction.
    rows = [[p(term_sentence(key, value), "Row")] for key, value in fields]
    table = Table(rows, colWidths=[170 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [PALE, colors.white]),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def offer_pages(option, data):
    return [
        p(data["company"], "DocTitle"),
        p(f"Fictional offer letter | Option {option} | Fixture v1.0", "DocSub"),
        p(
            "To Demo Candidate: this invented offer is for testing Fork. No employment is offered. "
            "All monetary fields below are INR; annual fields are per year."
        ),
        term_table(data),
        PageBreak(),
        p("Offer terms", "DocTitle"),
        p(f"{data['company']} | Fictional terms continued", "DocSub"),
        p("1. Salary and CTC", "Section"),
        p(
            "Fixed annual gross equals basic plus HRA plus special allowance. Annual CTC equals "
            "fixed gross plus target variable pay, employer PF, gratuity provision "
            "and annual equity "
            "reference. Employee PF is deducted from gross and must not be added to CTC again. "
            "Employer PF and gratuity provision are not monthly cash payments."
        ),
        p("2. Variable pay and payroll", "Section"),
        p(
            "Variable pay is a discretionary annual payment at financial year end, between zero "
            "and the target stated above. It is not guaranteed. Fixed gross is paid monthly in "
            "twelve equal installments. Both employee and employer PF are contractually fixed at "
            "INR 1800 per month for this fixture. Professional tax and income tax are deducted "
            "as applicable; see the separate historical payroll test worksheet."
        ),
        p("3. Joining, relocation and leaving", "Section"),
        p(
            "Joining bonus and relocation reimbursement are outside the annual CTC shown above. "
            "A joining bonus, if nonzero, is paid with the first salary. If the final employment "
            "date is before the stated clawback month, the full gross joining bonus is repayable; "
            "at or after that month no repayment is due. Relocation is a reimbursement against "
            "receipts up to the stated maximum and has no clawback. There is no service bond. "
            "The notice period is calendar days; any notice buyout must be agreed separately."
        ),
        p("4. Equity and gratuity", "Section"),
        p(
            "Where equity units are nonzero, these are fictional RSUs with zero strike price. "
            "Twenty-five percent vests on completion of month 12, then the balance vests equally "
            "each month through month 48. Unvested units lapse on exit. The reference price is "
            "illustrative, not a guaranteed exit price; the value may be zero. Annual equity "
            "reference is one quarter of the original grant reference value. Gratuity provision "
            "is an employer CTC estimate, not a promise of payment or a substitute for the "
            "eligibility rules applicable at exit."
        ),
        p("Fixture boundary", "Section"),
        p(
            "This document contains no signature, bank details, identity numbers or real candidate "
            "data. No company or benefit described here should be treated as a real offer."
        ),
    ]


def policy_pages(option, data):
    harbor = option == "A"
    return [
        p(data["company"], "DocTitle"),
        p(f"{data['product']} | Fictional health policy | Option {option}", "DocSub"),
        p(
            "A synthetic policy wording for a two-adult family floater. All money is INR. "
            "These are invented contract terms, not a real insurance product or medical advice."
        ),
        term_table(data),
        Spacer(1, 8 * mm),
        p("Cover schedule", "Section"),
        p(
            "One annual family pool covers two demo adults aged 35 and 32. Premium is the total "
            "amount charged, inclusive of any applicable taxes. Renewal premiums are not "
            "guaranteed. The following page defines the exact claim order and worked examples."
        ),
        PageBreak(),
        p("How a claim is paid", "DocTitle"),
        p(f"{data['product']} | Clause order and examples", "DocSub"),
        p("1. Waiting periods", "Section"),
        p(
            "Non-accident admissions before day 30 are excluded. Accidents are exempt from the "
            "initial waiting period. Cataract and hernia have a 24-month specific waiting period. "
            "Declared pre-existing conditions have a "
            f"{data['preexisting_wait_months']}-month wait. "
            "If several waits apply, all must have expired. At the exact boundary cover starts."
        ),
        p("2. Claim calculation, in this order", "Section"),
        p(
            "Start with admissible hospital charges, excluding non-medical items. After waiting "
            "periods, cap cataract claims at the stated per-eye sub-limit. Next apply the room "
            "rule, then subtract the per-claim deductible (floor zero), then apply the co-pay "
            "to the remaining amount, then cap payment at remaining sum insured. Out-of-pocket "
            "equals the original hospital bill minus the insurer payment."
        ),
        p(
            "Room rule: multiply the whole eligible claim by min(1, room limit / actual daily "
            "room cost). This fictional proportionate deduction includes room and all linked "
            "medical charges."
            if harbor
            else "Room rule: no proportionate deduction. Only the room-charge excess "
            "above INR 10000 "
            "per day is excluded; other eligible charges are unaffected."
        ),
        p("3. Restoration and no-claim bonus", "Section"),
        p(
            "After the pool is fully exhausted, restore the base sum insured once per policy "
            "year for a subsequent unrelated admission. Restoration cannot top up the claim "
            "that exhausted the pool and cannot be used for the same illness. At renewal, a "
            "claim-free year adds the stated NCB share of base cover, up to the stated maximum. "
            "Any paid claim resets accumulated NCB to zero at the next renewal. Restoration "
            "expires at year end; base cover and NCB form the new opening pool."
        ),
        p("4. Worked examples (all waiting periods satisfied)", "Section"),
        p(
            "General treatment: bill INR 100000, four days in an INR 8000/day room, no exclusions "
            "or sub-limit, full pool remaining. Room ratio 5000/8000 = 0.625. Eligible amount "
            "62500; less deductible 10000 = 52500; insurer pays 80% = 42000. Family pays 58000. "
            "At INR 4000/day with the same bill, insurer pays (100000 - 10000) x 80% = 72000; "
            "family pays 28000."
            if harbor
            else "General treatment: bill INR 100000, four days in an INR 8000/day room, "
            "no exclusions "
            "or sub-limit, full pool remaining. No room excess, deductible or co-pay: insurer "
            "pays 100000 and family pays zero. At INR 12000/day with the same bill, room excess "
            "is (12000 - 10000) x 4 = 8000: insurer pays 92000; family pays 8000."
        ),
        p(
            "A non-accident admission on day 10 with an INR 50000 bill pays zero under either "
            "policy. These worked examples define this fixture only; production rules must "
            "follow the policy actually uploaded by the user."
        ),
    ]


def build_pdf(data, story) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=19 * mm,
        bottomMargin=23 * mm,
        title=f"Fork fictional fixture - {data['company']}",
        author="Fork contributors",
        pageCompression=1,
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        OUT.mkdir(parents=True, exist_ok=True)
    for records, maker in ((OFFERS, offer_pages), (POLICIES, policy_pages)):
        for option, data in records.items():
            content = build_pdf(data, maker(option, data))
            path = OUT / data["filename"]
            if args.check:
                if not path.exists() or path.read_bytes() != content:
                    raise SystemExit(f"Stale PDF fixture: {path.name}")
            else:
                path.write_bytes(content)
    print("Verified four PDF fixtures" if args.check else "Created four PDF fixtures")


if __name__ == "__main__":
    main()
