import subprocess

from kedge import gitgh


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for k, v in [("user.email", "k@k"), ("user.name", "k")]:
        subprocess.run(["git", "-C", str(tmp_path), "config", k, v], check=True)
    (tmp_path / "a.py").write_text("x = 1\n")
    gitgh.sh(["git", "add", "-A"], tmp_path)
    gitgh.sh(["git", "commit", "-qm", "init"], tmp_path)
    return str(tmp_path)


def test_changed_files_sees_edit_new_and_delete(tmp_path):
    cwd = _repo(tmp_path)
    (tmp_path / "a.py").unlink()
    (tmp_path / "b.py").write_text("y\n")
    assert sorted(gitgh.changed_files(cwd)) == ["a.py", "b.py"]


def test_reset_restores_and_hash_changes(tmp_path):
    cwd = _repo(tmp_path)
    good = gitgh.head(cwd)
    clean = gitgh.diff_hash(cwd)
    (tmp_path / "a.py").write_text("x = 2\n")
    (tmp_path / "c.py").write_text("z\n")
    assert gitgh.diff_hash(cwd) != clean
    gitgh.reset(cwd, good)
    assert gitgh.changed_files(cwd) == [] and gitgh.diff_hash(cwd) == clean


def test_commit_returns_sha(tmp_path):
    cwd = _repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 3\n")
    sha, _ = gitgh.commit(cwd, "step")
    assert sha == gitgh.head(cwd)


def test_run_tests_parses(tmp_path):
    ok, passed, total = gitgh.run_tests(str(tmp_path), "echo '2 passed, 1 failed'; exit 1")
    assert (ok, passed, total) == (False, 2, 3)


def test_excluded_paths_ignored_and_survive_reset(tmp_path):
    cwd = _repo(tmp_path)
    good = gitgh.head(cwd)
    gitgh.exclude(cwd, [".entire/", ".opencode/"])
    (tmp_path / ".entire").mkdir()
    (tmp_path / ".entire" / "settings.json").write_text("{}")
    assert gitgh.changed_files(cwd) == []
    (tmp_path / "junk.py").write_text("x\n")
    gitgh.reset(cwd, good)
    assert (tmp_path / ".entire" / "settings.json").exists() and not (tmp_path / "junk.py").exists()


def test_test_output_returns_tail(tmp_path):
    out = gitgh.test_output(str(tmp_path), "echo line1; echo 'E   ImportError: boom'; exit 1")
    assert "ImportError: boom" in out


def test_trim_log_keeps_errors_with_context():
    log = "\n".join([f"noise {i}" for i in range(500)] + ["setup ok", "a", "E   ImportError: no module mathx", "b", "c"]
                    + [f"noise2 {i}" for i in range(500)] + ["FAILED tests/test_a.py::test_1"])
    out = gitgh.trim_log(log).splitlines()
    assert "E   ImportError: no module mathx" in out and "FAILED tests/test_a.py::test_1" in out
    assert "a" in out and "b" in out and "noise 0" not in out and len(out) <= 60


def test_trim_log_fallback_tail():
    out = gitgh.trim_log("\n".join(f"line {i}" for i in range(100))).splitlines()
    assert out[-1] == "line 99" and len(out) == 60


def test_wait_ci_maps_exit_codes(monkeypatch):
    class R:
        def __init__(self, rc, out=""): self.returncode, self.stdout, self.stderr = rc, out, ""
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: R(0))
    assert gitgh.wait_ci("u") == "passed"
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: R(1))
    assert gitgh.wait_ci("u") == "failed"
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: R(1, "no checks reported"))
    assert gitgh.wait_ci("u") == "no checks"
    def slow(*a, **k): raise subprocess.TimeoutExpired("gh", 1)
    monkeypatch.setattr(subprocess, "run", slow)
    assert gitgh.wait_ci("u") == "timeout"
