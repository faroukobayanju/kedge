import json

from kedge.supervisor import decide_next, loop
from tests.test_loop import PLAN, TEST_CMD, fixing_worker, fixture


def test_resume_after_crash(tmp_path):
    cwd = fixture(tmp_path / "repo")
    saved = {}

    def crashing(prompt, c):
        raise KeyboardInterrupt
    try:
        loop(cwd, TEST_CMD, PLAN, "fix", worker=crashing, save=lambda s: saved.update(json.loads(json.dumps(s))))
    except KeyboardInterrupt:
        pass
    assert saved["step"] == 1 and saved["good"]
    r = loop(cwd, TEST_CMD, PLAN, "fix", worker=fixing_worker, state=saved)
    assert r["status"] == "green"


def test_decide_next():
    rb = {"rolled_back": True, "drift": "loop"}
    assert decide_next([], 3) == "edit"
    assert decide_next([rb, rb], 3) == "replan"
    assert decide_next([rb, rb, {"action": "replan", "rolled_back": False}], 3) == "edit"
    assert decide_next([rb] * 4, 3) == "give_up"
    assert decide_next([{"drift": "over_budget", "rolled_back": False}], 3) == "give_up"


def test_replan_after_two_rollbacks(tmp_path):
    calls = {"n": 0}

    def drifting_then_fixing(prompt, cwd):
        calls["n"] += 1
        if calls["n"] <= 2:  # two out-of-plan edits in a row
            open(f"{cwd}/STRAY.md", "w").write("x\n")
            return {"cost_usd": 0.0, "text": "", "error": None}
        return fixing_worker(prompt, cwd)

    def replanner(plan, notes, cwd):
        return {**plan, "steps": ["fix calc.py"], "cost_usd": 0.0}
    r = loop(fixture(tmp_path), TEST_CMD, PLAN, "fix", worker=drifting_then_fixing, replanner=replanner)
    assert [s["action"] for s in r["steps"]] == ["worker", "worker", "replan", "worker"]
    assert r["status"] == "green" and r["rollbacks"] == 2


def test_escalation_switches_model_and_resets_cost_history(tmp_path, monkeypatch):
    monkeypatch.setenv("KEDGE_MODEL", "litellm/claude-haiku")
    monkeypatch.setenv("KEDGE_ESCALATE_MODEL", "litellm/claude-sonnet-4.6")
    seen = []

    def stray(prompt, cwd):
        import os
        seen.append(os.environ["KEDGE_MODEL"])
        open(os.path.join(cwd, "STRAY.md"), "w").write(str(len(seen)))  # out of plan every time
        return {"cost_usd": 0.01, "text": "", "error": None}
    r = loop(fixture(tmp_path), TEST_CMD, PLAN, "fix", worker=stray, replanner=lambda p, n, c: {**p, "cost_usd": 0.0},
             max_steps=3, budget=5.0)
    assert seen[:2] == ["litellm/claude-haiku"] * 2 and seen[2] == "litellm/claude-sonnet-4.6"
    assert any(s["action"] == "replan" for s in r["steps"])
