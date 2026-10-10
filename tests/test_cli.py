from kedge.cli import main


def test_bad_url_exits_2():
    assert main(["run", "not-a-url"]) == 2


def test_target_not_allowlisted_exits_2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "targets.json").write_text("[]")
    assert main(["run", "https://github.com/o/r/pull/1"]) == 2
