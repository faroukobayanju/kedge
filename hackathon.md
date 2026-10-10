# neatHack build log: Kedge

## Project
**Kedge** is a supervisor that pulls unattended coding agents back on course. It turns failing dependency-bump PRs green, catches silent drift (deleted or skipped tests, edits outside the plan, loops, budget overruns, false success claims), rolls back to the last good commit, and retries.

The problem: coding agents left alone fail silently and report success anyway.

## Team
Pending: the builders choose which names and handles to publish.

## Stack
- Python 3.12, `uv`, `gh` CLI
- Worker agent: OpenCode (free models), with Claude Code as an alternative. Being decided; see the build log.
- neatlogs: one span per supervisor step, readback through the CLI
- Entire: checkpoints on agent commits
- cfo.ai: business plan (pending)

## Build log

### 2026-10-10
- **Done (before kickoff, tools only, no project code):**
  - Installed Entire CLI 0.11.4. `entire enable --agent claude-code` installs 9 hooks non-interactively.
  - Headless `claude -p` failed with `Invalid API key · Please run /login`, because the standalone CLI isn't logged in on the builder's machine.
  - Installed OpenCode 2.0.25. It lists 11 free models (for example `opencode/big-pickle`).
  - `opencode run --auto --format json -m opencode/big-pickle "<prompt>"` made the edit in about 10 s. The JSONL output includes `step_finish` events with `cost: 0` and token counts, plus a final `text` event.
- **Open finding:** with `entire enable --agent opencode`, a headless `opencode run` plus a manual commit produced **0 Entire checkpoints** (`entire session list` reports "No sessions."), even with `entire` on PATH and the OpenCode service restarted. `opencode run --standalone` hung with no output. Still under investigation.
- **Done (after kickoff, 4:35 PM IST):** created the repo with a `uv` scaffold (flat `kedge/` package, `neatlogs` dependency, `pytest`), plus the design, spec and plan docs, this log, and the neatHack skill.

- **Done (Sat evening):** Tasks 1, 2, 3, 4 and 6 are committed. `uv run pytest` gives **31 passed**.
  - **Task 1:** drift checks and the test-summary parser. pytest output with only collection errors is now counted (`2 errors` → 0/2), which a broken import produces.
  - **Task 2:** git and gh operations.
  - **Task 3:** the worker adapter now defaults to **OpenCode**: `opencode run --format json --auto` for edits, `--agent plan` for read-only planning. Claude Code is available with `KEDGE_WORKER=claude`. Two real calls worked at $0: the edit created the file, and the plan narrowed `allowed_files` to `src/util.js` for a lodash `_.pluck` failure.
  - **Task 4:** the supervisor loop. Rollback on drift and the recovery notes are verified on a fixture repo with a stub worker. The chaos run is caught as `tests_regressed` and recovers to green, and without the guard it ships with fewer tests.
  - **Task 6:** the chaos injector, done early to unblock Task 4.
- **Not yet done:** a real end-to-end run on a GitHub PR (needs `targets.json` and the CLI from Task 8).

- **Fixed: Entire capture of headless agent runs.** Root cause, from OpenCode's log: OpenCode **v2** rejects Entire's generated plugin with `failed to load plugin … Plugin must export a default definition with an id and an effect or setup function`, so Entire never sees the session. Fix: pin **OpenCode v1.18.35** (`scripts/setup-opencode.sh`, which installs into `.tools/`). Entire's commit hook runs `opencode export`, so v1 must come first on PATH, with its own XDG data dirs. Kedge's CLI now sets this up (`worker.use_pinned_opencode`). Verified in a scratch repo: a headless `opencode run` plus `git commit` produced the trailer `Entire-Checkpoint: 01M4JS2RDRFJW0SDNYSZYK0Z8H`, and `entire checkpoint explain HEAD` shows the intent, the write tool call, the file and 44.4k tokens. 37 tests pass.

## Demo
Pending.

## Known limitations and next steps
- Requires `entire` on PATH (`~/.local/bin`) and `./scripts/setup-opencode.sh` run once.
- Next: first real run on a GitHub PR (needs `targets.json`, Task 9), the Task 5 neatlogs spike, and Tasks 11–18.

## Submission
- Submit on X by quoting the official neatlogs post, Mon Oct 12, 7:00–11:55 PM IST. Include the team, name, project, public repo and demo.
- Outstanding: everything.
