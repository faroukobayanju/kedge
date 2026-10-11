"""`kedge ui`: serve the run dashboard and a read-only JSON view of runs/."""
import json
import os
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

UI_DIR = os.path.join(os.path.dirname(__file__), "ui")
RUN_ID_CHARS = set("0123456789abcdef-")


def _load(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def _steps(run_dir):
    path = os.path.join(run_dir, "steps.jsonl")
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path):
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # a step being written right now
    return out


def _from_report(d) -> dict | None:
    """Runs from before result.json existed: read status and links back from report.md."""
    p = os.path.join(d, "report.md")
    if not os.path.exists(p):
        return None
    text = open(p, encoding="utf-8").read()
    m = re.search(r"^## Kedge run `[^`]+`: (\w+)", text, re.M)
    trace = re.search(r"\[neatlogs trace\]\(([^)]+)\)|neatlogs trace `([^`]+)`", text)
    ci = re.search(r"^CI: ([^·]+?) ·", text, re.M)
    return {"status": m.group(1) if m else "unknown", "trace_url": (trace.group(1) or trace.group(2)) if trace else None,
            "ci_status": ci.group(1).strip() if ci else None, "guard": True, "storm": None}


def run_detail(runs_dir, run_id) -> dict | None:
    if not run_id or not set(run_id) <= RUN_ID_CHARS:  # no path tricks
        return None
    d = os.path.join(runs_dir, run_id)
    if not os.path.isdir(d):
        return None
    meta = _load(os.path.join(d, "meta.json"), {})
    result = _load(os.path.join(d, "result.json")) or _from_report(d)
    steps = _steps(d)
    kw = meta.get("kw", {})
    return {
        "run_id": run_id,
        "pr_url": (result or {}).get("pr_url") or meta.get("pr_url"),
        "title": (meta.get("pr") or {}).get("title", ""),
        "repo": (meta.get("pr") or {}).get("repo", ""),
        "status": (result or {}).get("status", "running"),
        "guard": kw.get("guard", True) if not result else result.get("guard", True),
        "storm": kw.get("storm") if not result else result.get("storm"),
        "cost_usd_total": (result or {}).get("cost_usd_total", steps[-1]["cost_usd_total"] if steps else 0.0),
        "rollbacks": sum(1 for s in steps if s.get("rolled_back")),
        "drifts": sum(1 for s in steps if s.get("drift") and s["drift"] != "over_budget"),
        "false_claims": sum(1 for s in steps if s.get("false_claim")),
        "draft_pr": (result or {}).get("draft_pr"),
        "trace": (result or {}).get("trace_url"),
        "ci_status": (result or {}).get("ci_status"),
        "entire_explain": (result or {}).get("entire_explain", ""),
        "finished_at": (result or {}).get("finished_at"),
        "base_total": meta.get("base_total", -1),
        "plan": _load(os.path.join(d, "plan.json"), {}),
        "steps": steps,
    }


def list_runs(runs_dir) -> list[dict]:
    if not os.path.isdir(runs_dir):
        return []
    ids = sorted((n for n in os.listdir(runs_dir) if os.path.isdir(os.path.join(runs_dir, n))), reverse=True)
    runs = [run_detail(runs_dir, i) for i in ids]
    return [r for r in runs if r and r["pr_url"]]


def make_handler(runs_dir):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=UI_DIR, **k)

        def log_message(self, *a):
            pass

        def _json(self, obj, code=200):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/api/runs":
                return self._json(list_runs(runs_dir))
            if path.startswith("/api/runs/"):
                r = run_detail(runs_dir, path.rsplit("/", 1)[1])
                return self._json(r) if r else self._json({"error": "run not found"}, 404)
            return super().do_GET()
    return Handler


def serve(runs_dir="runs", port=8711) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(os.path.abspath(runs_dir)))
    print(f"⚓ kedge ui on http://127.0.0.1:{port}  (Ctrl+C to stop)")
    httpd.serve_forever()
