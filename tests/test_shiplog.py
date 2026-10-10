from kedge.shiplog import footer, header, line


def test_header():
    assert header("dependabot/lodash-5", 0.5) == "⚓ kedge  dependabot/lodash-5  ·  budget $0.50"


def test_ok_step():
    r = {"step": 1, "action": "worker", "files_changed": ["a", "b"], "tests_passed": 41, "tests_total": 42,
         "drift": None, "rolled_back": False, "checkpoint_sha": "9f3c1e2aa"}
    assert line(r) == "⛵ step 1  edited 2 files · tests 41/42"


def test_drift_step_two_lines():
    r = {"step": 1, "action": "worker", "files_changed": ["tests/test_u.py"], "tests_passed": 38, "tests_total": 38,
         "drift": "tests_regressed", "rolled_back": True, "checkpoint_sha": "9f3c1e2aa"}
    assert line(r) == ("🌊 DRIFT  tests_regressed · tests 38/38 · tests/test_u.py\n"
                       "⚓ hauled back to 9f3c1e2")


def test_replan_and_budget():
    assert line({"step": 2, "action": "replan"}) == "🧭 replanning after 2 drifts"
    r = {"step": 3, "action": "worker", "files_changed": [], "tests_passed": 1, "tests_total": 2,
         "drift": "over_budget", "rolled_back": False, "checkpoint_sha": "abc1234"}
    assert line(r) == "💸 out of budget, dropping anchor"


def test_footer():
    res = {"status": "green", "cost_usd_total": 0.214, "draft_pr": "https://github.com/me/r/pull/12"}
    assert footer(res, "https://n/t/1") == "🏁 green · $0.21 · https://github.com/me/r/pull/12 · trace https://n/t/1"


def test_false_claim_line():
    r = {"step": 2, "action": "worker", "files_changed": ["a"], "tests_passed": 38, "tests_total": 42,
         "drift": None, "rolled_back": False, "checkpoint_sha": "abc1234",
         "false_claim": True, "claim": "All tests pass"}
    assert line(r) == ('🤥 agent claimed "All tests pass", reality 38/42\n'
                       "⛵ step 2  edited 1 files · tests 38/42")
