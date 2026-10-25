# Fork contracts v1.0.0

Status: implementation baseline for Phase 0, 2026-10-25. All three owners must review
contract changes. The source of truth is `apps/api/contracts.py`; JSON Schema and
TypeScript are generated, never maintained independently.

## Generation

```sh
python -m scripts.export_contracts
npm run contracts:types
python -m mocks.make_mocks
```

Commit the source, `docs/schemas/`, `apps/web/src/contracts.ts`, this document and
affected mocks together. CI checks drift and validates fixtures with Pydantic.
JSON Schema captures structural constraints; Pydantic additionally checks relationships
such as array lengths, ordered percentiles and probability totals.

## Decision Spec

Exactly two options, IDs `A` and `B`; INR; 1-20 years; monthly engine steps.
`metrics.direction` is `maximize` for in-hand money and `minimize` for out-of-pocket.
Every variable has a unique name, unit, source (`user`, `default`, `data`), nonempty
`source_ref`, confirmation flag and editable flag. A fixed variable has `value`;
a distribution variable has `dist`. Supplying both is invalid.

Distributions are discriminated by `type`: normal (`mean`, `std`), lognormal (`mu`,
`sigma`, natural-log parameters), triangular (`low`, `mode`, `high`), uniform (`low`,
`high`), Bernoulli (`p`), discrete (`values`, `probs`). All numbers must be finite.
Discrete probabilities sum to one; duplicate values are invalid. Fixed numerical
variables may declare `sweep_range`. Strings and categorical values cannot be bisected.

Documents use `source=data`, with `source_ref=document_id`. Unsourced defaults use
the exact label `illustrative default`. Sourced legal rules use `source=data`, an
official URL plus effective year in `source_ref`, and `editable=false`. Fixed demo
year selection is not itself a statutory rule. A financial year must be selected explicitly.

Events carry name, yearly probability, effect description and provenance. These are
simulation events, distinct from the SSE stream. Effects are interpreted by a tested
pack/model; never evaluate the effect text as code.

## Simulation boundary (Phase 1 implementation)

`simulate(option_id, params, rng, n)` returns `cash_in_hand` and `net_worth` as
`n × (12 * horizon_years)` month-end arrays, scalar metrics of length `n`, and path
event logs. Values are INR, not lakh. The fixed runner aggregates quarter endpoints
(month indices 2, 5, 8, ...) for the browser. Annual-only arrays in the original
specification cannot support its quarterly chart; this resolves that conflict.

For common random numbers, the runner must create named random streams for each
shared uncertainty and stable path IDs. Merely giving both options the same seed
is insufficient if their code consumes random draws in different orders. Never run
agent-written model or test code on the API server or in the Phase 0 fixture scripts.

## Results

`data_kind=mock` must remain visible in development. Only actual execution may use
`simulation`. Include pack, branch, horizon, path count, seed and objective.
`x_points` lists all quarter ends (`Q1-Y1` ...); no origin is included. Each option
contains ordered p5/p10/p25/p50/p75/p90/p95 arrays, up to 1,000 sampled paths,
aligned path stories and metric histograms. The UI may render an origin without
adding it to the stored arrays. `path_stories[i].id` identifies `sampled_paths[i]`.
Both options must use the same ordered sample IDs. Percentiles and win rates are
computed from all paths, not from the display sample.

`p_win.A`, `p_win.B`, and `p_win.tie` sum to one. Ties are not silently awarded to B.
Histograms use edges plus counts; each metric's counts sum to `path_count`.
`sensitivities` contains ranked tornado sweeps, separately from actual flip points.
A flip point includes the bracket, direction and winner on that side. No crossing
means no flip point; never fabricate a threshold. Non-monotone sweeps need a different
search or an explicit unsupported result before bisection is used.

The frontier is `grid[y_index][x_index]`, containing **P(A wins)** for both packs.
Its explicit axes strictly increase. `frontier=null` is valid before analysis or
when fewer than two suitable variables exist. The initial result may have empty
sensitivities/flip points; `flip.ready` announces an updated result to fetch.

Fine Print's primary metric remains out-of-pocket, excluding premiums, per the
project specification. Its `total_cost` metric adds premiums. Never describe a win
on out-of-pocket as a win on total cost. Users must see which metric is compared.

## REST contracts

Routes below are agreed interfaces, **not implemented endpoints yet**. Phase 0 only
implements `/health`. All route bodies/responses have named Pydantic models.

| Method and route | Request | Response / HTTP |
| --- | --- | --- |
| GET `/health` | none | `{status, phase, mode}` / 200 |
| POST `/sessions` | `CreateSessionRequest` | `CreateSessionResponse` / 201 |
| POST `/sessions/{id}/documents` | multipart `file` (PDF), `option_id` (A/B) | `UploadDocumentResponse` / 201 |
| PATCH `/sessions/{id}/terms` | `PatchTermsRequest` | `OkResponse` / 200 |
| GET `/sessions/{id}/interview/next` | none | `InterviewNextResponse` / 200 |
| POST `/sessions/{id}/interview/answer` | `InterviewAnswerRequest` | `OkResponse` / 200 |
| POST `/sessions/{id}/build` | none | `BuildResponse` / 202 |
| POST `/sessions/{id}/whatif` | `WhatIfRequest` | `WhatIfResponse` / 202, or 200 if out of scope |
| GET `/sessions/{id}/branches` | none | `BranchesResponse` / 200 |
| GET `/branches/{id}/results` | none | `Results` / 200; 409 if not ready |
| GET `/sessions/{id}/report` | required query `branch_id` | `ReportResponse` / 200 |
| GET `/sessions/{id}/events` | optional `replay=build`; header `Last-Event-ID` | SSE / 200 |

The uploaded PDF must be attributed to an option explicitly. Term values are flattened
scalar fields (nested policy clauses use dotted names). Evidence includes document ID,
one-based page, exact quote and backend-verified `matched`. The user can confirm low
confidence fields. No API key belongs in a request sent by the browser.

What-if requests identify `parent_branch_id`, avoiding the ambiguity of a mutable
"current branch". Reports likewise identify their branch. Query/body IDs must belong
to the requested session; Phase 1 must enforce ownership and idempotent build handling.
Expected error envelope: `ErrorResponse`. Use 400 unsupported request, 404 missing
resource, 409 state conflict, 413 oversize PDF, 415 unsupported media, 422 validation,
429 capacity, 502 provider failure. Phase 1 must normalize FastAPI validation errors.

## Branches and persistence

Branch contains its parent, spec snapshot, parameter diff, model/checkpoint IDs and
status. `change_type` is root, param or structural. `diff` describes scalar parameter
edits; structural changes use `change_summary` and a new model version. IDs may be
null while building. SQL rows may store `spec_json`; the wire field is `spec`.

Tables planned for Phase 1: sessions (journey/status), documents (terms), branches
(parent/spec), model_versions (code/tests/status/checkpoint), runs (kind/results),
llm_calls (tier/tokens/latency). Files and health details are session-scoped; deletion
must cover both app storage and retained remote images before claiming that privacy promise.

## SSE wire format

Each event is a discriminated model. Transport example:

```text
id: demo_offer_xray:1
event: agent.status
data: {"schema_version":"1.0.0","id":"demo_offer_xray:1","session_id":"demo_offer_xray","branch_id":"br_offer_xray_root","sequence":1,"elapsed_ms":0,"data_kind":"mock","event":"agent.status","data":{"status":"extracting","text":"MOCK replay"}}

```

The SSE `data` contains the entire envelope. `id` is unique per session; sequence
increases monotonically across branches. Reconnect resumes after `Last-Event-ID`;
clients deduplicate by ID. Heartbeats are comments, not contract events. The future
server must explicitly signal expired replay history rather than silently dropping events.
`elapsed_ms` is relative to session start. Replay delay is the difference between
successive offsets, not the entire offset each time. Mock JSONL uses the same envelope.

| Event | Payload |
| --- | --- |
| extract.done | document_id, terms (confidence and evidence per term) |
| agent.status | status, text |
| code.chunk | file, text, attempt, reset (replace panel before first chunk of a retry) |
| test.result | name, passed, message, attempt |
| sandbox.fork | fork_id, parent checkpoint, purpose, optional option_id |
| sim.progress | fork_id, done, total |
| results.ready | branch_id (fetch results; flip search may still be running) |
| flip.ready | branch_id (refetch updated results) |
| llm.call | tier, tokens_in, tokens_out, ms |
| error | where, message, recoverable |

Session states: created -> extracting -> interviewing -> building -> simulating ->
analyzing -> ready, with failed/cancelled exits. A what-if has its own branch progress;
the previous ready branch remains usable. No synthetic event is evidence of live execution.

## Other reconciliations

- Nano classifies what-ifs (routing table and task A6); Super handles interview wording
  and story templates. Code chooses required pack questions and validates specs.
- Maximum five interview questions for either launch pack; Open mode is beta.
- Python 3.12 is the tested baseline, matching the pinned SDK quickstart, replacing
  the specification's Python 3.11 starting suggestion.
- The displayed 64%, month 17 and similar examples are illustrative. Real outputs
  must be computed; fixtures explicitly identify their synthetic mechanism.
