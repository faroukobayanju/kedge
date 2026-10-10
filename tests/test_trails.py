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
