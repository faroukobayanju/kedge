# How we used neatlogs, Entire and cfo.ai

Each tool answers one question about the agent. neatlogs: **what did it do, step by step?** Entire: **why did it write this code?** cfo.ai: **is supervising agents a business?** We used each one to build Kedge, to improve it, and to plan around it. This page says how, with the bugs each one helped us find.

![Where the tools plug in](../diagrams/tools-map.png)

## neatlogs: one trace per run, one span per step

**Build.** Kedge emits a `WORKFLOW` root span per run and a `TOOL` span per agent step, with the whole step record as attributes. The attributes are `kedge.drift`, `kedge.tests_passed`, `kedge.tests_total`, `kedge.files_changed`, `kedge.tokens`, `kedge.rolled_back`, `kedge.false_claim` and the rest. Tags `guard:on|off` and `storm:<mode>` make a before run and an after run filterable side by side. Details: [integrations.md](../reference/integrations.md#neatlogs).

**Improve.** Reading traces back is how we found three of Kedge's bugs:

- **The readback shape.** The neatlogs OpenAPI spec showed that `traces list` returns `{data: {traces: [...]}}` with a `traceId` but no URL. Kedge was looking for a URL. We fixed the parser (commit `423216a`) and now store the ID.
- **The wrong `neatlogs` binary.** The Python SDK installs its own `neatlogs` script into the venv, which shadowed the npm CLI. Readback silently returned nothing until Kedge called `~/.local/bin/neatlogs` explicitly.
- **Readback timing.** Traces that show `unavailable` in `result.json` were often just not ingested yet when the run finished. The before run's trace `7b302eac…` was found minutes later with the same query. That's why the docs tell you to re-query.

**Plan.** The tokens per step that neatlogs carries (and that `steps.jsonl` keeps) are the input to the cfo.ai cost model.

**A false alarm worth knowing about.** For a few hours several traces showed `dlq` with 0 spans, and we suspected Kedge was losing its root span. They all finalized later with the full tree. The lesson: neatlogs finalization can lag, so check again before debugging.

## Entire: a checkpoint on every agent commit

**Build.** In every fresh clone Kedge runs `entire enable --agent opencode`. Every commit of a clean step then carries an `Entire-Checkpoint:` trailer. Kedge records the ID per step, puts `entire checkpoint explain` in the report and PR body, pushes `refs/entire/*` to the fork, and turns drifts into Entire Trail findings. Details: [integrations.md](../reference/integrations.md#entire).

**Improve.** Making Entire see a headless agent took most of day one, and it fixed four real bugs:

- **OpenCode v2 broke Entire's plugin.** OpenCode's own log showed `failed to load plugin … Plugin must export a default definition`, so Entire never saw a session and we got 0 checkpoints. Fix: pin OpenCode 1.18.35 (`scripts/setup-opencode.sh`) and put it first on `PATH` with its own XDG dirs, because Entire's hook calls `opencode export`.
- **OpenCode resolved the project from `PWD`,** so it edited, and loaded plugins from, the caller's directory instead of the clone. Fix: `--dir <clone>` plus `PWD=<clone>`.
- **An inherited stdin stopped OpenCode loading the plugin.** Fix: `stdin=DEVNULL`.
- **Entire's own files counted as drift.** `.entire/` and `.opencode/` showed up as `out_of_plan` edits until Kedge added them to `.git/info/exclude`.

**What it gives a reviewer.** `entire checkpoint explain 01M4M45DRP0JWA8GR1NPWGTT84` shows the agent's intent ("You are fixing a failing dependency-bump PR…"), the tokens (97k), the commit (`bdfc56c`) and the one file it touched (`versions.py`). A reviewer can see why the code exists without trusting the agent's summary.

## cfo.ai: pricing a supervisor

**Plan.** We built the business plan with cfo.ai's Ari: [business-plan.md](../business-plan.md) and [business-plan.pdf](../business-plan.pdf).

- **Price:** $10 per green PR. Failed attempts are free, so the customer pays only for what Kedge's checks let through.
- **Cost:** about $0.45 model spend per green PR. That figure is priced from measured tokens per green PR (about 62k), at paid-model rates, grossed up for a 60% green rate. Add $0.30 payment processing and $0 infrastructure (it runs on the customer's CI). Gross margin is 92.5%.
- **Two scenarios.** Base: 50 teams by Sep 2027, $6k/month revenue, a $60k raise needed in Apr 2027, $14,430 cash at month 24. Upside: 200 teams, $36k/month, self-funding, $358,192 cash at month 24.

**Improve.** The model told us the lever is volume, not price: break-even needs 74 teams at 20 PRs/month. And green rate is pure margin, since only green PRs are billed. That's why the hackathon effort went into green rate and honest drift catching rather than features.

**Honest caveat.** Every batch run used a free model ($0), so the $0.45 is an estimate from token counts, not a bill. It gets replaced once paid runs exist.

## Related

- [Evidence for every claim](../evidence.md)
- [How Kedge works](how-kedge-works.md)
