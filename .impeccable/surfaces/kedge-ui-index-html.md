---
version: 1
slug: "kedge-ui-index-html"
primary_target: "kedge/ui/index.html"
related_targets: []
---

# Surface: Kedge run dashboard (`kedge ui`)

Mode: Operate (viewed mostly through a 2-minute demo video by hackathon judges; secondary: devs inspecting their runs).
Job: in seconds, see which runs went green, where the agent drifted or lied, that Kedge rolled back, and jump to evidence (draft PR, neatlogs trace, Entire checkpoint). Compare a --no-guard run with a guarded run on the same PR.
Data: runs/*/steps.jsonl, plan.json, meta.json, report fields; runs/batch-*.jsonl summary.
States: green, gave_up, already_green, running (no report yet), empty (no runs), drift, false claim, worker error, replan.
Later surface: a public landing page reusing this world.

## Direction contract

THESIS: Every agent claim goes to the monitor. A run is a replay with a scoreline (tests passed/total); each drift is a VAR check that ends in a ruling (disallowed, rolled back). Refuses the default sidebar + badge table + vertical timeline.

OWN-WORLD: Broadcast graphics on pitch-night navy (#0e1621 ground, #16212e panels), white type, one green #00e0a4 for confirmed/green, yellow #ffd400 for CHECK in progress/attention, red #ff3b30 for disallowed/drift. Barlow Condensed (self-hosted) for display and scorelines, Barlow for UI text, tabular numerals. Drift also reads without colour: disallowed segments carry diagonal hatch and a stop bar. State lives in fixed cells (filled = held, hollow = not, struck = disallowed).

STORY: Judge sees the run list as a fixture list with scorelines, opens one, watches the replay strip: steps as frames, a CHECK banner over the drift, "Disallowed: test deleted, rolled back to 9f3c1e2", scoreline flips to green, final whistle = draft PR. Believes Kedge checks, not trusts. Clicks the trace/checkpoint.

FIRST VIEWPORT: Top bar: Kedge wordmark, batch scoreline (green/total, drifts caught, false claims, $), Compare toggle. Left rail: fixture list (No. sequence headline per run, PR repo#n, status cell, small replay strip at thumbnail scale). Main: selected run header (No., PR title, final scoreline large), the replay strip full width as the signature move, then ruling cards for each check, then evidence row (draft PR, trace, checkpoint, plan). Primary action: open draft PR.

FORM: VAR Review Room, my top-ranked grounded candidate (rank 1 of 7), shown as the pick card; seed key ff2e4c23. Raises kept: fixed state cells, one sequence number per run, colour-independent drift marks, one replay drawing at three scales.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
