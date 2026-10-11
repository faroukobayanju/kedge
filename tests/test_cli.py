from kedge import cli
from kedge.cli import main


def test_bad_url_exits_2():
    assert main(["run", "not-a-url"]) == 2


def test_target_not_allowlisted_exits_2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "targets.json").write_text("[]")
    assert main(["run", "https://github.com/o/r/pull/1"]) == 2


def test_load_dotenv_does_not_override(tmp_path, monkeypatch):
    from kedge.cli import load_dotenv
    (tmp_path / ".env").write_text("# comment\nKEDGE_T1=from_file\nKEDGE_T2=from_file\n")
    monkeypatch.setenv("KEDGE_T2", "real")
    monkeypatch.delenv("KEDGE_T1", raising=False)
    load_dotenv(str(tmp_path / ".env"))
    import os
    assert os.environ["KEDGE_T1"] == "from_file" and os.environ["KEDGE_T2"] == "real"
    monkeypatch.delenv("KEDGE_T1")


def test_resume_without_state_exits_2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["resume", "nope"]) == 2


def test_dep_of():
    assert cli.dep_of("build(deps): bump packaging from 21.3 to 24.2", "dependabot/pip/packaging-24.2") == "packaging"
    assert cli.dep_of("chore(deps): update all", "renovate/fast-uri-4.x") == "fast-uri-4.x"


def test_budget_comes_from_cfo_model_unless_given():
    assert cli.budget_or_cfo(None) == 0.45
    assert cli.budget_or_cfo(2.0) == 2.0


def _step(n, files, cp="", rolled_back=False, action="worker"):
    return {"step": n, "action": action, "files_changed": files, "rolled_back": rolled_back, "entire_checkpoint": cp}


def test_proof_needs_trace_and_checkpoint_on_every_kept_commit():
    steps = [_step(1, ["tests/t.py"], rolled_back=True), _step(2, ["v.py"], cp="CP1"), _step(3, [])]
    assert cli.proof_of(steps, "T1") == {"trace": "T1", "checkpoints": ["CP1"], "missing": []}
    p = cli.proof_of([_step(1, ["v.py"])], "unavailable")
    assert p["missing"] == ["neatlogs trace", "Entire checkpoint on step 1"]


def test_prove_refuses_runs_that_are_not_unproven(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "runs" / "r1"
    d.mkdir(parents=True)
    (d / "meta.json").write_text("{}")
    (d / "result.json").write_text('{"status": "green"}')
    assert cli.main(["prove", "r1"]) == 2
