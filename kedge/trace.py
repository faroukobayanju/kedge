import json
import os
import subprocess
from contextlib import contextmanager

# neatlogs uses a private OpenTelemetry provider, so only the neatlogs API exports spans.
_on = False
WORKFLOW = "dependency-pr-repair"


def start(run_id, tags) -> None:
    global _on
    if not os.environ.get("NEATLOGS_API_KEY"):
        return
    import neatlogs
    neatlogs.init(api_key=os.environ["NEATLOGS_API_KEY"], endpoint="https://ingest.neatlogs.com",
                  workflow_name=WORKFLOW, tags=[f"{k}:{v}" for k, v in {"run_id": run_id, **tags}.items()])
    _on = True


@contextmanager
def run_span(run_id, pr_url):
    """Root WORKFLOW span around one run, so step spans nest under it."""
    if not _on:
        yield None
        return
    import neatlogs
    with neatlogs.trace(f"kedge run {run_id}", kind="WORKFLOW") as s:
        s.set_attribute("kedge.run_id", run_id)
        s.set_attribute("kedge.pr_url", pr_url)
        yield s


def record(rec) -> None:
    if not _on:
        return
    import neatlogs
    kind = "AGENT" if rec["action"] == "replan" else "TOOL"
    with neatlogs.trace(f"step {rec['step']} {rec['action']}", kind=kind) as s:
        for k, v in rec.items():
            s.set_attribute(f"kedge.{k}", json.dumps(v) if isinstance(v, (list, dict)) or v is None else v)


def finish() -> None:
    if _on:
        import neatlogs
        neatlogs.flush()
        neatlogs.shutdown()


def find_trace(resp, run_id) -> str:
    for t in resp.get("data", {}).get("traces", []):
        if f"run_id:{run_id}" in t.get("tags", []):
            return t["traceId"]
    return "unavailable"


def trace_url(run_id) -> str:
    # Readback uses the neatlogs CLI with NEATLOGS_TOKEN, never the ingest key.
    # Shape per neatlogs OpenAPI: {"data": {"traces": [{"traceId", "tags", ...}]}}; no URL field.
    try:
        env = {k: v for k, v in os.environ.items() if k != "NEATLOGS_API_KEY"}
        out = subprocess.run(["neatlogs", "traces", "list", "--workflow", WORKFLOW, "--limit", "50", "--json"],
                             capture_output=True, text=True, timeout=20, env=env).stdout
        return find_trace(json.loads(out), run_id)
    except Exception:
        return "unavailable"
