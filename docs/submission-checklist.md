# Submission checklist

Maps each item judges check ([neatlogs.com/hackathon](https://neatlogs.com/hackathon)) to the link that proves it. `PENDING` means the evidence does not exist yet.

Submit on X by quoting the official neatlogs post: team, name, project, public repo, demo. Opens Mon Oct 12, 7:00 PM IST; planned close 11:55 PM IST (Discord cutoff is authoritative).

| Judges check | Weight | Our evidence | Status |
|---|---|---|---|
| The agent handles a substantial task end to end | 30% | `kedge batch targets.json` over 10 real failing Dependabot/Renovate PRs ([targets.json](../targets.json)); summary line in [evidence.md](evidence.md#batch) | PENDING |
| Agent improved (before/after run with numbers) | 25% | `--chaos --no-guard` vs `--chaos` on the same PR, table in [evidence.md](evidence.md#before-and-after) | PENDING |
| neatlogs use | 25% | Trace links or screenshots, one per run in [evidence.md](evidence.md#neatlogs) | PENDING |
| Entire use | 25% | `Entire-Checkpoint:` trailers on agent commits + `entire checkpoint explain` output in [evidence.md](evidence.md#entire) | PENDING |
| cfo.ai use (pricing, costs, revenue, runway) | 25% | [business-plan.pdf](business-plan.pdf) | PENDING |
| Failure recovery | 30% | A run where drift was caught, rolled back and recovered: [evidence.md](evidence.md#recovery) | PENDING |
| Demo video | 20% | Link in [README](../README.md#for-judges) | PENDING |
| Building in public (#neatHack) | 15% | X post links in [evidence.md](evidence.md#building-in-public) | PENDING |
| Code written during the event | required | Public repo, all commits dated Oct 10–12, 2026: `git log --format='%ad %s' --date=iso` | DONE (first commit Oct 10 after 12:30 PM IST) |
| Usefulness and originality | 10% | README pitch: Kedge checks what the agent did, not what it says it did | DONE |
