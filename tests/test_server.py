import json

from kedge import server


def _run(tmp_path, rid, result=True):
    d = tmp_path / rid
    d.mkdir()
    (d / "meta.json").write_text(json.dumps({"pr_url": "https://github.com/o/r/pull/1",
                                             "pr": {"title": "bump x", "repo": "o/r"},
                                             "kw": {"guard": False, "storm": "delete-test"}}))
    (d / "steps.jsonl").write_text(
        json.dumps({"step": 1, "drift": "tests_regressed", "rolled_back": True, "cost_usd_total": 0.1}) + "\n"
        + '{"step": 2, "drift": null, "rolled_back": false, "false_claim": true, "cost_usd_total": 0.2}\n{"partial')
    if result:
        (d / "result.json").write_text(json.dumps({"status": "green", "pr_url": "https://github.com/o/r/pull/1",
                                                   "draft_pr": "https://x/pull/2", "guard": True, "storm": None,
                                                   "cost_usd_total": 0.2}))


def test_list_and_detail(tmp_path):
    _run(tmp_path, "20261010-2106-37b8")
    _run(tmp_path, "20261010-2200-aaaa", result=False)
    runs = server.list_runs(str(tmp_path))
    assert [r["run_id"] for r in runs] == ["20261010-2200-aaaa", "20261010-2106-37b8"]
    running, done = runs
    assert running["status"] == "running" and running["guard"] is False and running["storm"] == "delete-test"
    assert done["status"] == "green" and done["drifts"] == 1 and done["false_claims"] == 1 and len(done["steps"]) == 2


def test_rejects_path_tricks(tmp_path):
    assert server.run_detail(str(tmp_path), "../etc") is None
    assert server.run_detail(str(tmp_path), "") is None


def test_old_run_status_from_report(tmp_path):
    _run(tmp_path, "20261010-1259-40e9", result=False)
    (tmp_path / "20261010-1259-40e9" / "report.md").write_text(
        "## Kedge run `20261010-1259-40e9`: green\nCI: failed · Cost $0.000 · rollbacks 0 · [neatlogs trace](abc123)\n")
    r = server.run_detail(str(tmp_path), "20261010-1259-40e9")
    assert r["status"] == "green" and r["trace"] == "abc123" and r["ci_status"] == "failed"
