# Integrations: neatlogs, Entire, cfo.ai

What each tool receives from Kedge, and where it lives in the code. For why we used them the way we did, see [How we used neatlogs, Entire and cfo.ai](../explanation/tools.md).

![Where the tools plug in](../diagrams/tools-map.png)

## neatlogs

Code: `kedge/trace.py`. SDK: `neatlogs>=1.4.26` (Python). Readback: the neatlogs npm CLI (0.2.1).

**Setup.** `trace.start()` calls `neatlogs.init(api_key=NEATLOGS_API_KEY, endpoint="https://ingest.neatlogs.com", workflow_name="dependency-pr-repair", tags=[...])`. With no `NEATLOGS_API_KEY`, every trace call is a no-op.

**One trace per run.**

| Span | Kind | Attributes |
|---|---|---|
| `kedge run <run_id>` | `WORKFLOW` (root) | `kedge.run_id`, `kedge.pr_url` |
| `step <n> <action>` | `TOOL` (`AGENT` for `replan`) | Every field of the [step record](run-files.md#step-record-stepsjsonl), as `kedge.<field>` (lists JSON-encoded) |

Trace tags: `run_id:<id>`, `pr_url:<url>`, `guard:on|off`, `storm:<mode>|off`.

**Readback.** After the run, `trace.trace_url()` runs the npm CLI with the service-account token, never the ingest key:

```bash
~/.local/bin/neatlogs --host https://app.neatlogs.com --profile setup-https---app-neatlogs-com \
  --project "$NEATLOGS_PROJECT_ID" traces list --workflow dependency-pr-repair --limit 50 --json
```

It finds the trace tagged `run_id:<id>` and stores its `traceId` in `result.json` as `trace_url`. The API returns no URL field, so Kedge stores the ID. If the trace hasn't been ingested yet, it stores `unavailable`. The trace still exists; find it later with the same command.

**Finalization delay.** A trace can sit in `"finalizationStatus": "dlq"` or `pending` with 0 spans, sometimes named after its first step, for hours before neatlogs finalizes it with the full tree. Every trace from our runs eventually finalized. Re-query instead of re-running.

## Entire

Code: `kedge/cli.py:run_one`, `kedge/gitgh.py`, `kedge/trails.py`. CLI: Entire 0.11.4.

**Capture inside each run.** In the fresh clone, Kedge runs `entire enable --agent opencode` (or `claude-code`). If the OpenCode plugin file `.opencode/plugins/entire.ts` is missing afterwards, it re-runs with `--force`. Entire's hooks then watch the agent session. Every `git commit` Kedge makes for a clean step gets an `Entire-Checkpoint: <id>` trailer, which `gitgh.commit()` reads back into the step record.

**OpenCode version pin.** OpenCode v2 rejects Entire's plugin ("Plugin must export a default definition…"), so Entire never sees the session. `scripts/setup-opencode.sh` installs OpenCode **1.18.35** into `.tools/opencode`. `worker.use_pinned_opencode()` puts it first on `PATH` with its own XDG data dirs, because Entire's commit hook shells out to `opencode export` and must hit the same binary. The agent also runs with `--dir <clone>`, `PWD=<clone>` and `stdin=DEVNULL`. Without those, OpenCode resolves the wrong project or skips the plugin.

**Explain.** At the end of a run, Kedge runs `entire checkpoint explain <last checkpoint>` and puts the output in `result.json` (`entire_explain`) and in the report and PR body.

**Publishing.** `gitgh.push_branch()` also pushes `refs/entire/*` to the fork, so checkpoints are public next to the branch:

```bash
git ls-remote https://github.com/faroukobayanju/kedge-demo.git 'refs/entire/*'
```

**Trails.** On a green run Kedge first tries `entire trail create --repo gh/<fork> --branch kedge/<run_id> --base <default> --type bug ...`, which opens the PR. It then posts one finding per drift (`entire trail finding add`) and resolves the ones it recovered from. If Trails isn't enabled for the repo (early access), it falls back to `gh pr create --draft`.

## cfo.ai

No code: cfo.ai is where we planned the business. The batch measured tokens per green PR from `steps.jsonl` (`tokens_per_green` in the batch summary). We gave those numbers to cfo.ai's Ari to build a 24-month operating model with Base and Upside scenarios. The result is [business-plan.md](../business-plan.md) and [business-plan.pdf](../business-plan.pdf).

## Related

- [Evidence](../evidence.md)
- [CLI reference: environment](cli.md#environment)
