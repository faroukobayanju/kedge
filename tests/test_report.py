import json

from kedge.report import render

META = {"run_id": "r1", "pr_url": "https://x/pull/1", "status": "green", "cost_usd_total": 0.09,
        "rollbacks": 1, "trace_url": "https://neatlogs/t/1", "entire_explain": "checkpoint abc"}


def test_render_both(tmp_path):
    recs = [{"step": 1, "action": "worker", "files_changed": ["tests/test_a.py"], "tests_passed": 2,
             "tests_total": 2, "cost_usd": 0.05, "drift": "tests_regressed", "rolled_back": True},
            {"step": 2, "action": "worker", "files_changed": ["calc.py"], "tests_passed": 3,
             "tests_total": 3, "cost_usd": 0.04, "drift": None, "rolled_back": False}]
    (tmp_path / "steps.jsonl").write_text("\n".join(json.dumps(r) for r in recs))
    html, md = render(str(tmp_path), META)
    h, m = open(html).read(), open(md).read()
    assert "tests_regressed" in h and "<table" in h and "https://neatlogs/t/1" in h
    assert "| 1 |" in m and "rolled back" in m and "checkpoint abc" in m


def test_render_without_steps_file(tmp_path):
    html, _ = render(str(tmp_path), META)
    assert "Kedge run r1" in open(html).read()


def test_ci_status_shown(tmp_path):
    (tmp_path / "steps.jsonl").write_text("")
    meta = {"run_id": "r", "pr_url": "u", "status": "green", "cost_usd_total": 0, "rollbacks": 0,
            "trace_url": "t", "entire_explain": "e", "ci_status": "passed"}
    h, m = render(str(tmp_path), meta)
    assert "CI: passed" in open(h).read() and "CI: passed" in open(m).read()
