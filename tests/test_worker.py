import json
import subprocess

from kedge import worker

JSONL = "\n".join(json.dumps(e) for e in [
    {"type": "step_start", "part": {}},
    {"type": "step_finish", "part": {"cost": 0.01, "tokens": {"input": 10, "output": 5, "reasoning": 1}}},
    {"type": "text", "part": {"text": "first"}},
    {"type": "step_finish", "part": {"cost": 0.02}},
    {"type": "text", "part": {"text": "Created hello.txt."}},
])


def test_parse_opencode_jsonl():
    assert worker.parse_opencode(JSONL) == {"result": "Created hello.txt.", "total_cost_usd": 0.03, "tokens": 16}


def test_parse_opencode_ignores_garbage_lines():
    assert worker.parse_opencode("not json\n" + JSONL)["total_cost_usd"] == 0.03


def test_worker_error_costs_zero(monkeypatch):
    def boom(*a, **k):
        raise subprocess.TimeoutExpired("opencode", 900)
    monkeypatch.setattr(subprocess, "run", boom)
    r = worker.run_edit_step("do it", "/tmp")
    assert r["cost_usd"] == 0.0 and r["error"] == "TimeoutExpired"


def test_make_plan_falls_back_on_bad_json(monkeypatch):
    monkeypatch.setattr(worker, "_agent", lambda prompt, cwd, edit: {"result": "not json", "total_cost_usd": 0.01})
    p = worker.make_plan("bump x", "log", ["package.json"], "/tmp")
    assert p["allowed_files"] == worker.FALLBACK_ALLOWED and p["cost_usd"] == 0.01


def test_make_plan_parses_json_in_prose(monkeypatch):
    out = 'Sure: {"hypothesis": "h", "allowed_files": ["a.py"]} done'
    monkeypatch.setattr(worker, "_agent", lambda prompt, cwd, edit: {"result": out, "total_cost_usd": 0.0})
    assert worker.make_plan("t", "log", [], "/tmp")["allowed_files"] == ["a.py"]


def test_opencode_command_shape(monkeypatch):
    seen = {}

    class P:
        stdout, stderr, returncode = JSONL, "", 0

    def fake(args, **k):
        seen["args"] = args
        return P()
    monkeypatch.setattr(subprocess, "run", fake)
    monkeypatch.delenv("KEDGE_WORKER", raising=False)
    worker._agent("hi", "/tmp", edit=True)
    assert seen["args"][:4] == ["opencode", "run", "--format", "json"] and "--auto" in seen["args"]
    worker._agent("hi", "/tmp", edit=False)
    assert "--auto" not in seen["args"] and ["--agent", "plan"] == seen["args"][4:6]


def test_pinned_opencode_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin")
    for k in ("XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME"):
        monkeypatch.delenv(k, raising=False)
    assert worker.use_pinned_opencode(str(tmp_path)) is False  # nothing installed: env untouched
    import os
    assert os.environ["PATH"] == "/usr/bin"
    (tmp_path / ".tools/opencode/node_modules/.bin").mkdir(parents=True)
    (tmp_path / ".tools/opencode/node_modules/.bin/opencode").write_text("")
    assert worker.use_pinned_opencode(str(tmp_path)) is True
    assert os.environ["PATH"].startswith(str(tmp_path / ".tools/opencode/node_modules/.bin"))
    assert os.environ["XDG_DATA_HOME"] == str(tmp_path / ".tools/opencode/data")


def test_plan_has_steps(monkeypatch):
    monkeypatch.setattr(worker, "_agent", lambda p, c, edit: {"result": '{"hypothesis":"h","allowed_files":["a"],"steps":["s1","s2"]}', "total_cost_usd": 0.0})
    assert worker.make_plan("t", "log", [], "/tmp")["steps"] == ["s1", "s2"]


def test_plan_steps_fallback(monkeypatch):
    monkeypatch.setattr(worker, "_agent", lambda p, c, edit: {"result": '{"hypothesis":"h","allowed_files":["a"]}', "total_cost_usd": 0.0})
    assert worker.make_plan("t", "log", [], "/tmp")["steps"] == ["make the failing tests pass"]


def test_replan_includes_notes(monkeypatch):
    seen = {}

    def fake(prompt, cwd, edit):
        seen["prompt"] = prompt
        return {"result": '{"hypothesis":"h2","allowed_files":["b"],"steps":["x"]}', "total_cost_usd": 0.01}
    monkeypatch.setattr(worker, "_agent", fake)
    p = worker.replan({"hypothesis": "h1", "allowed_files": ["a"], "steps": ["s"]}, ["Do not delete tests."], "/tmp")
    assert p["hypothesis"] == "h2" and "Do not delete tests." in seen["prompt"] and "h1" in seen["prompt"]
