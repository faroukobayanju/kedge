# Evidence

Every number here comes from a real run. Nothing is filled in by hand. `PENDING` means the run has not happened yet.

## Before and after

Same PR, same storm. Before: guard off. After: Kedge on.

```bash
uv run kedge run <pr> --storm delete-test --no-guard   # BEFORE
uv run kedge run <pr> --storm delete-test              # AFTER
```

| Metric | Before (no guard) | After (Kedge) |
|---|---|---|
| PR | PENDING | PENDING |
| Tests in shipped PR | PENDING | PENDING |
| Drift caught | 0 | PENDING |
| Rollbacks | 0 | PENDING |
| Cost | PENDING | PENDING |
| CI on draft PR | PENDING | PENDING |
| neatlogs trace | PENDING | PENDING |
| Entire checkpoint | PENDING | PENDING |

## Recovery

A run where the agent drifted, Kedge rolled back, and the next step recovered. Report excerpt and voyage chart:

PENDING

## Batch

`uv run kedge batch targets.json` over 10 failing dependency PRs:

```
PENDING
```

| Green PRs | Drifts caught | Mean $ per green PR |
|---|---|---|
| PENDING | PENDING | PENDING |

## neatlogs

One trace per run, tagged `run_id`, `guard`, `chaos`. Each step span carries `kedge.drift`.

PENDING

## Entire

Every agent commit carries an `Entire-Checkpoint:` trailer. Verified in a scratch repo on Oct 10 (see [hackathon.md](../hackathon.md)). From the real runs:

PENDING

## cfo.ai

[business-plan.pdf](business-plan.pdf): $10 per green PR, cost per PR from the batch, two scenarios (50 teams × 20 PRs/month, 200 teams × 30 PRs/month), runway from $0 plus hackathon credits.

PENDING

## Building in public

| # | Post | Link |
|---|---|---|
| 1 | The idea | PENDING |
| 2 | Architecture | PENDING |
| 3 | First trace | PENDING |
| 4 | Drift caught | PENDING |
| 5 | The numbers | PENDING |
| 6 | Submission | PENDING |
