from kedge.checks import parse_summary, drift


def test_pytest_summary():
    assert parse_summary("==== 41 passed, 1 failed in 0.3s ====") == (41, 42)


def test_pytest_errors_counted():
    assert parse_summary("3 passed, 2 errors in 1s") == (3, 5)


def test_jest_summary():
    assert parse_summary("Tests:       1 failed, 41 passed, 42 total") == (41, 42)


def test_unparseable():
    assert parse_summary("ImportError: no module named foo") == (-1, -1)


BASE = dict(passed=5, total=5, best_passed=5, baseline_total=5, files=["src/a.py"],
            allowed=["src/**/*.py"], diff_hash="h1", seen_hashes=set(),
            cost_total=0.1, budget=0.5, guard=True)


def test_clean_step_no_drift():
    assert drift(**BASE) is None


def test_tests_regressed_on_deleted_test_beats_out_of_plan():
    assert drift(**{**BASE, "total": 4, "files": ["tests/test_a.py"]}) == "tests_regressed"


def test_out_of_plan_root_file_matches_globstar():
    assert drift(**{**BASE, "files": ["src/x.py"]}) is None
    assert drift(**{**BASE, "files": ["setup.cfg"]}) == "out_of_plan"


def test_loop():
    assert drift(**{**BASE, "seen_hashes": {"h1"}}) == "loop"


def test_over_budget_even_without_guard():
    assert drift(**{**BASE, "cost_total": 0.6, "guard": False}) == "over_budget"


def test_unparseable_counts_skip_regression():
    assert drift(**{**BASE, "passed": -1, "total": -1}) is None


def test_no_guard_ignores_drift():
    assert drift(**{**BASE, "total": 1, "guard": False}) is None


def test_collection_errors_only_counted():
    # broken import: pytest reports only errors, no passed/failed
    assert parse_summary("2 errors in 0.05s") == (0, 2)


from kedge.checks import claimed_success  # noqa: E402


def test_claims_detected():
    assert claimed_success("Done! All tests pass now.") == "All tests pass"
    assert claimed_success("I fixed the import.") == "fixed"


def test_negated_or_absent_claims_ignored():
    assert claimed_success("Tests still fail; could not fix the import.") is None
    assert claimed_success("Updated requirements.txt") is None
    assert claimed_success("") is None
