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

## Demo
Pending.

## Known limitations and next steps
- The Entire capture for headless agent sessions isn't working yet (see above).
- Next: Task 1 (drift checks), Task 5 spike (neatlogs API).

## Submission
- Submit on X by quoting the official neatlogs post, Mon Oct 12, 7:00–11:55 PM IST. Include the team, name, project, public repo and demo.
- Outstanding: everything.
