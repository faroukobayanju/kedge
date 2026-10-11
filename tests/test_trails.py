import json
import subprocess

from kedge import trails

STEPS = [
    {"run_id": "r", "step": 1, "drift": "tests_regressed", "rolled_back": True, "files_changed": ["t.py"],
     "tests_passed": 1, "tests_total": 1, "checkpoint_sha": "abc12345", "false_claim": True, "claim": "Fixed"},
    {"run_id": "r", "step": 2, "drift": None, "rolled_back": False, "files_changed": ["calc.py"],
     "tests_passed": 3, "tests_total": 3, "checkpoint_sha": "def67890", "false_claim": False, "claim": ""},
    {"run_id": "r", "step": 3, "drift": "over_budget", "rolled_back": False, "files_changed": [],
     "tests_passed": 3, "tests_total": 3, "checkpoint_sha": "def67890"},
]


def test_findings_one_per_drift_and_claim():
    f = trails.findings_for(STEPS)
    assert [(x["kind"], x["severity"], x["resolved"]) for x in f] == [
        ("tests_regressed", "high", True), ("false_claim", "high", True)]
    assert "rolled back to abc1234" in f[0]["body"] and 'Claim: "Fixed"' in f[1]["body"]
    assert f[0]["client_id"] == "r-1-tests_regressed"


class P:
    def __init__(self, rc, out=""):
        self.returncode, self.stdout, self.stderr = rc, out, ""


def test_open_trail_falls_back_when_not_enabled(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: P(1))
    assert trails.open_trail("/tmp", "me/r", "kedge/x", "main", "t", "b") is None


def test_open_trail_missing_binary(monkeypatch):
    def boom(*a, **k):
        raise FileNotFoundError("entire")
    monkeypatch.setattr(subprocess, "run", boom)
    assert trails.open_trail("/tmp", "me/r", "kedge/x", "main", "t", "b") is None


def test_post_findings_resolves_recovered(monkeypatch):
    calls = []

    def fake(args, **k):
        calls.append(args)
        return P(0, '{"id": "f1"}')
    monkeypatch.setattr(subprocess, "run", fake)
    assert trails.post_findings("/tmp", "me/r", "kedge/x", STEPS) == 2
    assert sum(1 for c in calls if c[1:4] == ["trail", "finding", "resolve"]) == 2


def test_files_from_explain():
    text = "● Checkpoint X\n## Intent\nfix it\n## Files (2)\n\n- `versions.py`\n- `requirements.txt`\n\n── Transcript"
    assert trails._files_from_explain(text) == ["versions.py", "requirements.txt"]


def test_past_fixes(monkeypatch):
    search = {"results": [{"data": {"matchedCheckpointId": "C1", "repo": "o/r", "displayName": "Fix import"}},
                          {"data": {"matchedCheckpointId": "C1", "repo": "o/r", "displayName": "dup"}},
                          {"data": {"sessionId": "s-no-checkpoint"}},
                          {"data": {"matchedCheckpointId": "C2", "repo": "o/x", "displayName": "Other"}},
                          {"data": {"matchedCheckpointId": "C3", "repo": "o/x", "displayName": "Cheat"}}]}

    class P:
        def __init__(self, out):
            self.stdout, self.returncode = out, 0

    def fake(args, cwd):
        if args[1] == "search":
            return P(json.dumps(search))
        return P({"C1": "## Files (1)\n- `versions.py`\n", "C3": "## Files (1)\n- `tests/test_x.py`\n"}.get(args[2], ""))
    monkeypatch.setattr(trails, "_entire", fake)
    lines = trails.past_fixes("/tmp", "packaging", n=5)
    assert lines == ['Entire checkpoint C1 (o/r): "Fix import", touched [\'versions.py\']',
                     'Entire checkpoint C2 (o/x): "Other"']
