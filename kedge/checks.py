import re
from fnmatch import fnmatch

NOTES = {
    "tests_regressed": "Previous attempt reduced passing/total tests. Do not delete or skip tests.",
    "out_of_plan": "Only edit files matching: {allowed}. You edited: {files}.",
    "loop": "You repeated a failed attempt. Try a different approach.",
    "verify_failed": "Tests passed once but failed or lost tests on re-run. Make the fix deterministic.",
    "false_claim": "Your last message claimed success but tests did not pass. Run the tests before claiming.",
}

CLAIM = re.compile(r"all (?:the )?tests (?:now )?pass(?:ing)?|tests (?:are )?passing|\bfixed\b|\bresolved\b", re.I)
NEGATION = re.compile(r"\b(?:not|never|unable|cannot|can't|couldn't|still fail\w*)\b", re.I)


def claimed_success(text: str) -> str | None:
    # a negated sentence ("could not fix", "still failing") is not a claim
    if not text or NEGATION.search(text):
        return None
    m = CLAIM.search(text)
    return m.group(0) if m else None


def parse_summary(output: str) -> tuple[int, int]:
    jest = re.search(r"Tests:\s+(?:(\d+) failed, )?(\d+) passed, (\d+) total", output)
    if jest:
        return int(jest[2]), int(jest[3])
    if re.search(r"\bno tests ran\b", output):  # pytest exit 5: every test file gone or skipped
        return 0, 0
    nums = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|errors?)\b", output)}
    if "passed" not in nums and "failed" not in nums and "error" not in nums and "errors" not in nums:
        return -1, -1
    passed = nums.get("passed", 0)
    return passed, passed + nums.get("failed", 0) + nums.get("error", 0) + nums.get("errors", 0)


def _allowed(f: str, globs: list[str]) -> bool:
    # fnmatch '*' spans '/', but "src/**/x" must also match "src/x"
    return any(fnmatch(f, g) or fnmatch(f, g.replace("**/", "")) for g in globs)


def drift(*, passed, total, best_passed, baseline_total, files, allowed,
          diff_hash, seen_hashes, cost_total, budget, guard) -> str | None:
    if cost_total > budget:
        return "over_budget"
    if not guard:
        return None
    if diff_hash in seen_hashes:
        return "loop"
    if total >= 0 and (passed < best_passed or total < baseline_total):
        return "tests_regressed"
    if any(not _allowed(f, allowed) for f in files):
        return "out_of_plan"
    return None
