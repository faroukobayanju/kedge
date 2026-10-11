# Dashboard and API

`kedge ui` (`kedge/server.py`) serves the dashboard in `kedge/ui/` and a read-only JSON view of `runs/`. It binds to `127.0.0.1` only, on port `8711` by default. It uses the standard-library HTTP server and has no dependencies.

## The dashboard

The page is a "contact sheet on a lightbox": each run is a strip of film, one frame per step.

| Control | What it does |
|---|---|
| **Replay** button, or Space | Replays the selected run: frames feed in, a drift gets a red X, the strip rewinds to the last good frame, and the final print lifts off |
| **Race** button | Pick two runs from the sheet list and replay them side by side (the before/after view) |
| Sheet label (top left) | Opens the list of runs |
| `s` | Toggle slow motion (0.55×) for screen recording |
| Esc | Close the open slip or the sheet list |
| `#<run_id>` in the URL | Open that run directly |

The score always uses the base-branch test count as the denominator, so a run that deleted 3 of 5 tests reads 2/5, never 2/2.

## API

| Route | Returns |
|---|---|
| `GET /api/runs` | Array of run objects, newest first. Folders without a `pr_url` are skipped. |
| `GET /api/runs/<run_id>` | One run object, or `404 {"error": "run not found"}`. The ID must contain only `0-9a-f-`, which blocks path tricks. |
| `GET /*` | Static files from `kedge/ui/` |

Responses are `application/json` with `Cache-Control: no-store`.

Run object fields: `run_id`, `pr_url`, `title`, `repo`, `status` (`running` while there is no `result.json`), `guard`, `storm`, `cost_usd_total`, `rollbacks`, `drifts`, `false_claims`, `draft_pr`, `trace`, `ci_status`, `entire_explain`, `finished_at`, `base_total`, `plan`, `steps`.

Runs from before `result.json` existed are read back from `report.md`.

## The landing page (`site/`)

`site/` is a static copy of the same replay engine with two real runs baked in, for judges who won't run anything:

```bash
uv run python scripts/build_site.py 20261010-2209-75ad 20261010-2211-58eb
```

The script copies `app.js`, `app.css`, `fonts2.css` and the fonts from `kedge/ui/`. It writes only the public fields of each run to `site/data.js`, and scrubs local paths and the username out of the Entire text.

## Related

- [Run files](run-files.md)
- [How to watch runs in the dashboard](../how-to/watch-runs.md)
