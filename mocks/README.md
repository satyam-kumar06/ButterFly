# Synthetic fixtures

Run `python -m mocks.make_mocks` from the repo root; `--check` verifies committed
outputs without writing. The seed is 20261025 (Fine Print adds one). NumPy is pinned
in the dependency lock so fixtures can be reproduced in CI.

- `spec_*.json`: both launch packs, real contract shape, invented input data.
- `results_*.json`: 10,000 synthetic paths, 1,000 matched display paths per option,
  sixteen quarters, seven percentiles, complete histograms, sweeps and 12x12 frontier.
- `terms_*.json`: exact page-one quotes from the fictional PDFs, with expected values.
- `branches_*.json`: one original branch per pack, ready for branch-tree scaffolding.
- `events_build.jsonl`: 9.4-second build replay, absolute offsets in milliseconds.
  It includes a scripted failure, repair, ten total forks (two test attempts + eight
  simulation shards), progress, results and flip readiness. Model counts are synthetic.
- `expected_payroll.json`, `expected_claims.json`: independent literal reference values
  for later golden tests. Do not regenerate these from the production calculation code.

The random walks are deliberately simple. Offer A's synthetic final gap is
`(tenure-17)*5000 + (payout-.8)*300000 + noise`; the sampled baseline uses tenure 24
and payout .8. Insurance's synthetic OOP difference is `(room_cost-6500)*days + noise`.
The sweeps and frontier reuse that same noise, so the baseline win rate and frontier
refer to the same toy experiment. Thresholds use its empirical median, not the
headline numbers in the original pitch. These mechanisms **do not implement the
offer or insurance terms**. The handwritten claim and payroll reference cases do.

Use `data_kind=mock` visibly everywhere. The replay code chunks are display strings;
never execute them. Production results and live test-repair events must come from
actual agent/sandbox work. Mock assets are dynamically imported by the Phase 0
inspector; production screens and a timed replay hook belong to Phase 1 C1/A1.
