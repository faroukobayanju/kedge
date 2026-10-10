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
