# Drift checks

After every agent step Kedge runs the tests and calls `checks.drift()` (`kedge/checks.py`). The first check that fires wins, in this order. Any drift except `over_budget` resets the clone to the last good commit (`git reset --hard` + `git clean -fd`), records the diff hash, and adds a recovery note to the next prompt.

| Order | Drift | Fires when | Rolls back? | Recovery note sent to the agent |
|---|---|---|---|---|
| 0 | `over_budget` (`budget_stop`) | **Before** a step: spend so far + the expected step cost (mean of the last 3) > budget | No: the run stops without paying for the step | (none) |
| 1 | `over_budget` | After a step: total model spend > budget | No: the run stops | (none) |
| 2 | `loop` | The step's diff hash equals one already rolled back | Yes | "You repeated a failed attempt. Try a different approach." |
| 3 | `tests_regressed` | Passed < best passed so far, **or** total < the PR branch's starting total | Yes | "Previous attempt reduced passing/total tests. Do not delete or skip tests." |
| 3b | `tests_regressed` | At least one test passed **and** total < the base branch's total | Yes | (same) |
| 4 | `out_of_plan` | A changed file matches none of the plan's `allowed_files` globs | Yes | "Only edit files matching: {allowed}. You edited: {files}." |

Every recovery note also quotes the agent's last reply back to it: `Your last reply said: "..."`.
| 5 | `verify_failed` | The tests passed and nothing above fired, but a second test run fails or loses tests | Yes | "Tests passed once but failed or lost tests on re-run. Make the fix deterministic." |

`--no-guard` turns off checks 2 to 5. Only the budget stays.

## False claims

`checks.claimed_success()` looks for success language in the agent's last message (`all tests pass`, `tests passing`, `fixed`, `resolved`). It ignores negated sentences (`not`, `never`, `unable`, `cannot`, `can't`, `couldn't`, `still failing`). A step is a `false_claim` when the agent claimed success but the tests did not pass, or the total fell below the PR branch's starting total. A false claim does not roll back by itself. It is flagged in the step record and the ship's log (`🤥`), and with the guard on it adds this note: "Your last message claimed success but tests did not pass. Run the tests before claiming."

## Why there are two test totals

On a broken dependency bump, the PR branch often can't even import the code under test. pytest then reports one error per test **file**, not per test, so `2 errors` reads as 0/2 when the real suite has 5 tests. Kedge counts the tests once on the base branch, in a throwaway `git worktree` (`gitgh.base_total`, retried once). That base count only applies after at least one test passes. Until the import works, only the PR-branch counts are meaningful.

## Allowed-file globs

Globs come from the plan. `fnmatch` lets `*` cross `/`, and `src/**/x` also matches `src/x`. If the planner returns nothing usable, the fallback plan allows common manifest and lock files (`package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `requirements*.txt`, `pyproject.toml`, `poetry.lock`, `uv.lock`, `src/**/*`) plus non-test source files named in the failure output (`worker.files_in_log`, up to 10).

Kedge never counts its own tooling as an agent edit. `.entire/`, `.opencode/`, `.claude/`, `__pycache__/`, `*.pyc`, `.pytest_cache/` and `node_modules/` go into the clone's `.git/info/exclude`.

## What happens after a drift

`supervisor.decide_next()` picks the next action:

| Situation | Next action |
|---|---|
| Last step was `over_budget` | `give_up` |
| More rollbacks than `--max-rollbacks` | `give_up` |
| The last two steps both rolled back | `replan`: ask for a different plan, with the last 3 notes. If `KEDGE_ESCALATE_MODEL` is set, switch to that model from here on. |
| Otherwise | `edit`: another agent step, with the last 3 recovery notes appended |

A run that reaches `--max-steps` without going green ends `gave_up`.

## Entire Trails findings

When a run goes green and Entire Trails is available for the fork, every caught drift becomes a finding on the trail (`kedge/trails.py`):

| Kind | Severity |
|---|---|
| `tests_regressed`, `false_claim` | high |
| `out_of_plan`, `verify_failed` | medium |
| `loop` | low |

Findings the run recovered from (rolled back) are resolved with "Kedge recovered: rolled back and retried".

## Related

- [CLI reference](cli.md)
- [How Kedge works](../explanation/how-kedge-works.md)
