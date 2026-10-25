# Working together

Brain owns `apps/api` except the sandbox adapter; Engine owns `forklib`, `packs`,
`sandbox_runtime` and the sandbox adapter; Face owns `apps/web` and visual demo assets.
All three share `docs/contracts.md`, generated schemas/types, and `mocks`.
Assign real GitHub usernames before adding CODEOWNERS; no fictional reviewer accounts.

Use `a/...`, `b/...`, `c/...` branches for team work and `codex/...` for assistant work.
Open a PR into `main`, wait for **Python checks** and **Frontend build**, and obtain
one approval from another team member. Do not push directly to main. The repo's
branch protection requires these checks, up-to-date branches, resolved conversations
and one review; an updated commit dismisses stale approvals.

When changing a contract, notify the other two owners in the team's existing channel
and update Pydantic, schema, TypeScript, docs and mocks in the same PR. CI cannot
replace that agreement. Keep secret values in local `.env` or backend hosting secrets.
Never put them in `VITE_` variables. Use only fictional documents in this public repo.

Run the commands in README before requesting review. A test of a future simulation
must check known answers or invariants, not compare an implementation against itself.
Never execute runtime LLM-written simulation code or tests outside Nebius Sandboxes.
