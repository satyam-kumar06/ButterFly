"""Offer X-ray template model (task B4), hand-written by the Engine owner.

Two jobs:
  1. Fallback: if Ultra's model fails its tests three times, this runs instead.
  2. Example: it is pasted into Ultra's write_model prompt as the reference.

Interface (fixed, shared with agent-written models):

    simulate(option_id, spec, rng, n) -> {
        "cash_in_hand": (n, quarters) cumulative money in hand at each quarter end,
        "metrics": {name: (n,) array},          # includes the spec's primary metric
        "story":   {name: (n,) array},          # raw facts for hover stories
    }

Month 1 is April, the start of the financial year. All maths is vectorised over
the n futures; the only loop is over months/years, never over futures.

What one future looks like:
  * Join, get fixed pay monthly (rising by `annual_hike` each April) and the
    joining bonus in month 1.
  * Variable pay is paid each March at target x payout share, while still employed.
  * The original job ends at the earlier of: leaving voluntarily after
    `tenure_months`, or a layoff. Leaving early repays the joining bonus
    (voluntary exits only). Vested equity is realised when the job ends
    (or marked at its value at the horizon).
  * After a voluntary exit: a new job at (1 + switch_hike) x pay, no variable or
    equity. After a layoff: no pay for 2-5 months, then a job at the same pay.
  * Every financial year: tax on that year's salary income (fixed + variable +
    bonus + equity), spread evenly over the months worked, employee PF and
    state professional tax deducted monthly.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from forklib import (
    clawback_due,
    cumulative_quarterly,
    esop_value,
    event_mask,
    exit_price,
    fy_month,
    gratuity,
    professional_tax,
    salary_path,
    tax_on_salary,
)
from packs.common import SpecView, load_json

DEFAULTS = load_json(Path(__file__).with_name("defaults.json"))


def simulate(option_id: str, spec: dict, rng: np.random.Generator, n: int) -> dict:
    s = SpecView(spec, DEFAULTS, rng, n)
    M, Y = s.months, s.years
    month = np.arange(1, M + 1)  # 1-based simulation month
    year_of = (month - 1) // 12  # financial-year index 0..Y-1
    cal_month = fy_month(month)  # 4 = April ... 3 = March

    def term(field, default=None):
        return s.scalar(f"{option_id}.{field}", default)

    # ---- the offer (from the documents) --------------------------------------
    fixed_annual = (
        float(term("annual_basic"))
        + float(term("annual_hra"))
        + float(term("annual_special_allowance"))
    )
    fixed0 = fixed_annual / 12
    basic0 = float(term("annual_basic")) / 12
    var_target = float(term("annual_variable_target", 0.0))
    bonus = float(term("joining_bonus", 0.0))
    claw_months = float(term("clawback_months", 0.0))
    pf_month = float(term("employee_pf_monthly", 0.12 * basic0))
    location = str(term("location", "karnataka"))
    units = float(term("equity_units", 0.0))
    ref_price = float(term("equity_reference_price", 0.0))
    strike = float(term("equity_strike_price", 0.0))
    cliff = float(term("equity_cliff_months", 0.0))
    vest = float(term("equity_vesting_months", 0.0))
    regime = str(s.scalar("tax_regime"))
    fy = str(s.scalar("financial_year"))

    # ---- uncertainty (shared names => common random numbers) -----------------
    tenure = np.clip(np.round(s.draw("tenure_months")), 1, M + 1)  # >= M+1 means stays
    hike = s.draw("annual_hike", (n, Y), clip=(-0.10, 0.50))
    switch = s.draw("switch_hike", clip=(-0.20, 1.0))
    payout = s.draw(f"{option_id}.variable_payout", (n, Y), clip=(0.0, 1.5))
    lay = s.event("layoff")
    lo, hi = DEFAULTS["layoff_duration_months"]
    if lay is not None and lay["prob_per_year"] > 0:
        gap_mask, lay_start = event_mask(
            lay["prob_per_year"], s.rng("layoff"), n, M, duration=(lo, hi), max_events=1
        )
    else:
        gap_mask, lay_start = np.zeros((n, M), bool), np.zeros(n, int)
    price = exit_price(
        ref_price,
        s.rng(f"{option_id}.equity_price"),
        n,
        p_zero=float(s.scalar(f"{option_id}.equity_zero_chance")),
        sigma=float(s.scalar(f"{option_id}.equity_price_sigma")),
    )

    # ---- when does the original job end? --------------------------------------
    laid_off_first = (lay_start > 0) & (lay_start <= tenure)
    exit_month = np.where(laid_off_first, lay_start - 1, np.minimum(tenure, M))  # last month worked
    stayed = ~laid_off_first & (tenure > M)
    voluntary = ~laid_off_first & (tenure <= M)
    in_orig = month[None, :] <= exit_month[:, None]
    in_gap = gap_mask & ~in_orig  # a layoff gap only counts after the original job ended

    # ---- pay ----------------------------------------------------------------
    orig = salary_path(fixed0, hike, M)  # fixed pay if never leaving
    growth = orig / fixed0
    new_job = orig * np.where(voluntary, 1 + switch, 1.0)[:, None]
    fixed_pay = np.where(in_orig, orig, np.where(in_gap, 0.0, new_job))
    employed = fixed_pay > 0

    variable = np.zeros((n, M))
    for y in range(Y):  # paid in March (month 12, 24, ...) of each year
        m = 12 * (y + 1) - 1
        variable[:, m] = np.where(in_orig[:, m], var_target * payout[:, y] * growth[:, m], 0.0)

    bonus_pay = np.zeros((n, M))
    bonus_pay[:, 0] = np.where(exit_month >= 1, bonus, 0.0)

    equity_at = np.where(stayed, M, exit_month)
    equity_val = esop_value(units, strike, cliff, vest, equity_at, price)
    equity_pay = np.zeros((n, M))
    idx = np.clip(equity_at, 1, M).astype(int) - 1
    equity_pay[np.arange(n), idx] = equity_val

    claw = np.where(voluntary, clawback_due(bonus, claw_months, exit_month), 0.0)
    claw_pay = np.zeros((n, M))
    claw_pay[np.arange(n), idx] = claw

    grat = np.where(stayed, 0.0, gratuity(basic0 * growth[np.arange(n), idx], exit_month))
    grat_pay = np.zeros((n, M))
    grat_pay[np.arange(n), idx] = grat  # tax-exempt up to Rs 20L; never near that here

    taxable_m = fixed_pay + variable + bonus_pay + equity_pay

    # ---- deductions -----------------------------------------------------------
    tax_m = np.zeros((n, M))
    for y in range(Y):
        cols = year_of == y
        gross_y = taxable_m[:, cols].sum(axis=1)
        tax_y = tax_on_salary(gross_y, regime, fy)
        worked = employed[:, cols].sum(axis=1)
        per_month = np.divide(tax_y, worked, out=np.zeros(n), where=worked > 0)
        tax_m[:, cols] = per_month[:, None] * employed[:, cols]
    pf_m = np.where(employed, pf_month, 0.0)
    pt_m = np.where(employed, professional_tax(location, fixed_pay, cal_month[None, :]), 0.0)

    in_hand = taxable_m + grat_pay - claw_pay - tax_m - pf_m - pt_m

    # ---- outputs ----------------------------------------------------------------
    cum_q = cumulative_quarterly(in_hand)
    total = in_hand.sum(axis=1)
    rent = float(s.scalar(f"{option_id}.monthly_rent", 0.0))
    return {
        "cash_in_hand": cum_q,
        "metrics": {
            "cumulative_in_hand": total,
            "savings_after_rent": total - rent * M,
            "worst_month": in_hand.min(axis=1),
            "clawback_paid": claw,
            "equity_value": equity_val,
            "tax_paid": tax_m.sum(axis=1),
        },
        "story": {
            "exit_month": np.where(stayed, 0, exit_month),
            "voluntary_exit": voluntary.astype(float),
            "layoff_month": np.where(laid_off_first, lay_start, 0),
            "switch_hike": np.where(voluntary, switch, 0.0),
            "avg_variable_payout": payout.mean(axis=1) if var_target > 0 else np.zeros(n),
            "clawback_paid": claw,
            "equity_value": equity_val,
            "final_in_hand": total,
        },
    }


def story_lines(story: dict, i: int, label: str) -> list[str]:
    """Plain-language event log for future #i (used by hover cards, no LLM)."""

    def lakh(x):
        return f"Rs {x / 1e5:.1f}L"

    lines = []
    if story["avg_variable_payout"][i] > 0:
        lines.append(f"variable paid at {story['avg_variable_payout'][i] * 100:.0f}% on average")
    if story["layoff_month"][i]:
        lines.append(f"laid off in month {int(story['layoff_month'][i])}")
    elif story["exit_month"][i]:
        lines.append(
            f"switched jobs in month {int(story['exit_month'][i])} "
            f"for a {story['switch_hike'][i] * 100:.0f}% hike"
        )
    else:
        lines.append(f"stayed at {label} the whole time")
    if story["clawback_paid"][i] > 0:
        lines.append(f"repaid a {lakh(story['clawback_paid'][i])} joining bonus")
    if story["equity_value"][i] > 0:
        lines.append(f"equity worth {lakh(story['equity_value'][i])}")
    lines.append(f"ended with {lakh(story['final_in_hand'][i])} in hand")
    return lines
