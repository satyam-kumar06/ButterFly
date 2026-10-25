# Phase 0 handoff

Updated 2026-10-25. Local foundation delivered; **Phase 0 cannot be called fully
closed until platform access and the three-person contract review are complete.**

| Task | Status | Evidence / remaining action |
| --- | --- | --- |
| 0.1 Shared contracts | Implemented; team review pending | `apps/api/contracts.py`, `docs/contracts.md`, seven generated schemas and generated TypeScript. Three builders should review the recorded decisions before splitting. |
| 0.2 Mock data | Implemented | Both packs, 10,000 synthetic paths, 1,000 matched display samples, percentiles, histograms, frontier, terms and timed build replay. All visibly mock. |
| 0.3 Repository | Implemented; main protection verified | MIT license, README, ignored `.env`, Python/Node dependencies, CI, branch protection payload, contribution and PR workflow. |
| 0.4 Platform access | **Blocked on account access** | Owner confirmed access still needed. SDK installed; docs and local API signatures reviewed. Config checker and metered live probes provided. No live calls passed. |
| 0.5 Fictional documents | Implemented | Four two-page PDFs, exact extraction quotes, six monthly payslips, six annual payout cases, clawback/equity and policy claim reference values. |

## Verification

35 Python tests passed locally. Ruff lint/format, schema/type/mock/PDF drift checks,
TypeScript compilation and Vite production build passed. All eight PDF pages were
rendered and visually inspected; both packs loaded in the browser. Vite reports
large mock-data chunks; they are loaded on demand, not in the initial JS bundle.
See the PR's checks for remote execution. Mocks are contract-valid, not a validation
of real finance.

## Team handoff

- Brain starts with A1 backend routes/SSE against these fixtures, then A2 client.
- Engine starts with B1 sandbox spike once access is activated, and can work on
  trusted primitives and fixture-derived golden tests independently.
- Face starts C1 with generated types and mocks. The Phase 0 inspector is a temporary
  developer page, not the finished product design.

The real team members still need to agree to contracts and use their own platform
accounts. This work does not impersonate their approval or create accounts for them.
Complete live checks after access arrives, record timings/limits/errors in
`platform-notes.md`, and revisit model IDs/network controls before running generated code.

## Remote repository

Repository confirmed public: `satyam-kumar06/ButterFly`. Main protection was applied
and read back through GitHub's API: one approving review, stale review dismissal,
required **Python checks** and **Frontend build**, strict up-to-date branches,
resolved conversations, enforcement for admins, no force-pushes or branch deletion.
Changes are on `codex/phase-0` for a draft PR; main remains subject to team review.
