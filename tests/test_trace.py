from kedge import trace


def test_no_key_is_noop(monkeypatch):
    monkeypatch.delenv("NEATLOGS_API_KEY", raising=False)
    trace.start("r1", {"guard": "on"})
    with trace.run_span("r1", "u"):
        trace.record({"step": 1, "action": "worker", "drift": None, "files_changed": ["a"]})
    trace.finish()
    assert trace.trace_url("definitely-not-a-run") == "unavailable"


def test_find_trace_matches_run_tag():
    resp = {"success": True, "data": {"page": 1, "traces": [
        {"traceId": "t1", "tags": ["run_id:other"]},
        {"traceId": "t2", "tags": ["guard:on", "run_id:r9"]}]}}
    assert trace.find_trace(resp, "r9") == "t2"
    assert trace.find_trace(resp, "nope") == "unavailable"
    assert trace.find_trace({}, "r9") == "unavailable"


def test_memory_reads_past_runs_on_same_repo():
    traces = [
        {"traceId": "now", "tags": ["run_id:r-now", "repo:o/r"]},
        {"traceId": "t1", "tags": ["run_id:r1", "repo:o/r", "dep:packaging"]},
        {"traceId": "t2", "tags": ["run_id:r2", "repo:other/x"]},
        {"traceId": "t3", "tags": ["run_id:r3", "repo:z/z", "dep:packaging"]},
        {"traceId": "t4", "tags": ["run_id:r4", "repo:o/r", "guard:off"]},
    ]
    spans = {
        "t1": [{"output": {"preview": '{"step": 1, "drift": "out_of_plan", "files": ["tests/t.py"]}'}},
               {"output": {"preview": '{"status": "green", "green_files": ["versions.py"]}'}}],
        "t2": [{"output": {"preview": '{"step": 1, "drift": "loop", "files": []}'}}],
        "t3": [{"output": {"preview": "not json"}}, {"output": {"preview": '{"status": "green", "green_files": ["a.py"]}'}}],
        "t4": [{"output": {"preview": '{"status": "green", "green_files": ["tests/t.py"]}'}}],
    }
    lines = trace.memory_from(traces, lambda t: spans[t], "o/r", "packaging", "r-now")
    assert len(lines) == 2  # current run, unrelated repo and the unguarded run are skipped
    assert "out_of_plan" in lines[0] and "versions.py" in lines[0]
    assert lines[1].startswith("run_id:r3") and "a.py" in lines[1]


def test_verdict_body():
    steps = [{"step": 1, "drift": "out_of_plan", "files_changed": ["t.py"], "tests_passed": 2, "tests_total": 2,
              "rolled_back": True, "false_claim": False},
             {"step": 2, "drift": None, "files_changed": ["v.py"], "tests_passed": 5, "tests_total": 5,
              "rolled_back": False, "false_claim": False}]
    b = trace.verdict_body(steps, "green")
    assert b["issueTypes"] == ["out_of_plan"] and b["rating"] == -30 and "rolled back" in b["comment"]
    assert trace.verdict_body([], "green")["rating"] == 100
    assert trace.verdict_body([], "gave_up") is None
