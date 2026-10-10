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
