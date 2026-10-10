# Demo video script (2:00)

Judges score: how clearly it explains the agent and the use of neatlogs, Entire and cfo.ai (20%). Every claim on screen comes from a real run.

Record on Farouk's Mac. Terminal font 18pt+, dark theme. Crop tokens, emails and private links out of every frame.

| Time | Shot | On screen | Voiceover |
|---|---|---|---|
| 0:00–0:10 | Hook | Title card: "My agent said 'all tests pass'. It had deleted one." | "Coding agents left alone don't crash. They drift, and they still report success." |
| 0:10–0:40 | The race | Split terminal. Left: `kedge run <pr> --storm delete-test --no-guard`. Right: `kedge run <pr> --storm delete-test`. Left ships fast with fewer tests. Right shows 🌊 drift, ⚓ rolled back, 🏁 green. | "Same PR, same sabotage. Without Kedge, the PR ships with a test missing. With Kedge, the drift is caught, rolled back, and the agent fixes it for real." |
| 0:40–1:05 | Judge's pick | `kedge run <pr> --storm skip-test` or `--storm stray-edit`, caught live. | "Pick a storm. Skip a test, or edit a file outside the plan. Kedge checks what the agent did, not what it says." |
| 1:05–1:20 | Voyage chart | Open `runs/<id>/report.html`. Waves, anchors, the finish flag, the CI line. | "Every run leaves a report: each step, each drift, each rollback." |
| 1:20–1:35 | neatlogs | Trace for the recovered run, step span open on `kedge.drift`. | "neatlogs traces every step, so you see exactly where it drifted." |
| 1:35–1:45 | Entire | `git log -1` showing the `Entire-Checkpoint:` trailer, then `entire checkpoint explain HEAD`. | "Entire checkpoints every agent commit: the intent, the tool calls, the tokens." |
| 1:45–1:55 | cfo.ai | `docs/business-plan.pdf`: price, cost per PR, two scenarios, runway. | "$10 per green PR. Our batch cost $X per PR. cfo.ai planned the business." |
| 1:55–2:00 | Close | Batch line: "N of 10 red PRs green, M drifts caught." Logo. | "Kedge pulls your coding agent back on course." |

## Needs before recording
- Task 16 (`--storm`) merged. Until then, use `--chaos`.
- One before/after pair on the same PR, with real numbers in [evidence.md](evidence.md).
- One neatlogs trace URL for a recovered run.
- `docs/business-plan.pdf`.
- Batch summary line.
