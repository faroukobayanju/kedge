# Kedge

> *Kedging:* a crew throws a small anchor ahead of a drifting ship, then hauls the ship back on course.

Kedge is a supervisor for unattended coding agents. It runs a headless coding agent to turn failing Dependabot/Renovate PRs green, and checks every step for silent drift: deleted or skipped tests, edits outside the plan, loops, budget overruns and false "all tests pass" claims. When it finds drift, it rolls back to the last good commit and retries with a recovery note.

**Kedge doesn't trust what the agent says. It checks.**

On the same PR with the same sabotage, the unsupervised agent shipped a "green" PR with **2 of 5 tests** and said "Fixed" ([kedge-demo#9](https://github.com/faroukobayanju/kedge-demo/pull/9)). Under Kedge, the cheat was caught at step 1, rolled back, and the PR shipped with **5 of 5** ([kedge-demo#10](https://github.com/faroukobayanju/kedge-demo/pull/10)). Over 10 real failing dependency PRs, it turned 4 of 9 fixable ones green, unattended, at $0 model spend.

![The supervisor loop](docs/diagrams/supervisor-loop.png)

Built for [neatHack](https://neatlogs.com/hackathon), Oct 10 to 12, 2026, with neatlogs (a trace per run, a span per step), Entire (a checkpoint on every agent commit) and cfo.ai (the business plan).

## For judges

| What | Where |
|---|---|
| Demo video (80 s) | PENDING: link once posted |
| Every claim with evidence you can check | [docs/evidence.md](docs/evidence.md) |
| Before/after numbers | [docs/evidence.md#the-agent-improved](docs/evidence.md#the-agent-improved) |
| neatlogs traces | [docs/evidence.md#neatlogs](docs/evidence.md#neatlogs) |
| Entire checkpoints | [docs/evidence.md#entire](docs/evidence.md#entire) |
| cfo.ai business plan | [docs/business-plan.pdf](docs/business-plan.pdf) |
| Recovery from failures | [docs/evidence.md#the-agent-recovers-from-failures](docs/evidence.md#the-agent-recovers-from-failures) |
| How we used the three tools | [docs/explanation/tools.md](docs/explanation/tools.md) |
| #neatHack posts | [docs/evidence.md#built-in-public](docs/evidence.md#built-in-public) |
| Judging items mapped to proof | [docs/submission-checklist.md](docs/submission-checklist.md) |

## Quick start

```bash
uv sync
./scripts/setup-opencode.sh            # pinned OpenCode v1; v2 breaks Entire's plugin
export PATH="$HOME/.local/bin:$PATH"   # entire CLI
cp .env.example .env                   # optional: neatlogs keys; never commit .env
uv run pytest -q                       # 87 passed

uv run python -m kedge run https://github.com/faroukobayanju/kedge-demo/pull/1 --storm delete-test
uv run python -m kedge ui                        # replay runs at http://127.0.0.1:8711
```

The PR must be listed in [`targets.json`](targets.json), with a `fork` you can push to. The full walkthrough is the [tutorial](docs/tutorial.md).

## Documentation

All docs: [docs/README.md](docs/README.md).

- [Tutorial](docs/tutorial.md): run the before/after yourself
- How-to: [batch](docs/how-to/run-a-batch.md) · [add a target](docs/how-to/add-a-target.md) · [resume](docs/how-to/resume-a-run.md) · [other agents](docs/how-to/use-claude-code.md) · [dashboard](docs/how-to/watch-runs.md) · [site and video](docs/how-to/build-the-site-and-video.md)
- Reference: [CLI](docs/reference/cli.md) · [drift checks](docs/reference/drift-checks.md) · [run files](docs/reference/run-files.md) · [dashboard API](docs/reference/dashboard.md) · [integrations](docs/reference/integrations.md)
- Explanation: [how Kedge works](docs/explanation/how-kedge-works.md) · [how we used the tools](docs/explanation/tools.md)

## Layout

| Path | What |
|---|---|
| `kedge/` | The package: `cli.py` (commands), `supervisor.py` (the loop), `checks.py` (drift), `worker.py` (agent + planner), `gitgh.py` (git/gh), `trace.py` (neatlogs), `trails.py` (Entire Trails), `report.py`, `shiplog.py`, `chaos.py` (storms), `server.py` + `ui/` (dashboard) |
| `tests/` | 87 pytest tests |
| `site/` | Static landing page with two real runs baked in (`scripts/build_site.py`) |
| `videos/` | The Remotion demo film, with its soundtrack synthesized in code |
| `docs/` | Documentation, evidence, business plan, diagrams |
| `targets.json` | Allowlist of PRs Kedge may touch |

Build log: [hackathon.md](hackathon.md). Design and plan: [design](docs/designs/kedge-design.md) · [spec](docs/specs/kedge-spec.md) · [plan](docs/plans/2026-10-10-kedge.md).
