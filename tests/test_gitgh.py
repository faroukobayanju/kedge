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
