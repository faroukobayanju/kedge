# How to run a batch over many PRs

Run Kedge unattended over every PR in a targets file and get one summary line with green count, drifts caught, spend and tokens.

## Prerequisites

- Kedge installed (see the [tutorial](../tutorial.md), steps 1 and 2)
- A targets file. [`targets.json`](../../targets.json) has 10 real failing Dependabot/Renovate PRs, each with a fork you can push to. To use your own forks, see [How to add a target](add-a-target.md).

## Steps

1. Start the batch and keep the results:

   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   uv run kedge batch targets.json 2> runs/batch.err | tee runs/batch.jsonl
   ```

   The ship's log goes to `runs/batch.err`. One JSON line per target, then the summary, goes to `runs/batch.jsonl`. A run takes 2 to 35 minutes depending on install time and how often the free model stalls.

2. To run only some targets, write a smaller file:

   ```bash
   python3 -c "import json; t=json.load(open('targets.json')); json.dump([x for x in t if 'cimd' in x['pr_url']], open('runs/one.json','w'))"
   uv run kedge batch runs/one.json
   ```

## Verification

The last line of `runs/batch.jsonl` is the summary:

```bash
tail -1 runs/batch.jsonl
```

```json
{"green": 1, "total": 3, "drifts_caught": 0, "false_claims": 0, "usd_total": 0.0, "usd_per_green": 0.0, "tokens_total": 37996, "tokens_per_green": 37996, "mean_steps": 3.67, "mean_minutes": 23.96}
```

Every green line has a `draft_pr` URL on the target's fork.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `"status": "error: Command '… ' timed out after 600 seconds"` | The test command is too slow (usually the install). Speed it up or drop the target. |
| Many `worker_error` steps (`⛈` in the log) | The free model stalled. Each agent call times out after 300 s and the loop retries. Try another `KEDGE_MODEL`, or `KEDGE_WORKER=claude`. |
| `gave_up` with `tests -1/-1` on every step | Kedge can't parse the test output. Check that `test_cmd` prints a Jest or pytest summary. |
| Every Python step drifts `out_of_plan` on `__pycache__` | You're on an old clone. Current Kedge excludes test artifacts and sets `PYTHONDONTWRITEBYTECODE=1`. |

## Related

- [CLI reference: batch](../reference/cli.md#kedge-batch)
- [Evidence: our batch results](../evidence.md#the-agent-handles-a-real-task-end-to-end)
