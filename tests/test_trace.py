from kedge import trace


def test_no_key_is_noop(monkeypatch):
    monkeypatch.delenv("NEATLOGS_API_KEY", raising=False)
    trace.start("r1", {"guard": "on"})
    with trace.run_span("r1", "u"):
        trace.record({"step": 1, "action": "worker", "drift": None, "files_changed": ["a"]})
    trace.finish()
    assert trace.trace_url("definitely-not-a-run") == "unavailable"
