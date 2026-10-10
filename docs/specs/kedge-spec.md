# Spec: Kedge

> Kedging: a crew throws a small anchor ahead of a drifting ship, then hauls the ship back on course.
> Kedge does the same for an unattended coding agent: when the agent drifts, Kedge pulls it back to the last good state and retries.

Status: DRAFT, 2026-10-10. Source design: `docs/designs/driftguard.md` (renamed to Kedge).
Event: neatHack. Build window Oct 10 12:30 PM IST to Oct 12 11:55 PM IST. Team of 2. Budget $0, so the plan depends on Bedrock credits.

## Context

Coding agents left to run alone fail silently. They delete a failing test, edit unrelated files, loop, or overspend, and still report success. Kedge is a supervisor that runs headless Claude Code on one bounded task: turning a failing Dependabot/Renovate PR green. After every step it checks for drift, rolls back to the last good commit when it finds any, and retries with a recovery note. It opens a draft PR only after the tests pass.

Judging weights it targets: agent 30%, use of neatlogs/Entire/cfo.ai 25%, demo 20%, building in public 15%, originality 10%.

## Current State (verified 2026-10-10)

- Greenfield. No Kedge code exists. The repo is created at kickoff, because commits must be dated inside the build window.
- Host tools: `gh` installed, `claude` installed, `python3` and `uv` installed. **Not installed: `docker`, `entire`, `opencode`.**
- **Docker is dropped.** Each run gets a fresh clone under `$TMPDIR/kedge/<run_id>` (`gh repo clone` + `gh pr checkout`). Tests run on the host, so only allowlisted target repos may be used (see `targets.json`).
- What the docs confirmed:
  - **Entire.** Captures Claude Code through `.claude/settings.json` hooks. Checkpoints are git refs `refs/entire/checkpoints/...`, and each commit gets an `Entire-Checkpoint: <id>` trailer. Commands: `entire checkpoint list|explain|search|tokens`. There is no rewind command. [github.com/entireio/cli]
  - **neatlogs.** Python SDK (`pip install neatlogs`, `neatlogs.init()`) with auto-instrumentation, decorators, tags, custom attributes and span kinds. Public API at `https://app.neatlogs.com/api/v1/public` (Bearer token plus `x-project-id`). [docs.neatlogs.com/sdk, /api-reference]
- **Not yet known (Day-1 spikes):**
  - exact neatlogs Python function names for custom spans and attributes
  - whether Entire hooks fire for `claude -p` (headless mode)
  - the neatlogs free-tier limits

## Proposed Change

### CLI

```
kedge run <pr-url> [--chaos] [--no-guard] [--budget 0.50] [--max-rollbacks 3] [--max-steps 6]
kedge batch targets.json [--chaos] [--no-guard]
kedge report <run_id>            # re-render report.html + report.md
```

Exit codes: `0` = PR green and draft PR opened. `1` = gave up and wrote a report. `2` = setup error (bad URL, missing tool, auth).

### Run flow

```
fetch PR (gh) ─> worktree on PR head ─> entire enable ─> baseline tests
   └─> plan (cheap LLM call: hypothesis + allowed_files)
        └─> loop step 1..max_steps:
              worker = claude -p (one step, recovery notes appended)
              [--chaos: after step 1, delete one test file]
              run tests ─> checks ─> drift?
                 no  ─> commit, good_sha = HEAD
                        tests green? ─> push + draft PR ─> exit 0
                 yes ─> git reset --hard good_sha; git clean -fd
                        add recovery note; rollbacks += 1
                        rollbacks > max ─> give-up report ─> exit 1
              cost > budget ─> give-up report ─> exit 1
```

### Drift checks (`kedge/checks.py`)

All checks are deterministic. No LLM is involved.

| Check | Trigger | Recovery note added to the worker prompt |
|---|---|---|
| `tests_regressed` | `tests_passed < best_passed` or `tests_total < baseline_total` | "Previous attempt reduced passing/total tests. Do not delete or skip tests." |
| `out_of_plan` | a changed file matches no glob in `plan.allowed_files` | "Only edit: {allowed_files}. You edited {files}." |
| `over_budget` | `cost_usd_total > budget` | none. Kedge gives up |
| `loop` | the diff hash equals any earlier rolled-back diff hash | "You repeated a failed attempt. Try a different approach." |

`--no-guard` disables `tests_regressed`, `out_of_plan` and `loop`. It exists for the "before" run. `over_budget` always stays on, because credits are the only budget.

### Data shapes

`runs/<run_id>/steps.jsonl`, one line per step:

```json
{"run_id":"20261010-1432-ab12","step":2,"action":"worker","files_changed":["requirements.txt","src/x.py"],
 "tests_passed":41,"tests_total":42,"cost_usd":0.07,"cost_usd_total":0.12,
 "drift":null,"rolled_back":false,"checkpoint_sha":"9f3c1e2","entire_checkpoint":"a1b2c3"}
```

`drift` is `null` or one of `"tests_regressed"`, `"out_of_plan"`, `"over_budget"`, `"loop"`.

`runs/<run_id>/plan.json`:

```json
{"hypothesis":"lodash 5 removed _.pluck; replace with _.map","allowed_files":["package.json","package-lock.json","src/**/*.js"]}
```

`targets.json`. Only the repos listed here may be run, because tests execute on the host:

```json
[{"pr_url":"https://github.com/<owner>/<repo>/pull/<n>","test_cmd":"pytest -q","fork":"<you>/<repo>"}]
```

Test result parsing: the test command's exit code is the pass/fail signal, and `tests_passed`/`tests_total` are parsed from the last summary line using a per-runner regex:
- pytest: `(\d+) passed`, `(\d+) failed`
- jest/vitest: `Tests:\s+(?:(\d+) failed, )?(\d+) passed, (\d+) total`

If the summary can't be parsed, both counts are `-1` and `tests_regressed` is skipped for that step.

### Worker call

```
claude -p "<prompt>" --output-format json --permission-mode acceptEdits --max-turns 15
```

- Runs with `cwd = worktree`.
- `total_cost_usd` is read from the JSON output.
- On Bedrock, set `CLAUDE_CODE_USE_BEDROCK=1`.
- The prompt contains the PR title, the failing CI log tail (`gh run view <id> --log-failed`, last 200 lines), `plan.json`, the recovery notes, and "Do ONE step toward making tests pass, then stop."
- Everything goes through a single function, `run_edit_step(prompt, cwd) -> {cost_usd, text}`. The OpenCode fallback replaces only that function.

### Observability (`kedge/trace.py`)

- Call `neatlogs.init()` once per run, tagged `run_id`, `pr_url`, `guard=on|off` and `chaos=on|off`.
- Create one span per step (kind `agent` for the supervisor, `tool` for the worker, tests and git), with every `steps.jsonl` field as an attribute.
- When the run ends, fetch the trace URL and totals through the public API for the report.
- If the API call fails, still write the report and put `trace: unavailable` in its place.

### Report (`kedge/report.py`)

- Both `report.html` and `report.md` are rendered from `steps.jsonl` with stdlib `string.Template`. No dependency is added.
- Contents:
  - one timeline row per step: step, action, files, tests, cost, drift, rolled back
  - totals
  - the neatlogs trace link
  - `entire checkpoint explain <id>` output for the final commit
- `report.md` becomes the body of the draft PR.

## Acceptance Criteria

1. `kedge run <url>` on an allowlisted PR creates `runs/<run_id>/steps.jsonl` with at least 1 line, and either opens a draft PR on the fork (exit 0) or writes a give-up report (exit 1).
2. With `--chaos`, a deleted test file is detected as `tests_regressed` in the same step, rolled back, and the next step does not repeat it. The neatlogs trace shows the drift attribute.
3. With `--chaos --no-guard`, the run opens a PR whose `tests_total` is lower than the baseline. This is the "before" evidence.
4. `out_of_plan` fires when a changed file matches no `allowed_files` glob. Covered by a unit test.
5. `loop` fires when a diff hash repeats. Covered by a unit test.
6. A run stops at `cost_usd_total > budget` and never makes another worker call after that.
7. Every agent commit carries an `Entire-Checkpoint:` trailer. If Entire hooks don't fire for `claude -p`, record that, and capture the checkpoints from the build sessions instead.
8. `kedge batch targets.json` over 10 PRs writes one summary line per PR plus totals (green count, drifts caught, mean $/green PR).
9. `report.html` opens offline and shows every step, and `report.md` is posted as the PR body.
10. `pytest` passes for `checks.py` and the test-summary parser (at least 8 tests).

## Testing Plan

| Layer | What | Count |
|---|---|---|
| Unit | the four drift checks with fixture step records; pytest and jest summary parsing including the unparseable case | +8 |
| Integration | a local fixture repo (tiny Python package with 3 tests and a broken import) runs a full loop with `run_edit_step` stubbed; chaos deletes a test and the run rolls back | +2 |
| E2E | 1 real allowlisted PR with the real worker, guard on, and the same PR with `--chaos --no-guard` | +2 manual |

## Rollback Plan

- Kedge only writes inside its own worktree and pushes only to the user's fork as a **draft** PR.
- To undo: close the draft PR, `git push <fork> --delete kedge/<run_id>`, `git worktree remove`.

## Effort Estimate (about 30 build hours per person)

**Person A, core (about 21h):**
- `git_ops` + `gh_ops`: 3h
- worker adapter: 2h
- supervisor loop: 5h
- checks + parser: 3h
- PR creation: 1h
- batch: 2h
- hardening on real PRs: 5h

**Person B, evidence (about 23h):**
- neatlogs spike + `trace.py`: 4h
- chaos: 1h
- report: 3h
- `targets.json` curation (10 PRs): 3h
- before/after runs: 2h
- cfo.ai plan: 3h
- X posts: 2h
- demo video: 5h

## Files Reference (new repo `kedge/`)

| File | Owner | Purpose |
|---|---|---|
| `pyproject.toml` | A | `uv` project, console script `kedge = kedge.cli:main`, deps `neatlogs` only. `make_plan` also goes through `claude -p --model haiku`, so there is a single auth path |
| `kedge/cli.py` | A | argparse: `run`, `batch`, `report` |
| `kedge/supervisor.py` | A | the run loop shown above |
| `kedge/worker.py` | A | `run_edit_step()`, `make_plan()` |
| `kedge/gitgh.py` | A | worktree, commit, reset, diff hash, push, draft PR, CI log |
| `kedge/checks.py` | A | the drift checks and the test-summary parser |
| `kedge/trace.py` | B | neatlogs init, spans, post-run fetch |
| `kedge/chaos.py` | B | delete one test file |
| `kedge/report.py` | B | HTML and Markdown rendering |
| `targets.json` | B | 10 allowlisted PRs |
| `tests/test_checks.py` | A | unit tests |
| `tests/test_loop.py` | A | integration test with the stub worker |
| `tests/fixtures/tinyrepo/` | A | fixture repo |
| `docs/business-plan.pdf` | B | cfo.ai export |

## Out of Scope

- Docker or sandboxing beyond the allowlist.
- A web UI or dashboard.
- Calling neatlogs Detections during a run (stretch goal).
- An LLM-judge drift check (stretch goal).
- Non-dependency issues, and PRs upstream (draft PRs go to the fork only).
- Dodo Payments integration (it only appears in the cfo.ai pricing story).

## Open Questions (owner, deadline)

1. Do Entire hooks fire for `claude -p`? **A**, Day 1 by 2 PM IST.
2. What are the exact neatlogs span and attribute APIs? **B**, Day 1 by 2 PM IST.
3. Did we get Bedrock credits? **both**, at check-in. If not, use the OpenCode fallback and ask on Discord.
