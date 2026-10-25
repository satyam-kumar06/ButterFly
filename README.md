# Fork

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/satyam-kumar06/ButterFly/actions/workflows/ci.yml/badge.svg)](https://github.com/satyam-kumar06/ButterFly/actions/workflows/ci.yml)

**Fork your sandbox. Fork your life.**

Fork is a planned coding agent that turns a money decision into a tested simulation,
explores possible futures, and shows which assumptions change the outcome. Launch
packs: Offer X-ray (job offers) and Fine Print (health insurance). Open mode is beta scope.

**Current state: Phase 0 foundation.** Contracts, seeded mock data, fictional demo
PDFs, payroll references and CI are implemented. The browser is a fixture inspector;
the API exposes only `/health`. There is no live agent or financial simulation yet.
Nebius account access and live checks are pending; see [Phase 0 status](docs/phase-0-status.md).

## Run locally

Requirements: Python 3.12 and Node.js >=22.12 (Node 22 LTS tested). From the repo root:

```sh
python -m venv .venv
```

Activate on PowerShell with `.\.venv\Scripts\Activate.ps1` or on macOS/Linux with
`source .venv/bin/activate`. If execution policy blocks activation, use
`.\.venv\Scripts\python.exe` directly instead of changing machine policy.

```sh
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps -e .
npm ci
```

Copy `.env.example` to `.env` (`Copy-Item .env.example .env` on PowerShell, `cp` on
macOS/Linux). No API key is needed for mock mode. The file is ignored by Git.

```sh
python -m uvicorn apps.api.main:app --reload
# In a second terminal:
npm run dev
```

Open the frontend URL printed by Vite (normally http://127.0.0.1:5173).
API health: http://127.0.0.1:8000/health; API docs: http://127.0.0.1:8000/docs.
`VITE_MOCK=1` loads fixtures. Live mode is intentionally unavailable in Phase 0.

## Generate and check

```sh
python -m scripts.export_contracts
npm run contracts:types
python -m mocks.make_mocks
python -m scripts.make_demo_documents

python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m scripts.export_contracts --check
npm run contracts:check
python -m mocks.make_mocks --check
python -m scripts.make_demo_documents --check
npm run build
```

PDF regeneration is deterministic with the locked ReportLab version. Generated
schemas, TypeScript, mocks and four PDFs are committed. CI rejects stale artifacts.

## Phase 0 handoff

- [Shared contracts and decisions](docs/contracts.md)
- [Platform setup and remaining live checks](docs/platform-notes.md)
- [Synthetic fixture guide](mocks/README.md)
- [Hand-worked salary references](docs/demo-payroll.md)
- [Team workflow](CONTRIBUTING.md)
- [Nimbus offer](output/pdf/offer_nimbus.pdf), [Kestrel offer](output/pdf/offer_kestrel.pdf)
- [Harbor policy](output/pdf/policy_harbor.pdf), [Meadow policy](output/pdf/policy_meadow.pdf)

```text
apps/api/          Python contracts and health-only FastAPI app (Brain)
apps/web/          React/TypeScript fixture inspector (Face)
forklib/           Trusted primitives and legal rules, Phase 1 (Engine)
packs/             Offer X-ray and Fine Print pack implementation, Phase 1 (Engine)
sandbox_runtime/   Fixed runner/base image, Phase 1 (Engine)
mocks/             Specs, results, event recording, expected extraction/payroll/claims
scripts/           Generators and platform probes
docs/              Contracts, schemas, platform notes and handoff
output/pdf/        Four fictional source documents for the demo
```

## How Fork will use Nemotron, Token Factory and Sandboxes

Planned routing: Nano extracts terms and classifies what-ifs; Super phrases interview
questions and result stories; Ultra writes and repairs simulation code/tests. All
provider calls will happen on the backend. The Phase 0 probe checks configured model
IDs against the account catalog before a hello call. It does not implement A2's client.

The planned sandbox flow saves a base filesystem, writes a decision spec, tests a
generated model in an isolated branch, then starts simulation shards from the tested
checkpoint. A failed attempt is abandoned. Parameter what-ifs reuse the tested model;
structural changes require another test cycle. Checkpoints preserve filesystem state,
not live processes. Actual interfaces and unresolved network/deletion controls are in
[platform notes](docs/platform-notes.md).

```text
base -> session -> tested model
                  |-- A shards 0..3
                  |-- B shards 0..3
                  |-- sensitivity / threshold / frontier runs
                  `-- what-if -> tested child model when required
```

## Accuracy and privacy

Mock outputs are labeled synthetic. Their random walks are not predictions, and
their win rates are not financial claims. The independent payroll/claim references
seed future golden tests. Source each legal rule with its effective year before
production use. Every reported number must come from computed results.

Do not upload real offer letters or health information to this public repository.
The future app needs verified session deletion, including remote checkpoint retention,
before promising it. Fork is a decision aid, not financial, tax or insurance advice.
