# Submission checklist

Maps each item judges check ([neatlogs.com/hackathon](https://neatlogs.com/hackathon)) to the evidence that proves it. `PENDING` means something is still missing.

Submit on X by quoting the official neatlogs post with the team, name, project, public repo and demo. Submissions open Mon Oct 12, 7:00 PM IST; our planned close is 11:55 PM IST (the Discord cutoff is authoritative).

| Judges check | Our evidence | Status |
|---|---|---|
| The agent handles a substantial task end to end | `kedge batch` over 10 real failing Dependabot/Renovate PRs: 4 of 9 fixable PRs green, unattended, $0 ([evidence](evidence.md#the-agent-handles-a-real-task-end-to-end)) | DONE |
| The agent improved (before/after with numbers) | Same PR and sabotage: 2 of 5 tests shipped without Kedge, 5 of 5 with Kedge, twice ([evidence](evidence.md#the-agent-improved)) | DONE |
| You used neatlogs | Finalized traces for the before run and all three guarded after runs; one trace per run, one span per step ([evidence](evidence.md#neatlogs)) | DONE (dashboard recording in the demo video, scene 06) |
| You used Entire | 4 checkpoints on agent commits, public under `refs/entire/*`, plus `entire checkpoint explain` output ([evidence](evidence.md#entire)) | DONE |
| You used cfo.ai (pricing, costs, revenue, runway) | [business-plan.pdf](business-plan.pdf), summary in [evidence](evidence.md#cfoai) | DONE |
| How well the tools were used | [How we used neatlogs, Entire and cfo.ai](explanation/tools.md) | DONE |
| The agent recovers from failures | Failed agent calls retried to green on a real PR; drift rolled back and recovered ([evidence](evidence.md#the-agent-recovers-from-failures)) | DONE |
| Demo video | 104 s, 1080p60, rendered from `videos/`: [posted on X](https://x.com/faroukobayanju/status/2109643801396379876) | DONE |
| Built in public (#neatHack) | X post links in [evidence](evidence.md#built-in-public) | PENDING: add links |
| Code written during the event | Public repo, 58 commits dated Oct 10 to 11, 2026, the first at 16:37 IST ([evidence](evidence.md#code-written-during-the-hackathon)) | DONE |
| Usefulness and originality | Kedge checks what the agent did, not what it says it did ([how it works](explanation/how-kedge-works.md)) | DONE |
