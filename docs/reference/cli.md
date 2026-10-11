# CLI reference

`kedge` is the command-line entry point (`kedge/cli.py`, installed as a script by `pyproject.toml`). Run it from the repository root with `uv run kedge ...` or `uv run python -m kedge ...`. It reads `.env` and `targets.json` from the current directory and writes everything it produces to `runs/`.

## Commands

| Command | What it does | Exit code |
|---|---|---|
| `kedge run <pr_url>` | Supervise one failing PR end to end. | `0` if the run ends `green` or `already_green`, `1` otherwise, `2` on bad input |
| `kedge batch <targets.json>` | Run every target in the file, one after another, then print a summary line. | `0` (a failing target never stops the batch) |
| `kedge resume <run_id>` | Continue a run that crashed or was killed, from its saved state. | Same as `run`; `2` if `runs/<run_id>/state.json` is missing |
| `kedge ui [--port N]` | Serve the run dashboard on `http://127.0.0.1:N` (default `8711`). | Runs until Ctrl+C |

### `kedge run`

```bash
uv run kedge run https://github.com/faroukobayanju/kedge-demo/pull/1 --storm delete-test
```

- `<pr_url>` must match `https://github.com/<owner>/<repo>/pull/<n>`. Anything else exits `2` with `error: expected https://github.com/<owner>/<repo>/pull/<n>`.
- The PR must be listed in `targets.json` (an allowlist). Otherwise: `error: PR not in targets.json allowlist`, exit `2`.

### `kedge batch`

```bash
uv run kedge batch targets.json
```

Prints one JSON line per target as it finishes:

```json
{"pr_url": "...", "status": "green", "cost_usd_total": 0.0, "rollbacks": 0, "draft_pr": "https://github.com/...", "minutes": 6.27}
```

Then one summary line:

```json
{"green": 1, "total": 3, "drifts_caught": 0, "false_claims": 0, "usd_total": 0.0, "usd_per_green": 0.0,
 "tokens_total": 37996, "tokens_per_green": 37996, "mean_steps": 3.67, "mean_minutes": 23.96}
```

| Field | Meaning |
|---|---|
| `green` / `total` | Runs that ended `green` / runs attempted |
| `drifts_caught` | Steps with any drift except `over_budget` |
| `false_claims` | Steps where the agent claimed success that the tests did not back up |
| `usd_total`, `usd_per_green` | Model spend reported by the agent CLI |
| `tokens_total`, `tokens_per_green` | Input + output + reasoning tokens over all steps |
| `mean_steps` | Agent steps per run (replans not counted) |
| `mean_minutes` | Wall-clock minutes per run |

A target that raises (clone failure, a test command that times out after 600 s) is recorded as `status: "error: <message>"` and the batch moves on.

### `kedge resume`

```bash
uv run kedge resume 20261010-2211-58eb
```

Reloads `meta.json` and `state.json`, hard-resets the clone to the last good commit (throwing away the half-finished step), and continues the loop with the original `--no-guard` / `--storm` / budget settings.

### `kedge ui`

```bash
uv run kedge ui --port 8711
```

Serves `kedge/ui/` and a read-only JSON view of `runs/`. See [dashboard.md](dashboard.md).

## Options (`run` and `batch`)

| Flag | Type | Default | Effect |
|---|---|---|---|
| `--storm {delete-test,skip-test,stray-edit}` | choice | off | After the agent's **first** step, sabotage the work tree on purpose (see [Storms](#storms)). Used to prove the guard works. |
| `--no-guard` | flag | guard on | Turn off every drift check except the budget. This is the "before" run. |
| `--budget` | float, USD | `0.50` | Stop with `over_budget` once model spend passes this. |
| `--max-rollbacks` | int | `3` | Give up after more rollbacks than this. |
| `--max-steps` | int | `6` | Give up after this many agent steps. |

## Storms

`kedge/chaos.py`. A storm runs once, right after the agent's first step and before the tests.

| Mode | What it does |
|---|---|
| `delete-test` | Deletes the first test file found (`test_*.py`, `*_test.py`, `*.test.js`, `*.test.ts`, `*.spec.js`, `*.spec.ts`), skipping `node_modules` and `.git`. |
| `skip-test` | Prepends `pytestmark = pytest.mark.skip` to the first `test_*.py`. |
| `stray-edit` | Writes `STORM.md` at the repo root (a file outside any plan). |

## `targets.json`

The allowlist of PRs Kedge may touch. An array of objects:

| Key | Required | Meaning |
|---|---|---|
| `pr_url` | yes | The failing PR |
| `test_cmd` | yes | Shell command that installs dependencies and runs the tests, run in the clone. Install steps belong here so every run sees the agent's dependency change. Times out after 600 s. |
| `fork` | yes | `owner/repo` that Kedge pushes its branch to and opens the draft PR on |
| `setup_cmd` | no | One-time setup run once after cloning |

```json
{
  "pr_url": "https://github.com/faroukobayanju/kedge-demo/pull/1",
  "test_cmd": "uv run --no-project --with-requirements requirements.txt --with pytest python -m pytest -q -p no:cacheprovider",
  "fork": "faroukobayanju/kedge-demo"
}
```

Test counts come from the test command's output (`kedge/checks.py:parse_summary`): Jest's `Tests: N passed, M total`, pytest's `N passed, M failed, K errors`, and pytest's `no tests ran` (counted as 0/0). Output Kedge can't parse counts as unknown (`-1`), and count-based checks skip it.

## Environment

Set in the shell or in `.env` (copy `.env.example`). Real environment variables win over `.env`.

| Variable | Used by | Meaning |
|---|---|---|
| `NEATLOGS_API_KEY` | `kedge/trace.py` | Ingest key. Without it, tracing is off and runs still work. |
| `NEATLOGS_TOKEN` | neatlogs CLI | Service-account token for reading traces back. Never mixed with the ingest key. |
| `NEATLOGS_PROJECT_ID` | neatlogs CLI | Project UUID for trace readback |
| `NEATLOGS_CLI` | `kedge/trace.py` | Path to the npm neatlogs CLI (default `~/.local/bin/neatlogs`). The Python SDK installs a different `neatlogs` script into the venv, so the path is explicit. |
| `NEATLOGS_HOST` | `kedge/trace.py` | Dashboard origin (default `https://app.neatlogs.com`) |
| `NEATLOGS_PROFILE` | `kedge/trace.py` | CLI profile name (default `setup-https---app-neatlogs-com`) |
| `KEDGE_WORKER` | `kedge/worker.py`, `kedge/cli.py` | `claude` switches the agent to headless Claude Code. Default: OpenCode. |
| `KEDGE_MODEL` | `kedge/worker.py` | OpenCode model (default `opencode/big-pickle`, a free model) |

Kedge also puts the pinned OpenCode v1 from `.tools/opencode` first on `PATH` and gives it its own `XDG_DATA_HOME`, `XDG_STATE_HOME` and `XDG_CACHE_HOME` (see [integrations.md](integrations.md#entire)).

## External tools

| Tool | Why |
|---|---|
| `gh` (logged in) | Read the PR, clone, check out, read failed CI logs, push to the fork, open the draft PR, watch CI |
| `git` | Commits, rollbacks, worktrees for the base-branch test count |
| `entire` (0.11.4, on `PATH`, usually `~/.local/bin`) | Checkpoints and Trails |
| OpenCode 1.18.35 (`./scripts/setup-opencode.sh`) | The default agent |
| `claude` (optional) | Headless Claude Code when `KEDGE_WORKER=claude` |
| neatlogs npm CLI (optional) | Trace readback after a run |

## The ship's log

While a run works, Kedge prints one line per step to stderr (`kedge/shiplog.py`):

```text
⚓ kedge  dependabot/pip/packaging-24.2  ·  budget $0.50
🧪 base branch has 5 tests
🌊 DRIFT  out_of_plan · tests 2/2 · tests/test_sorting.py, versions.py
⚓ hauled back to 33a6358
⛵ step 2  edited 1 files · tests 5/5
🏁 green · $0.00 · https://github.com/faroukobayanju/kedge-demo/pull/10 · trace d8a89d17c4f7d4a9898583e2d8d75f7f
```

| Mark | Meaning |
|---|---|
| `⛵` | A clean step |
| `🌊 DRIFT` + `⚓ hauled back` | Drift caught and rolled back to the named commit |
| `⛈` | The agent call itself failed (timeout or unreadable output) |
| `🧭` | Replanning after two rollbacks in a row |
| `💸` | Out of budget |
| `🤥` | The agent claimed success that the tests contradict |
| `🏁` | Final status, cost, draft PR, trace ID |

## Related

- [Drift checks](drift-checks.md): every check and its recovery note
- [Run files](run-files.md): what lands in `runs/<id>/`
- [How Kedge works](../explanation/how-kedge-works.md)
