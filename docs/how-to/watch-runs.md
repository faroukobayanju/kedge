# How to watch and compare runs in the dashboard

Replay any run as a film strip, and race two runs side by side.

## Prerequisites

- At least one run in `runs/`

## Steps

1. Start the dashboard from the repo root:

   ```bash
   uv run kedge ui
   ```

2. Open <http://127.0.0.1:8711>. The newest run is on the lightbox. Open the sheet list (top-left label) to pick another, or go straight to one with `http://127.0.0.1:8711/#<run_id>`.
3. Press **Replay** or Space to replay it.
4. To compare, press **Race**, pick two sheets (for example a `--no-guard` run and a guarded run of the same PR), then press Space.
5. Press `s` for slow motion when you screen-record.

A run still in progress shows as `running` and fills in as steps land. Refresh to update.

## Verification

`curl -s http://127.0.0.1:8711/api/runs | head -c 300` returns JSON for your runs.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Address already in use` | Another `kedge ui` is running. Stop it, or use `--port 8712`. |
| Old data after a code change | Restart `kedge ui`. The server doesn't reload. |
| A run is missing | Its folder has no `meta.json` with a `pr_url` (it crashed before cloning). |

## Related

- [Dashboard and API reference](../reference/dashboard.md)
