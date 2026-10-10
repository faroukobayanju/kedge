# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML/CSS/JS only, with no build step and no new dependencies. The dashboard is served locally by `kedge ui` (Python stdlib `http.server`) and reads the run data Kedge already writes under `runs/`. A public landing page, if built, is a static page that reuses the dashboard's visual language.

## Users

The primary viewers are **hackathon judges watching a 2-minute demo video** (neatHack, Oct 10–12 2026). Within seconds they must grasp the core story: *the agent drifted, Kedge caught it, rolled back, and the PR went green.* Several judges come from Entire and neatlogs, so they will look for real use of their tools.

Secondary users are developers running Kedge on their own repos, who inspect what happened in a run.

## Product Purpose

Kedge is a supervisor for unattended coding agents. It runs a headless coding agent (OpenCode by default, Claude Code optionally) on a bounded task: turning a failing Dependabot/Renovate PR green. After every step it checks for silent drift and rolls back to the last good commit when it finds any, then retries with a recovery note. It opens a draft PR only when the tests pass, including a second verification run.

Success means a red dependency PR becomes green without a human watching, and every cheat the agent tried is caught and recorded.

## Positioning

Kedge doesn't trust what the agent says; it checks. Drift detection is deterministic: test counts, file allowlists, diff hashes and budgets, with no LLM judge. Recovery is built into how it runs: git rollback, Entire checkpoints, and drifts posted as Entire Trail findings when Trails is enabled. Kedge is the layer above any coding agent, not another coding agent.

## Operating Context

- CLI: `kedge run <pr-url>`, `kedge batch targets.json`, `kedge resume <run_id>`, flags `--storm delete-test|skip-test|stray-edit` and `--no-guard`.
- Per-run artifacts in `runs/<run_id>/`: `steps.jsonl` (one record per step), `plan.json`, `state.json`, `meta.json`, `report.html`, `report.md`. A batch writes `runs/batch-*.jsonl` with a summary line.
- Step record fields: `step`, `action` (worker | worker_error | replan), `files_changed`, `tests_passed`, `tests_total`, `cost_usd`, `cost_usd_total`, `tokens`, `drift` (null | tests_regressed | out_of_plan | loop | verify_failed | over_budget), `rolled_back`, `checkpoint_sha`, `entire_checkpoint`, `false_claim`, `claim`, `plan_step`.
- neatlogs traces under workflow `dependency-pr-repair`, one per run, tagged `run_id:<id>`.
- Demo flow: a "race" of `--no-guard` vs Kedge on the same PR, then a judge picks a `--storm` mode live.

## Capabilities and Constraints

- Already shipped: run loop, drift checks, rollback, replanning, verification re-run, false-claim flag, resume, cross-run lessons, ship's-log terminal output, a voyage-chart SVG in `report.html`, neatlogs tracing with readback, and the Entire Trails integration with a draft-PR fallback.
- Terminology to keep: drift, haul back, storm, voyage, false claim, checkpoint, trail.
- Undecided: the per-trace neatlogs app URL format (reports currently show the trace ID). Trails depends on Entire early access, which hasn't been granted yet.

## Brand Commitments

- Name: **Kedge**. Kedging means throwing an anchor ahead of a drifting ship and hauling it back on course.
- Tagline: "Pulls your coding agent back on course." Line: "Kedge doesn't trust what the agent says. It checks."
- Nautical vocabulary and glyphs already in use: ⚓ ⛵ 🌊 🧭 💸 🏁 🤥.
- Judges asked for something "simple but elegant, with fun."

## Evidence on Hand

- Real green runs on `faroukobayanju/kedge-demo` PR #1 (packaging 21.3 → 24.2, `LegacyVersion` removed): draft PRs #2–#5. 1 step, about 1 min, $0 on a free model.
- A real green run on `cerberauth/cimd#7` through the fork `Haikeysgit/cimd`.
- Batch over 10 targets in progress (`runs/batch-2.jsonl`).
- neatlogs traces confirmed by CLI readback (e.g. run `20261010-2106-37b8` → trace `3009e94623c086449d3422d0d6473efe`).
- `diagrams/kedge-loop.png` and `diagrams/first-pr-card.png`.
- Do not fabricate: drift-caught numbers from real PRs (no real `--storm` run has happened yet), customers, testimonials or pricing beyond the cfo.ai plan.

## Product Principles

1. Show the catch: every drift, rollback and false claim is visible, never hidden in logs.
2. Evidence over claims: every number links to a run, trace or checkpoint.
3. Readable at demo speed: the story is legible in a few seconds of video.
4. Deterministic and honest: Kedge never claims success the tests don't show.
