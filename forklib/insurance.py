"""Health insurance claim settlement, vectorised over futures (task B5).

Clauses apply in the order the fictional policy wordings state (page 2):

    1. waiting periods       initial (non-accident, before day 30), specific (cataract,
                             hernia: 24 months), pre-existing (policy-specific)
    2. sub-limit             cataract capped per eye
    3. room rule             proportionate: whole claim x min(1, limit / room cost per day)
                             otherwise: only the room excess above the limit is cut
    4. deductible            per claim, floor zero
    5. co-pay                share of what remains
    6. sum insured           pay at most the remaining pool; restoration refills the base
                             cover once a year after the pool is fully exhausted, for a
                             LATER claim only (never the claim that exhausted it)

Renewal: a claim-free year adds the no-claim bonus share of base cover (up to its max);
any paid claim resets it to zero. Restoration expires at year end.

Order matters: the same bill gives different payouts if clauses are reordered,
which is why each clause has its own test.

Example (Harbor worked example: Rs 1L bill, 4 days at Rs 8,000/day, limit Rs 5,000,
proportionate, Rs 10,000 deductible, 20% co-pay):
    >>> pol = {"sum_insured": 500000, "room_rent_limit_per_day": 5000,
    ...        "proportionate_deduction": True, "deductible_per_claim": 10000, "copay": 0.2}
    >>> st = PolicyState.new(pol, 1)
    >>> pay = apply_policy_to_claim(np.array([100000.0]), np.array([8000.0]), np.array([4.0]),
    ...                             pol, st, admission_day=np.array([800]))
    >>> float(pay[0])
    42000.0
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

GENERAL, CATARACT, HERNIA, PREEXISTING = 0, 1, 2, 3
SPECIFIC = (CATARACT, HERNIA)
DAYS_PER_MONTH = 365 / 12


def _g(policy: dict, key: str, default=0.0):
    v = policy.get(key, default)
    return default if v is None else v


@dataclass
class PolicyState:
    """Per-future pool for the current policy year."""

    base: float
    remaining: np.ndarray
    ncb: np.ndarray
    restorations_left: np.ndarray
    exhausted: np.ndarray
    claimed_this_year: np.ndarray

    @classmethod
    def new(cls, policy: dict, n: int) -> PolicyState:
        base = float(policy["sum_insured"])
        return cls(
            base=base,
            remaining=np.full(n, base),
            ncb=np.zeros(n),
            restorations_left=np.full(n, int(_g(policy, "restoration_count", 0))),
            exhausted=np.zeros(n, bool),
            claimed_this_year=np.zeros(n, bool),
        )

    def renew(self, policy: dict) -> None:
        """Start a new policy year: update NCB, reset pool and restoration."""
        step = float(_g(policy, "ncb_per_claim_free_year", 0)) * self.base
        cap = float(_g(policy, "ncb_max", 0)) * self.base
        self.ncb = np.where(self.claimed_this_year, 0.0, np.minimum(self.ncb + step, cap))
        self.remaining = self.base + self.ncb
        self.restorations_left[:] = int(_g(policy, "restoration_count", 0))
        self.exhausted[:] = False
        self.claimed_this_year[:] = False


def eligible_amount(
    bill, room_per_day, days, policy: dict, *, admission_day, condition=GENERAL, accident=False
) -> np.ndarray:
    """Steps 1-5: what the policy would pay before the sum-insured cap."""
    bill = np.asarray(bill, float)
    room = np.asarray(room_per_day, float)
    days = np.asarray(days, float)
    day = np.asarray(admission_day, float)
    cond = np.broadcast_to(np.asarray(condition), bill.shape)
    months_in = day / DAYS_PER_MONTH

    # 1. waiting periods (cover starts exactly at the boundary)
    blocked = (day < _g(policy, "initial_wait_days", 0)) & ~np.asarray(accident, bool)
    blocked |= np.isin(cond, SPECIFIC) & (months_in < _g(policy, "specific_wait_months", 0))
    blocked |= (cond == PREEXISTING) & (months_in < _g(policy, "preexisting_wait_months", 0))
    amount = np.where(blocked, 0.0, bill)

    # 2. cataract sub-limit
    sub = _g(policy, "cataract_sublimit_per_eye", 0)
    if sub:
        amount = np.where(cond == CATARACT, np.minimum(amount, sub), amount)

    # 3. room rule
    limit = _g(policy, "room_rent_limit_per_day", 0)
    if limit:
        if _g(policy, "proportionate_deduction", False):
            amount = amount * np.minimum(1.0, limit / np.maximum(room, 1e-9))
        else:
            amount = np.maximum(amount - np.maximum(room - limit, 0) * days, 0)

    # 4. deductible, 5. co-pay
    amount = np.maximum(amount - _g(policy, "deductible_per_claim", 0), 0)
    return amount * (1 - _g(policy, "copay", 0))


def apply_policy_to_claim(
    bill,
    room_per_day,
    days,
    policy: dict,
    state: PolicyState,
    *,
    admission_day,
    condition=GENERAL,
    accident=False,
    active: np.ndarray | None = None,
) -> np.ndarray:
    """Settle one claim per future (where `active`), updating `state`. Returns insurer pay."""
    bill = np.asarray(bill, float)
    active = np.ones(bill.shape, bool) if active is None else np.asarray(active, bool)
    payable = np.where(
        active,
        eligible_amount(
            bill,
            room_per_day,
            days,
            policy,
            admission_day=admission_day,
            condition=condition,
            accident=accident,
        ),
        0.0,
    )
    # 6. restoration: only for a claim AFTER the pool was fully exhausted
    restore = active & state.exhausted & (state.restorations_left > 0) & (payable > 0)
    state.remaining = np.where(
        restore, state.remaining + float(_g(policy, "restoration_amount", 0)), state.remaining
    )
    state.restorations_left = state.restorations_left - restore
    state.exhausted &= ~restore
    pay = np.minimum(payable, state.remaining)
    state.remaining = state.remaining - pay
    state.exhausted |= active & (state.remaining <= 0) & (pay > 0)
    state.claimed_this_year |= pay > 0
    return pay
