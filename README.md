# Kedge

> *Kedging:* a crew throws a small anchor ahead of a drifting ship, then hauls the ship back on course.

Kedge is a supervisor for unattended coding agents. It runs a headless coding agent to turn failing Dependabot/Renovate PRs green, and checks every step for silent drift: deleted or skipped tests, edits outside the plan, loops, budget overruns and false "all tests pass" claims. When it finds drift, it rolls back to the last good commit and retries with a recovery note.

**Kedge doesn't trust what the agent says. It checks.**

Built for [neatHack](https://neatlogs.com/hackathon), Oct 10–12, 2026. Uses neatlogs (tracing), Entire (checkpoints) and cfo.ai (business plan).

## For judges

| What | Where |
|---|---|
| Demo video | PENDING |
| Before/after numbers | [docs/evidence.md](docs/evidence.md#before-and-after) |
| A run that drifted and recovered (neatlogs trace) | [docs/evidence.md](docs/evidence.md#recovery) |
| Entire checkpoint output | [docs/evidence.md](docs/evidence.md#entire) |
| cfo.ai business plan | [docs/business-plan.pdf](docs/business-plan.pdf) (PENDING) |
| #neatHack posts | [docs/evidence.md](docs/evidence.md#building-in-public) |
| Every judging item mapped to proof | [docs/submission-checklist.md](docs/submission-checklist.md) |

## Status

Work in progress. See [`hackathon.md`](hackathon.md) for the build log.

## For contributors

- Design: [`docs/designs/kedge-design.md`](docs/designs/kedge-design.md)
- Spec: [`docs/specs/kedge-spec.md`](docs/specs/kedge-spec.md)
- Plan, task by task with tests: [`docs/plans/2026-10-10-kedge.md`](docs/plans/2026-10-10-kedge.md)

```bash
uv sync
uv run pytest
cp .env.example .env   # then fill in the keys; never commit .env
./scripts/setup-opencode.sh   # pinned OpenCode v1; v2 breaks Entire's plugin
export PATH="$HOME/.local/bin:$PATH"   # entire CLI
```

Package code lives in `kedge/` (flat layout), and tests live in `tests/`.
