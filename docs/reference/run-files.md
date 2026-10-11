# Run files

Every run gets a folder `runs/<run_id>/`. The run ID is `YYYYMMDD-HHMM-xxxx` (local time plus 4 random hex characters). `runs/` is git-ignored: it can hold local paths and failure logs.

The clone itself lives at `$TMPDIR/kedge/<run_id>`. The base-branch worktree goes at `$TMPDIR/kedge/<run_id>-base` and is removed after counting.

| File | Written | Contents |
|---|---|---|
| `plan.json` | Before step 1 | `hypothesis`, `allowed_files` (globs), `steps` (1 to 4), `cost_usd` |
| `meta.json` | Before step 1 | `pr_url`, `test_cmd`, `fork`, `cwd`, `pr` (`title`, `base`, `head`, `repo`), `log_tail` (failure output given to the planner), `base_total`, `kw` (guard, storm, budget, max_rollbacks, max_steps) |
| `state.json` | After every step | Everything `resume` needs: `step`, `good` (last good SHA), `notes`, `seen` (rolled-back diff hashes), `cost`, `best`, `baseline_total`, `base_total`, `plan`, `plan_idx`, `steps` |
| `steps.jsonl` | One line per step | The step record (below). Also sent to neatlogs as span attributes. |
| `report.md`, `report.html` | At the end | Step table, voyage chart, Entire checkpoint explanation. `report.md` becomes the draft PR body. |
| `result.json` | At the end | `run_id`, `pr_url`, `status`, `cost_usd_total`, `rollbacks`, `trace_url` (a neatlogs trace ID or `unavailable`), `entire_explain`, `draft_pr`, `trail`, `guard`, `storm`, `finished_at` |

Shared files:

| File | Contents |
|---|---|
| `runs/lessons.jsonl` | `{"repo", "note"}` lines. A recovery note becomes a lesson only when its run rolled back **and** still went green. The last 3 lessons go into every new prompt as `LESSON FROM PAST RUNS`. They are not filtered by repo. |

## Step record (`steps.jsonl`)

| Field | Type | Meaning |
|---|---|---|
| `run_id` | str | |
| `step` | int | Step number (a replan reuses the current number) |
| `action` | str | `worker`, `worker_error` (the agent call failed) or `replan` |
| `files_changed` | list[str] | Files changed in the work tree after the step |
| `tests_passed`, `tests_total` | int | `-1` when the output couldn't be parsed |
| `cost_usd`, `cost_usd_total` | float | This step / the run so far |
| `tokens` | int | Tokens the agent CLI reported for this step |
| `drift` | str or null | See [drift-checks.md](drift-checks.md) |
| `rolled_back` | bool | |
| `checkpoint_sha` | str | Last good commit after this step |
| `entire_checkpoint` | str | Entire checkpoint ID from the commit's `Entire-Checkpoint:` trailer, or `""` |
| `plan_step` | int | Index of the plan step being worked on |
| `false_claim` | bool | |
| `claim` | str | The success phrase the agent used, or `""` |

Real example (run `20261010-2322-da07`, step 2):

```json
{"run_id": "20261010-2322-da07", "step": 2, "action": "worker", "files_changed": ["versions.py"],
 "tests_passed": 0, "tests_total": 5, "cost_usd": 0.0, "cost_usd_total": 0.0, "tokens": 23490,
 "drift": null, "rolled_back": false, "checkpoint_sha": "6b43429…", "entire_checkpoint": "01M4KYMP3EJ6E6ZFMVZZC85C11",
 "plan_step": 0, "false_claim": false, "claim": ""}
```

## Statuses

| `status` | Meaning |
|---|---|
| `green` | Tests pass (twice, with the guard on). A branch is pushed and a draft PR or trail is opened. |
| `already_green` | Tests already passed before any step. Nothing to do. |
| `gave_up` | Out of steps, too many rollbacks, or over budget. Nothing is pushed. |
| `error: …` | (batch only) The run raised before finishing |

## Related

- [Dashboard and API](dashboard.md): reads these files
- [CLI reference](cli.md)
