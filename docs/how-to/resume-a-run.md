# How to resume a crashed run

Continue a run that was killed (laptop slept, Ctrl+C, crash) from its last saved step, with the same settings.

## Prerequisites

- The run folder `runs/<run_id>/` with `state.json` and `meta.json`
- The clone still in `$TMPDIR/kedge/<run_id>` (it is lost if the temp folder was cleaned)

## Steps

1. Find the run ID: the folder name in `runs/`, or the newest one:

   ```bash
   ls -t runs | head -3
   ```

2. Resume it:

   ```bash
   uv run python -m kedge resume <run_id>
   ```

   Kedge resets the clone to the last good commit (dropping the half-finished step), then continues the loop. It keeps the original `--no-guard`, `--storm`, budget and limits from `meta.json`. New steps append to the same `steps.jsonl`.

## Verification

The command prints the same summary JSON as `kedge run`, and `runs/<run_id>/result.json` now exists.

## Troubleshooting

| Error | Fix |
|---|---|
| `error: no saved state for run <id>` | The run never finished its first save. Start a new run. |
| `fatal: not a git repository` | The clone in `$TMPDIR/kedge/<run_id>` is gone. Start a new run. |

## Related

- [Run files: state.json](../reference/run-files.md)
