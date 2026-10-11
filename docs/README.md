# Kedge documentation

Kedge supervises unattended coding agents. It turns failing Dependabot/Renovate PRs green, checks every agent step for silent drift, and rolls back to the last good commit when the agent cheats.

| If you want to… | Read |
|---|---|
| See it work in 15 minutes | [Tutorial: watch Kedge catch a cheating agent](tutorial.md) |
| Check our claims (judges) | [Evidence](evidence.md) · [Submission checklist](submission-checklist.md) |
| Understand the design | [How Kedge works, and why](explanation/how-kedge-works.md) |
| See how we used neatlogs, Entire and cfo.ai | [How we used the tools](explanation/tools.md) |

## How-to guides

- [How to run a batch over many PRs](how-to/run-a-batch.md)
- [How to add a failing PR as a target](how-to/add-a-target.md)
- [How to resume a crashed run](how-to/resume-a-run.md)
- [How to use Claude Code or another model as the agent](how-to/use-claude-code.md)
- [How to watch and compare runs in the dashboard](how-to/watch-runs.md)
- [How to rebuild the landing page and the demo video](how-to/build-the-site-and-video.md)

## Reference

- [CLI](reference/cli.md): commands, flags, `targets.json`, environment, the ship's log
- [Drift checks](reference/drift-checks.md): every check, its order and its recovery note
- [Run files](reference/run-files.md): everything in `runs/<id>/`
- [Dashboard and API](reference/dashboard.md): `kedge ui`, `/api/runs`, `site/`
- [Integrations](reference/integrations.md): what neatlogs, Entire and cfo.ai get, and where in the code

## Diagrams

Source HTML and PNG in [`diagrams/`](diagrams/):

- [The supervisor loop](diagrams/supervisor-loop.png)
- [Before and after on kedge-demo#1](diagrams/before-after.png)
- [Where the tools plug in](diagrams/tools-map.png)

## Background

- [Business plan (cfo.ai)](business-plan.md)
- [Design](designs/kedge-design.md) · [Spec](specs/kedge-spec.md) · [Build plan](plans/2026-10-10-kedge.md)
- [Build log](../hackathon.md)
- Visual design of the dashboard: [PRODUCT.md](../PRODUCT.md), [DESIGN.md](../DESIGN.md)
