import subprocess
import sys

from kedge import gitgh
from kedge.supervisor import loop

TEST_CMD = f"{sys.executable} -m pytest -q -p no:cacheprovider"
PLAN = {"hypothesis": "fix import", "allowed_files": ["calc.py"], "cost_usd": 0.0}


def fixture(tmp_path, broken=True):
    tmp_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for k, v in [("user.email", "k@k"), ("user.name", "k")]:
        subprocess.run(["git", "-C", str(tmp_path), "config", k, v], check=True)
    (tmp_path / "calc.py").write_text("from mathx import add\n" if broken else "def add(a, b): return a + b\n")
    # two test files: chaos deletes test_a.py (sorted first), test_b.py keeps pytest output parseable
    (tmp_path / "test_a.py").write_text(
        "from calc import add\n"
        "def test_1(): assert add(1, 1) == 2\n"
        "def test_2(): assert add(0, 0) == 0\n")
    (tmp_path / "test_b.py").write_text(
        "from calc import add\n"
        "def test_3(): assert add(2, 3) == 5\n")
    gitgh.sh(["git", "add", "-A"], tmp_path)
    gitgh.sh(["git", "commit", "-qm", "init"], tmp_path)
    return str(tmp_path)


def fixing_worker(prompt, cwd):
    open(f"{cwd}/calc.py", "w").write("def add(a, b): return a + b\n")
    return {"cost_usd": 0.05, "text": "fixed", "error": None}


def test_green_in_one_step(tmp_path):
    r = loop(fixture(tmp_path), TEST_CMD, PLAN, "fix it", worker=fixing_worker)
    assert r["status"] == "green" and r["rollbacks"] == 0 and len(r["steps"]) == 1


def test_chaos_caught_and_recovered(tmp_path):
    r = loop(fixture(tmp_path), TEST_CMD, PLAN, "fix it", worker=fixing_worker, chaos=True)
    assert r["steps"][0]["drift"] == "tests_regressed" and r["steps"][0]["rolled_back"]
    assert r["status"] == "green" and r["steps"][-1]["tests_total"] == 3


def test_chaos_without_guard_ships_fewer_tests(tmp_path):
    r = loop(fixture(tmp_path), TEST_CMD, PLAN, "fix it", worker=fixing_worker, chaos=True, guard=False)
    assert r["status"] == "green" and r["steps"][-1]["tests_total"] < 3


def test_noop_worker_gives_up_after_max_steps(tmp_path):
    def noop(p, c):
        return {"cost_usd": 0.01, "text": "", "error": None}
    r = loop(fixture(tmp_path), TEST_CMD, PLAN, "fix it", worker=noop, max_steps=3)
    assert r["status"] == "gave_up" and len(r["steps"]) == 3 and r["rollbacks"] == 0


def test_budget_stops_worker_calls(tmp_path):
    calls = []

    def pricey(p, c):
        calls.append(1)
        return {"cost_usd": 0.4, "text": "", "error": None}
    r = loop(fixture(tmp_path), TEST_CMD, PLAN, "fix it", worker=pricey, budget=0.5)
    assert r["status"] == "gave_up" and len(calls) == 2 and r["steps"][-1]["drift"] == "over_budget"


def test_already_green(tmp_path):
    r = loop(fixture(tmp_path, broken=False), TEST_CMD, PLAN, "fix it", worker=fixing_worker)
    assert r["status"] == "already_green" and r["steps"] == []


def test_worker_error_logged(tmp_path):
    def err(p, c):
        return {"cost_usd": 0.0, "text": "", "error": "TimeoutExpired"}
    r = loop(fixture(tmp_path), TEST_CMD, PLAN, "fix it", worker=err, max_steps=2)
    assert [s["action"] for s in r["steps"]] == ["worker_error", "worker_error"]
