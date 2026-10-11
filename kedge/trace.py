"""neatlogs: one trace per run, Kedge's memory across runs, and the verdict on each run.

- Every step span carries a compact JSON summary as its output (neatlogs keeps span input/output previews,
  not custom attributes), so later runs can read what happened.
- memory() reads past runs on the same repo or dependency back from neatlogs before planning.
- verdict() writes Kedge's judgement (drifts caught, false claims) onto the trace as feedback.
"""
import json
import os
import subprocess
import time
import uuid
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
        s.set_attribute("input.value", pr_url)
        yield s


def step_summary(rec) -> dict:
    """What a future run needs to know about this step."""
    return {"step": rec["step"], "action": rec["action"], "drift": rec.get("drift"),
            "tests": f"{rec.get('tests_passed', -1)}/{rec.get('tests_total', -1)}",
            "files": rec.get("files_changed", []), "rolled_back": rec.get("rolled_back", False),
            "false_claim": rec.get("false_claim", False), "cost_usd": rec.get("cost_usd", 0.0)}


def record(rec, prompt="") -> None:
    if not _on:
        return
    import neatlogs
    kind = "AGENT" if rec["action"] == "replan" else "TOOL"
    with neatlogs.trace(f"step {rec['step']} {rec['action']}", kind=kind) as s:
        for k, v in rec.items():
            s.set_attribute(f"kedge.{k}", json.dumps(v) if isinstance(v, (list, dict)) or v is None else v)
        s.set_attribute("input.value", prompt[-2000:] or f"step {rec['step']}")
        s.set_attribute("output.value", json.dumps(step_summary(rec)))


def summarize_run(span, res) -> None:
    """Root span output: the outcome, and which files the green step touched."""
    if span is None:
        return
    won = next((s["files_changed"] for s in reversed(res["steps"]) if s["files_changed"] and not s.get("rolled_back")), [])
    span.set_attribute("output.value", json.dumps({"status": res["status"], "rollbacks": res["rollbacks"],
                                                    "green_files": won, "cost_usd": round(res["cost_usd_total"], 4)}))


def finish() -> None:
    if _on:
        import neatlogs
        neatlogs.flush()
        neatlogs.shutdown()


def _cli(args, stdin=None):
    """Run the neatlogs npm CLI (user token, never the ingest key) and parse its JSON, or None."""
    try:
        env = {k: v for k, v in os.environ.items() if k != "NEATLOGS_API_KEY"}
        # the Python SDK also installs a `neatlogs` script into the venv; use the npm CLI explicitly
        exe = os.path.expanduser(os.environ.get("NEATLOGS_CLI", "~/.local/bin/neatlogs"))
        cmd = [exe, "--host", os.environ.get("NEATLOGS_HOST", "https://app.neatlogs.com"),
               "--profile", os.environ.get("NEATLOGS_PROFILE", "setup-https---app-neatlogs-com")]
        if os.environ.get("NEATLOGS_PROJECT_ID"):
            cmd += ["--project", os.environ["NEATLOGS_PROJECT_ID"]]
        p = subprocess.run(cmd + args + ["--json"], input=stdin, capture_output=True, text=True, timeout=30, env=env)
        return json.loads(p.stdout)
    except Exception:
        return None


def _traces():
    d = _cli(["traces", "list", "--workflow", WORKFLOW, "--limit", "50"]) or {}
    return d.get("data", {}).get("traces", [])


def find_trace(resp, run_id) -> str:
    for t in resp.get("data", {}).get("traces", []):
        if f"run_id:{run_id}" in t.get("tags", []):
            return t["traceId"]
    return "unavailable"


def trace_url(run_id, wait_s=0, poll_s=20) -> str:
    """The run's trace ID, retried for up to wait_s while neatlogs ingests it."""
    deadline = time.time() + wait_s
    while True:
        found = find_trace({"data": {"traces": _traces()}}, run_id)
        if found != "unavailable" or time.time() >= deadline:
            return found
        time.sleep(poll_s)


def memory_from(traces, spans_of, repo, dep, run_id, n=3) -> list[str]:
    """Lines describing past runs on the same repo or dependency, newest first."""
    out = []
    for t in traces:
        tags = t.get("tags", [])
        if f"run_id:{run_id}" in tags or not (f"repo:{repo}" in tags or (dep and f"dep:{dep}" in tags)):
            continue
        if "guard:off" in tags:  # an unguarded "green" may have cheated; never offer it as a fix
            continue
        steps = []
        for s in spans_of(t["traceId"]):
            try:
                steps.append(json.loads(s["output"]["preview"]))
            except (KeyError, TypeError, ValueError):
                continue
        drifted = [f"step {s['step']} {s['drift']} on {s.get('files', [])}" for s in steps if s.get("drift")]
        won = [s for s in steps if s.get("status") == "green"]
        line = next((t2 for t2 in tags if t2.startswith("run_id:")), "run")
        if drifted:
            line += "; drifted: " + "; ".join(drifted)
        if won:
            line += f"; went green editing {won[0].get('green_files', [])}"
        if drifted or won:
            out.append(line)
        if len(out) >= n:
            break
    return out


def memory(repo, dep, run_id) -> list[str]:
    def spans_of(trace_id):
        d = _cli(["traces", "raw-spans", trace_id]) or {}
        return d.get("data", {}).get("spans", [])
    return memory_from(_traces(), spans_of, repo, dep, run_id)


def verdict_body(steps, status) -> dict | None:
    kinds = sorted({s["drift"] for s in steps if s.get("drift") and s["drift"] != "over_budget"}
                   | {"false_claim" for s in steps if s.get("false_claim")})
    lines = [f"step {s['step']}: {s['drift'] or 'false claim'} · files {s['files_changed']} · tests "
             f"{s['tests_passed']}/{s['tests_total']}" + (" · rolled back" if s.get("rolled_back") else "")
             for s in steps if (s.get("drift") and s["drift"] != "over_budget") or s.get("false_claim")]
    if not lines and status != "green":
        return None
    rating = 100 if status == "green" and not lines else (-30 if status == "green" else -100)
    return {"rating": rating, "issueTypes": kinds,
            "comment": f"Kedge verdict: {status}. " + ("Caught: " + "; ".join(lines) if lines else "No drift.")}


def verdict(trace_id, steps, status) -> bool:
    """Write Kedge's judgement onto the trace as feedback, so the trace reads as a review."""
    body = verdict_body(steps, status)
    if not body or trace_id == "unavailable":
        return False
    d = _cli(["feedback", "create", "--trace", trace_id, "--body-stdin", "--idempotency-key", str(uuid.uuid4())],
             stdin=json.dumps(body))
    return bool(d and d.get("success"))
