"""Fine Print template model (task B5): which health policy protects a family better.

Same interface as every pack model (see packs/README.md). Lower is better here:
"cumulative" is total cost so far (premiums + out of pocket).

One future, year by year:
  * Pay the premium at the start of each policy year (rising by premium_increase).
  * Each member has Poisson-many hospital stays (rate by age band x a family
    multiplier). Each stay: days, room cost per day for the room the user picks,
    other charges; costs rise with medical inflation.
  * Stays are settled in date order through forklib.apply_policy_to_claim, which
    applies waiting period, sub-limit, room rule, deductible, co-pay, remaining
    cover and restoration in the policy's order. Renewal updates the no-claim bonus.
  * Out of pocket = bill - insurer payment.

Common random numbers: hospital stays are drawn from streams named for the
member and year, so policies A and B are tested against exactly the same illnesses.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from forklib import PolicyState, apply_policy_to_claim, cumulative_quarterly, sample
from packs.common import SpecView, load_json

DEFAULTS = load_json(Path(__file__).with_name("defaults.json"))
POLICY_FIELDS = [
    "sum_insured",
    "annual_premium_inclusive",
    "room_rent_limit_per_day",
    "proportionate_deduction",
    "copay",
    "deductible_per_claim",
    "cataract_sublimit_per_eye",
    "initial_wait_days",
    "specific_wait_months",
    "preexisting_wait_months",
    "restoration_count",
    "restoration_amount",
    "ncb_per_claim_free_year",
    "ncb_max",
]


def _rate(age: float) -> float:
    for lo, hi, r in DEFAULTS["rates_per_year_by_age"]["bands"]:
        if lo <= age < hi:
            return r
    return DEFAULTS["rates_per_year_by_age"]["bands"][-1][2]


def member_ages(s: SpecView) -> list[float]:
    ages = []
    k = 1
    while s.has(f"member_{k}_age"):
        ages.append(float(s.scalar(f"member_{k}_age")))
        k += 1
    if not ages:
        raise ValueError("Fine Print needs at least member_1_age")
    return ages


def simulate(option_id: str, spec: dict, rng: np.random.Generator, n: int) -> dict:
    s = SpecView(spec, DEFAULTS, rng, n)
    Y, M = s.years, s.months
    policy = {f: s.scalar(f"{option_id}.{f}", 0) for f in POLICY_FIELDS}
    ages = member_ages(s)
    K = int(DEFAULTS["max_stays_per_member_per_year"])

    # shared uncertainty (same for A and B)
    mult = s.draw("hosp_rate_multiplier", clip=(0, None))
    infl = s.draw("medical_inflation", clip=(-0.05, 0.5))
    room0 = s.draw("room_cost_per_day")
    prem_inc = s.draw(f"{option_id}.premium_increase", clip=(0, 1))

    state = PolicyState.new(policy, n)
    monthly_cost = np.zeros((n, M))
    oop_total = np.zeros(n)
    prem_total = np.zeros(n)
    year_cost = np.zeros((n, Y))
    stays_total = np.zeros(n)
    worst_stay_oop = np.zeros(n)

    for y in range(Y):
        if y > 0:
            state.renew(policy)
        premium = float(policy["annual_premium_inclusive"]) * (1 + prem_inc) ** y
        monthly_cost[:, 12 * y] += premium
        prem_total += premium
        year_cost[:, y] += premium
        f = (1 + infl) ** y

        # draw every possible stay slot for this year: members x K
        slots = []
        for j, age in enumerate(ages):
            r = s.rng(f"stay:{j}:{y}")
            count = r.poisson(_rate(age + y) * mult)
            for k in range(K):
                present = count > k
                days = np.maximum(1, np.round(_draw(s, "hospital_days", r, n)))
                other = _draw(s, "other_charges_per_stay", r, n)
                day_of_year = r.integers(0, 365, n)
                slots.append((present, days, other, day_of_year))
        order = np.argsort(np.stack([np.where(p, d, 999) for p, _, _, d in slots], 1), axis=1)
        rows = np.arange(n)
        present_all = np.stack([sl[0] for sl in slots], 1)
        days_all = np.stack([sl[1] for sl in slots], 1)
        other_all = np.stack([sl[2] for sl in slots], 1)
        doy_all = np.stack([sl[3] for sl in slots], 1)
        for k in range(order.shape[1]):  # settle in date order; loop over slots, not futures
            col = order[:, k]
            present = present_all[rows, col]
            if not present.any():
                continue
            days, other, doy = days_all[rows, col], other_all[rows, col] * f, doy_all[rows, col]
            room = room0 * f
            bill = room * days + other
            pay = apply_policy_to_claim(
                bill,
                room,
                days,
                policy,
                state,
                admission_day=y * 365 + doy,
                active=present,
            )
            oop = np.where(present, bill - pay, 0.0)
            oop_total += oop
            year_cost[:, y] += oop
            stays_total += present
            worst_stay_oop = np.maximum(worst_stay_oop, oop)
            month = np.minimum(12 * y + doy // 31, M - 1).astype(int)
            np.add.at(monthly_cost, (rows, month), oop)

    cum_q = cumulative_quarterly(monthly_cost)
    return {
        "cumulative": cum_q,
        "metrics": {
            "out_of_pocket": oop_total,
            "total_cost": oop_total + prem_total,
            "premiums_paid": prem_total,
            "worst_year_cost": year_cost.max(axis=1),
            "any_year_over_1_lakh": (year_cost.max(axis=1) > 100_000).astype(float),
        },
        "story": {
            "stays": stays_total,
            "out_of_pocket": oop_total,
            "worst_stay_oop": worst_stay_oop,
            "premiums_paid": prem_total,
        },
    }


def _draw(s: SpecView, name: str, r: np.random.Generator, n: int) -> np.ndarray:
    """A per-stay value from the spec (fixed or distribution) or the pack default,
    drawn from the stay's own stream so both policies see the same stay."""
    v = s.vars.get(name) or DEFAULTS["variables"][name]
    if v["kind"] == "fixed":
        return np.full(n, float(v["value"]))
    return sample(v["dist"], r, n)


def story_lines(story: dict, i: int, label: str) -> list[str]:
    def lakh(x):
        return f"Rs {x / 1e5:.1f}L"

    stays = int(story["stays"][i])
    lines = [f"{stays} hospital stay{'s' if stays != 1 else ''}" if stays else "no hospital stays"]
    if stays:
        lines.append(f"worst single stay cost you {lakh(story['worst_stay_oop'][i])}")
    lines.append(f"paid {lakh(story['premiums_paid'][i])} in premiums to {label}")
    lines.append(f"out of pocket {lakh(story['out_of_pocket'][i])}")
    return lines
