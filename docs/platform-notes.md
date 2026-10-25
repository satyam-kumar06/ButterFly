# Platform notes

Checked 2026-10-25 (Asia/Kolkata). **Account activation and live probes are pending.**
The owner confirmed platform access has not yet been obtained. No live inference,
sandbox hello, speed or quota test has passed. Documentation review and local SDK
installation are not substitutes for those checks.

## Access steps

1. Each builder should join the team's Nebius project with their own account. Obtain
   hackathon credits/access using the organizer's actual instructions.
2. Create a key at [Token Factory API keys](https://tokenfactory.nebius.com/).
   See [authentication instructions](https://docs.tokenfactory.nebius.com/api-reference/introduction).
3. Request [Sandboxes beta access](https://tokenfactory.nebius.com/sandboxes/about)
   for the project. Copy its project ID from Project settings. An accepted token
   does not by itself prove sandbox permission.
4. Copy `.env.example` to `.env` and populate `TOKEN_FACTORY_API_KEY`,
   `SANDBOX_API_KEY`, and `NEBIUS_PROJECT_ID`. The sandbox key may be the same
   project key if its permissions allow both services; do not assume activation.
5. Run configuration checks, then the explicitly metered live checks:

```sh
python -m scripts.check_platform
python -m scripts.check_platform --live --service token_factory
python -m scripts.check_platform --live --service sandboxes
```

Exit 2 means missing configuration or a failed check, never success. The report at
`docs/platform-check.local.json` is ignored. Copy only sanitized observations here
after testing. The script logs neither keys nor provider response bodies.

## Token Factory

The [official API introduction](https://docs.tokenfactory.nebius.com/api-reference/introduction)
documents OpenAI-compatible chat completions at `https://api.tokenfactory.nebius.com/v1/`
with bearer authentication. The probe first lists `/models`, then makes one short
chat request per configured tier. Listing a model alone does not test inference.

Candidate catalog IDs, case-sensitive, from the
[official Nemotron catalog](https://nebius.com/services/token-factory/models/nvidia-nemotron-models-inference)
and [Nemotron integration example](https://nebius.com/services/token-factory/nemotron):

| Tier | Candidate model ID | Actual account availability |
| --- | --- | --- |
| Nano | `nvidia/Nemotron-3-Nano-30B-A3B` | Unverified |
| Super | `nvidia/nemotron-3-super-120b-a12b` | Unverified |
| Ultra | `nvidia/Nemotron-3-Ultra-550b-a55b` | Unverified |

The unauthenticated catalog request was rejected. Exact IDs must be confirmed by
the authenticated probe; no silent substitution or fabricated successful call.
The future client also needs streaming, structured output and retry tests (A2).

## Sandboxes / Contree

Pinned `contree-sdk==0.3.6`, installed and inspected locally with Python 3.12.
Use the [versioned Python quickstart](https://docs.tokenfactory.nebius.com/sandboxes/start/python-quickstart),
not GitHub main's newer API examples. Constructor `Contree(config=ContreeConfig(...))`
accepts `IAMAuth(token, project_id, base_url)`. `images.use(..., strict=True)` selects
an available image; `await image.run(..., disposable=False)` saves filesystem state.
Check both exit code and returned image UUID before reuse. `disposable=True` returns
output without a reusable child filesystem. The probe writes a constant hello file,
saves it, then reads it from two independent disposable operations. It retains one
small checkpoint; no packages, arbitrary model code or capacity stress tests run.

[Access documentation](https://docs.tokenfactory.nebius.com/sandboxes/start/set-up-access)
distinguishes Python's `NEBIUS_PROJECT_ID` from CLI registration's `NEBIUS_AI_PROJECT`.
The project script passes configuration explicitly to avoid this mismatch.

[Image semantics](https://docs.tokenfactory.nebius.com/sandboxes/concepts/images-checkpoints-and-branches):
checkpoints preserve files, not live processes or memory. A branch is an independent
operation from the same immutable image. The proposed `SandboxManager` is our own
Phase 1 abstraction; `fork`, `checkpoint` and `discard` are not assumed SDK methods.

## Initial limits and measurements

[Published limits](https://docs.tokenfactory.nebius.com/sandboxes/operate/limits-retention-and-usage)
describe 50 simultaneous operations during beta, 180-day checkpoint retention, and
networking enabled by default. Actual account limits come from `/v1/whoami` with
Authorization and Project headers. Treat published values as planning information.

| Item | Current evidence | Next check |
| --- | --- | --- |
| SDK imports | 0.3.6 installed locally | Live authenticated hello |
| Model IDs and API | Documentation only | Catalog plus three inference calls |
| Sandbox access | Not yet obtained | Activation, whoami, hello |
| Parallel forks | Not measured | Two-branch probe, then B1 capacity measurements |
| Fork/startup latency | Not measured | Record measured durations |
| NumPy/SciPy base | Not prepared | B1 saved image with dependencies |
| Runtime limits | Unknown account values | Save sanitized whoami limits |
| Guest networking off | Not tested | SDK 0.3.6 run signature lacks a networking argument; verify supported API before generated code |
| File upload/download | Not tested | B1 round-trip JSON artifact |
| Deletion/retention | Not verified | Confirm remote cleanup before promising session deletion |

The application-side default concurrency is conservatively four until measured.
Timeouts must not blindly resubmit an operation that may already be running. Preserve
accepted operation IDs and inspect before retry. This issue belongs in platform feedback.
