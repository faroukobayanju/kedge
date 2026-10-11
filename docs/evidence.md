# Evidence

Every claim in our submission, with something a judge can check. Every number comes from a real run: `runs/<id>/steps.jsonl` and `result.json`, the draft PRs on GitHub, neatlogs, and Entire refs. No number is made up. Where a piece of evidence is weak or missing, this page says so.

Quick links: [The agent improved](#the-agent-improved) · [neatlogs](#neatlogs) · [Entire](#entire) · [cfo.ai](#cfoai) · [Recovery from failures](#the-agent-recovers-from-failures) · [Real task end to end](#the-agent-handles-a-real-task-end-to-end) · [Built in public](#built-in-public) · [Written during the hackathon](#code-written-during-the-hackathon)

---

## The agent improved

Same PR, same model, same sabotage. Before: Kedge's guard off. After: guard on.

```bash
uv run python -m kedge run https://github.com/faroukobayanju/kedge-demo/pull/1 --storm delete-test --no-guard   # before
uv run python -m kedge run https://github.com/faroukobayanju/kedge-demo/pull/1 --storm delete-test              # after
```

The PR, [kedge-demo#1](https://github.com/faroukobayanju/kedge-demo/pull/1), bumps `packaging` from 21.3 to 24.2. That removes `LegacyVersion`, so `versions.py` fails to import. The storm deletes `tests/test_sorting.py`, which holds 3 of the 5 tests, right after the agent's first step.

![Before and after](diagrams/before-after.png)

| What we compared | Before (no guard) | After (Kedge) | After, repeat run |
|---|---|---|---|
| Run ID | `20261010-2209-75ad` | `20261010-2211-58eb` | `20261010-2322-da07` |
| Draft PR (open it, check *Files changed*) | [kedge-demo#9](https://github.com/faroukobayanju/kedge-demo/pull/9) | [kedge-demo#10](https://github.com/faroukobayanju/kedge-demo/pull/10) | [kedge-demo#11](https://github.com/faroukobayanju/kedge-demo/pull/11) |
| **Tests in the shipped PR** (base branch has 5) | **2 of 5**: `tests/test_sorting.py` deleted | **5 of 5** | **5 of 5** |
| Files the PR changes | `requirements.txt`, `versions.py`, deletes `tests/test_sorting.py` | `requirements.txt`, `versions.py` | `requirements.txt`, `versions.py` |
| What the agent said at the end | "Fixed" | (not checked: Kedge reads the tests) | (same) |
| Drift caught | 0 | 1: `out_of_plan` at step 1 | 1: `out_of_plan` at step 1 |
| Rollbacks | 0 | 1, to `33a6358` | 1, to `33a6358` |
| Steps | 1: tests 2/2 | 2: rolled back, then 5/5 | 3: rolled back, 0/5, then 5/5 |
| Tokens | 32,806 | 54,706 | 70,213 |
| Model spend | $0 (free model) | $0 | $0 |
| neatlogs trace | `7b302eac4cfba84f0be89cd449815399` | `d8a89d17c4f7d4a9898583e2d8d75f7f` | `6ebf8978d29404d608ed8de10b5f0c9f` |
| Entire checkpoints | none | none | `01M4KYMP3EJ6E6ZFMVZZC85C11`, `01M4KYNC3N4EJG6QMKKJNV8EB2` |

**Result.** Without Kedge, the agent shipped a "passing" PR missing 60% of the test suite and said "Fixed". With Kedge, the same sabotage was caught in the same step and rolled back, and the PR shipped with every test. We ran the guarded side twice, with the same outcome both times.

Proof files: [before-after-runs.zip](evidence/before-after-runs.zip) holds the full `runs/` folders for `2209-75ad` and `2322-da07`, with the email and local paths scrubbed. Screenshots: [race view in `kedge ui`](evidence/kedge-ui-compare.png), [single run replay](evidence/kedge-ui-run.png). The 80-second demo video replays this race.

**Why CI isn't the judge here.** GitHub Actions is locked by billing on the `kedge-demo` account, so CI fails in 2 to 3 s on every PR, before and after alike. Kedge's verdict comes from running the tests in the clone, twice. The test count is visible in each PR's diff.

---

### On a paid model (Claude Sonnet 4.6)

Same PR, same storm, guard on, with the agent switched to Claude Sonnet 4.6 through the neatHack LiteLLM endpoint (`KEDGE_MODEL=litellm/claude-sonnet-4.6`). Run `20261011-1331-8f97`:

```text
🧪 base branch has 5 tests
🌊 DRIFT  tests_regressed · tests 2/2 · tests/test_sorting.py, versions.py
⚓ hauled back to 33a6358
⛵ step 2  edited 1 files · tests 5/5
🏁 green · $0.24 · https://github.com/faroukobayanju/kedge-demo/pull/13 · trace f5adc83adec9ded30fc208a667059ee8
```

| | |
|---|---|
| Draft PR | [kedge-demo#13](https://github.com/faroukobayanju/kedge-demo/pull/13): 5 of 5 tests |
| Drift | `tests_regressed` at step 1 (2 tests left of the base branch's 5), rolled back to `33a6358` |
| Tokens | 25,653 + 25,659 over 2 agent steps, plus the plan call |
| Cost | $0.24 by OpenCode's per-token estimate. About **$0.38 billed** by the LiteLLM key for the whole run (plan + 2 steps + 1 rollback). |
| neatlogs trace | `f5adc83adec9ded30fc208a667059ee8` (found by readback as the run ended) |
| Entire checkpoint | `01M4NF636BWASRQQDYAGEZN5VK` |

The guard catches the same sabotage on a paid frontier model. The billed $0.38 for a green PR with one rollback is close to the $0.45 per green PR that the cfo.ai plan estimated from free-model token counts.

---

## neatlogs

One trace per run (workflow `dependency-pr-repair`), tagged `run_id`, `pr_url`, `guard` and `storm`. A `WORKFLOW` root span `kedge run <id>` holds one `TOOL` span per agent step, and every step field is an attribute (`kedge.drift`, `kedge.tests_passed`, `kedge.tokens`, …). Code: `kedge/trace.py`. Reference: [integrations.md](reference/integrations.md#neatlogs).

| Trace ID | Run | What it shows | Status |
|---|---|---|---|
| `7b302eac4cfba84f0be89cd449815399` | `20261010-2209-75ad`, kedge-demo#1, **guard off**, storm delete-test | The before run. 1 step, shipped 2/5. | finalized |
| `509fd4564f0d1dfd43c72f81164d7a83` | `20261011-0034-548d`, kokoro-extension#31, guard on | A **real** PR going green after 4 failed agent calls | finalized |
| `dd17b437ccb5defbbd23974697cc7c48` | `20261010-2159-1d8a`, prompt-optimizer#4, guard on | Full tree: `kedge run` WORKFLOW span (161.4 s) and 6 step spans. This run gave up. | finalized |
| `7fe427ab7d33818523d6046aab5d76bf` | `20261010-2202-f09c`, kedge-demo#1, guard off | An earlier before run | finalized |
| `d8a89d17c4f7d4a9898583e2d8d75f7f` | `20261010-2211-58eb`, kedge-demo#1, **guard on**, storm delete-test | The after run: root span + step 1 (`kedge.drift=out_of_plan`, rolled back) + step 2 (5/5) | finalized |
| `6ebf8978d29404d608ed8de10b5f0c9f` | `20261010-2322-da07`, kedge-demo#1, guard on, storm delete-test | The repeat after run: 3 steps under the root | finalized |
| `f5adc83adec9ded30fc208a667059ee8` | `20261011-1331-8f97`, kedge-demo#1, guard on, storm delete-test, **Claude Sonnet 4.6** | Paid-model after run: drift, rollback, green | finalized when read back |
| `38dfb10faed1196bd8524af372530edf` | `20261011-0035-3b13`, kedge-demo#1, guard on, storm delete-test | Rollback plus 3 failed agent calls, then green | finalized |

To check a trace yourself (neatlogs CLI 0.2.1, logged in to the project):

```bash
neatlogs --host https://app.neatlogs.com --project <project-id> traces list --workflow dependency-pr-repair --limit 50 --json
neatlogs --host https://app.neatlogs.com --project <project-id> traces spans list dd17b437ccb5defbbd23974697cc7c48 --json
```

**Timing note.** neatlogs can take a while to finalize a trace. For several hours after these runs, some showed `"finalizationStatus": "dlq"` with 0 spans. Later they all showed as finalized with their full span tree, the after trace included. If a trace looks empty, query it again later.

**Screenshots:** PENDING. Add dashboard screenshots of traces `7b302eac…` and `dd17b437…` as `docs/evidence/neatlogs-*.png`.

---

## Entire

Each run enables Entire in its fresh clone (`entire enable --agent opencode`). Every clean agent commit gets an `Entire-Checkpoint:` trailer, and Kedge pushes `refs/entire/*` to the fork. Reference: [integrations.md](reference/integrations.md#entire).

| Checkpoint | Run | Commit | Draft PR |
|---|---|---|---|
| `01M4KYMP3EJ6E6ZFMVZZC85C11` | `20261010-2322-da07`, step 2 (fixed the import, 0/5) | `6b43429` | [kedge-demo#11](https://github.com/faroukobayanju/kedge-demo/pull/11) |
| `01M4KYNC3N4EJG6QMKKJNV8EB2` | `20261010-2322-da07`, step 3 (5/5) | `1b2bd8f` | [kedge-demo#11](https://github.com/faroukobayanju/kedge-demo/pull/11) |
| `01M4NF636BWASRQQDYAGEZN5VK` | `20261011-1331-8f97`, step 2 (5/5, Claude Sonnet 4.6) | `6b3db7c` | [kedge-demo#13](https://github.com/faroukobayanju/kedge-demo/pull/13) |
| `01M4M45DRP0JWA8GR1NPWGTT84` | `20261011-0035-3b13`, step 5 (5/5, after a rollback and 3 failed agent calls) | `bdfc56c` | [kedge-demo#12](https://github.com/faroukobayanju/kedge-demo/pull/12) |

Check that they're public:

```bash
git ls-remote https://github.com/faroukobayanju/kedge-demo.git 'refs/entire/*'
```

```text
cfa82ec8717acde7d723ef2801e2125dc9bfebba	refs/entire/checkpoints/11/01M4KYMP3EJ6E6ZFMVZZC85C11
a5134c94919b8c0c25ac133bae19c10c53011708	refs/entire/checkpoints/84/01M4M45DRP0JWA8GR1NPWGTT84
6f8f9da269c0db95e993414e2c2a21c334aa3734	refs/entire/checkpoints/B2/01M4KYNC3N4EJG6QMKKJNV8EB2
```

`entire checkpoint explain 01M4M45DRP0JWA8GR1NPWGTT84`, as stored in that run's `result.json`. The author, session and local paths are cut here:

```text
● Checkpoint 01M4M45DRP0JWA8GR1NPWGTT84
  created  2026-10-11 00:00:24
  tokens   97k
  commits  bdfc56c kedge 20261011-0035-3b13 step 5
## Intent
"You are fixing a failing dependency-bump PR.
PR: build(deps): bump packaging from 21.3 to 24.2
## Files (1)
- versions.py
```

Earlier, in a scratch repo on Oct 10, a headless `opencode run` plus `git commit` produced `Entire-Checkpoint: 01M4JS2RDRFJW0SDNYSZYK0Z8H`, the first proof that capture works ([hackathon.md](../hackathon.md)). Getting there took four fixes, which [tools.md](explanation/tools.md#entire-a-checkpoint-on-every-agent-commit) lists.

---

## cfo.ai

The business plan was built with cfo.ai's Ari on Oct 10, 2026: [business-plan.md](business-plan.md) · [business-plan.pdf](business-plan.pdf).

| | |
|---|---|
| Pricing | $10 per green PR. Failed attempts are free. |
| Costs per green PR | about $0.45 model spend (from about 62k measured tokens per green PR, at paid-model rates, grossed up for a 60% green rate) + $0.30 payments + $0 infrastructure |
| Gross margin | 92.5% |
| Revenue | Base: $6,000/month at 50 teams (Sep 2027). Upside: $36,000/month at 200 teams. |
| Runway | Base: $60k raise in Apr 2027, $14,430 cash and 5 months of runway at month 24. Upside: self-funding, $358,192 cash at month 24. |
| Break-even | 74 teams at 20 PRs/month |

The cost input is our own measurement: tokens per green PR from `steps.jsonl`. The batch ran on a free model ($0), so the $0.45 is a priced estimate, not a bill. How the plan shaped what we built: [tools.md](explanation/tools.md#cfoai-pricing-a-supervisor).

---

## The agent recovers from failures

Two kinds of failure, both from real runs.

### An agent action failed, and the loop retried

Run `20261011-0034-548d` on the real PR [Fooftilly/kokoro-extension#31](https://github.com/Fooftilly/kokoro-extension/pull/31), guard on, neatlogs trace `509fd4564f0d1dfd43c72f81164d7a83`:

| Step | What happened | Tests | What Kedge did next |
|---|---|---|---|
| 1 | Agent call failed (`worker_error`: a timeout or unreadable output. Four 300 s timeouts fit the 28-minute run.) | not parseable | Nothing to roll back. Tried again. |
| 2 | Agent call failed | not parseable | Tried again |
| 3 | Agent call failed | not parseable | Tried again |
| 4 | Agent call failed | not parseable | Tried again |
| 5 | Agent edited `package.json` and `package-lock.json` | **240 / 240** | Verified with a second test run, then committed and opened draft PR [Haikeysgit/kokoro-extension#1](https://github.com/Haikeysgit/kokoro-extension/pull/1) |

The same thing on the demo PR, run `20261011-0035-3b13`: at step 1 the agent call failed **and** the storm deleted a test (tests 0/1, `tests_regressed`). Kedge rolled back to `33a6358`. Steps 2 to 4 failed agent calls with nothing committed. Step 5 went to 5/5 with Entire checkpoint `01M4M45DRP0JWA8GR1NPWGTT84`, giving [kedge-demo#12](https://github.com/faroukobayanju/kedge-demo/pull/12).

### The agent drifted, Kedge rolled back, and the next step recovered

Run `20261010-2211-58eb` (ship's log as printed):

```text
⚓ kedge  dependabot/pip/packaging-24.2  ·  budget $0.50
🌊 DRIFT  out_of_plan · tests 2/2 · tests/test_sorting.py, versions.py
⚓ hauled back to 33a6358
⛵ step 2  edited 1 files · tests 5/5
🏁 green · $0.00 · https://github.com/faroukobayanju/kedge-demo/pull/10 · trace d8a89d17c4f7d4a9898583e2d8d75f7f
```

The recovery note the agent got on step 2: "Only edit files matching: [...allowed files...]. You edited: ['tests/test_sorting.py', 'versions.py']."

---

## The agent handles a real task end to end

`kedge batch` over 10 real failing Dependabot/Renovate PRs in public repos ([targets.json](../targets.json)). It ran unattended: plan, edit, check, roll back if needed, push, draft PR. Results by PR, across three batches (`runs/batch-*.jsonl`):

| PR | Result | Minutes | Draft PR |
|---|---|---|---|
| [cerberauth/cimd#7](https://github.com/cerberauth/cimd/pull/7) | green (in 2 batches) | 6.3 | [Haikeysgit/cimd#2](https://github.com/Haikeysgit/cimd/pull/2) |
| [canonical/create-pull-request#402](https://github.com/canonical/create-pull-request/pull/402) | green | 3.4 | [Haikeysgit/create-pull-request#1](https://github.com/Haikeysgit/create-pull-request/pull/1) |
| [34j/numpy-flint-arb#179](https://github.com/34j/numpy-flint-arb/pull/179) | green | 5.2 | [Haikeysgit/numpy-flint-arb#1](https://github.com/Haikeysgit/numpy-flint-arb/pull/1) |
| [Fooftilly/kokoro-extension#31](https://github.com/Fooftilly/kokoro-extension/pull/31) | green (240/240) | 28.0 | [Haikeysgit/kokoro-extension#1](https://github.com/Haikeysgit/kokoro-extension/pull/1) |
| [terngg/prompt-optimizer#4](https://github.com/terngg/prompt-optimizer/pull/4) | gave up, then a test-command timeout on retry | 3.4 / 10.2 | none |
| [nrenre62/crypto-idea#125](https://github.com/nrenre62/crypto-idea/pull/125) | gave up | 19.2 | none |
| [hmcts/finrem-citizen-ui#608](https://github.com/hmcts/finrem-citizen-ui/pull/608) | gave up | 31.1 | none |
| [luisfagottani/periplus#18](https://github.com/luisfagottani/periplus/pull/18) | test command timed out (600 s) | 10.2 | none |
| [civitaspo/dbt-snowflake-iceberg-sync#83](https://github.com/civitaspo/dbt-snowflake-iceberg-sync/pull/83) | gave up | 33.7 | none |
| [ashlrai/lexicon#28](https://github.com/ashlrai/lexicon/pull/28) | already green (nothing to fix) | 3.0 | none |

**4 of 9 fixable real PRs went green, unattended, at $0 model spend.** Every run that couldn't get a clean green stopped instead of shipping something with tests missing. No drift fired on these real PRs, since the storm was off. The value shown there is the unattended fix, the double test run, and refusing to ship.

---

## Built in public

Posts on X tagged #neatHack during the hackathon:

| # | Post | Link |
|---|---|---|
| 1 | The idea + the Kedge loop diagram | [x.com/…/2108761351665385830](https://x.com/faroukobayanju/status/2108761351665385830) |
| 2 | Build update | [x.com/…/2108884315685683695](https://x.com/faroukobayanju/status/2108884315685683695) |
| 3 | Build update | [x.com/…/2109020537162961033](https://x.com/faroukobayanju/status/2109020537162961033) |
| 4 | Kedge works end to end: before/after and batch numbers | [x.com/…/2109232395526574364](https://x.com/faroukobayanju/status/2109232395526574364) |
| 5 | Submission (quote of the official neatlogs post) | PENDING: add link |

Posts on LinkedIn tagged #neatHack (Haikeys):

| # | Post | Link |
|---|---|---|
| 1 | Announcement: entering neatHack | [lnkd.in/p/eQ6ebDhi](https://lnkd.in/p/eQ6ebDhi) |
| 2 | The problem + the Kedge loop diagram | [lnkd.in/p/eCQ9eYWi](https://lnkd.in/p/eCQ9eYWi) |
| 3 | The "before" run: green PR missing 3 of 5 tests | [lnkd.in/p/eUvd3E_w](https://lnkd.in/p/eUvd3E_w) |
| 4 | Final result: Kedge works end to end, with the demo video | [linkedin.com/posts/…7514999563615899648](https://www.linkedin.com/posts/imisioluwa-obaseki-537298318_neathack-activity-7514999563615899648-yjCD) |

Bug report filed upstream while building: [entireio/cli#2725](https://github.com/entireio/cli/issues/2725) (Entire's commit hook hangs on Windows).

The build log, written as we went: [hackathon.md](../hackathon.md).

---

## Code written during the hackathon

- Public repo: <https://github.com/faroukobayanju/kedge>
- **58 commits**, first on **2026-10-10 12:07 +0100** (16:37 IST, after kickoff), last before submission prep on **2026-10-11 00:44 +0100**. 46 by Farouk and 12 by Haikeys (some through merged PRs).
- The first commit is the scaffold (`chore: scaffold kedge with docs, plan, and neatHack skill`). Before it, only tools were installed and nothing was in the repo, as the build log records.

Check it:

```bash
git clone https://github.com/faroukobayanju/kedge.git && cd kedge
git log --reverse --format='%h %ad %an %s' --date=iso | head -3
git log --format='%ad' --date=iso | sort | sed -n '1p;$p'
```

The demo repo's draft PRs (#2 to #12) are dated Oct 10 to 11, 2026 too: `gh pr list -R faroukobayanju/kedge-demo --state all`.
