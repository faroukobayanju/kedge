"""Entire Trails: open a trail (which opens the draft PR) and post each drift as a finding.

Falls back to a plain draft PR when Trails is not enabled for the repo (early access).
"""
import json
import subprocess

from kedge.worker import TESTLIKE

SEVERITY = {"tests_regressed": "high", "false_claim": "high", "out_of_plan": "medium",
            "verify_failed": "medium", "loop": "low"}
WHAT = {"tests_regressed": "Agent reduced passing/total tests (deleted or skipped tests).",
        "out_of_plan": "Agent edited files outside the plan.",
        "loop": "Agent repeated an attempt that had already been rolled back.",
        "verify_failed": "Tests passed once but failed or lost tests on re-run.",
        "false_claim": "Agent claimed success but the tests disagreed."}


def _entire(args, cwd) -> subprocess.CompletedProcess:
    return subprocess.run(["entire", *args], cwd=cwd, capture_output=True, text=True, timeout=60)


def open_trail(cwd, fork, branch, base, title, body) -> str | None:
    """Create the trail; None means Trails is unavailable and the caller should open a draft PR."""
    try:
        p = _entire(["trail", "create", "--repo", f"gh/{fork}", "--branch", branch, "--base", base,
                     "--title", f"[kedge] {title}", "--body", body, "--type", "bug"], cwd)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode != 0:
        return None
    out = p.stdout.strip()
    return out.splitlines()[-1] if out else branch


def findings_for(steps) -> list[dict]:
    """One finding per caught drift or false claim; recovered drifts are marked resolved."""
    out = []
    for s in steps:
        kinds = [s["drift"]] if s.get("drift") and s["drift"] != "over_budget" else []
        if s.get("false_claim"):
            kinds.append("false_claim")
        for k in kinds:
            body = f"{WHAT[k]} Step {s['step']}: files {s['files_changed']}, tests {s['tests_passed']}/{s['tests_total']}."
            if k == "false_claim":
                body += f' Claim: "{s["claim"]}".'
            if s.get("rolled_back"):
                body += f" Kedge rolled back to {s['checkpoint_sha'][:7]} and retried."
            out.append({"kind": k, "severity": SEVERITY[k], "body": body,
                        "client_id": f"{s['run_id']}-{s['step']}-{k}", "resolved": bool(s.get("rolled_back"))})
    return out


def post_findings(cwd, fork, branch, steps) -> int:
    posted = 0
    for f in findings_for(steps):
        p = _entire(["trail", "finding", "add", "--repo", f"gh/{fork}", "--branch", branch, "--severity",
                     f["severity"], "--body", f["body"], "--client-id", f["client_id"], "--json"], cwd)
        if p.returncode != 0:
            continue
        posted += 1
        if f["resolved"]:
            try:
                fid = json.loads(p.stdout).get("id")
            except json.JSONDecodeError:
                fid = None
            if fid:
                _entire(["trail", "finding", "resolve", "--repo", f"gh/{fork}", "--branch", branch, fid,
                         "-m", "Kedge recovered: rolled back and retried"], cwd)
    return posted


def _files_from_explain(text) -> list[str]:
    """`## Files (N)` section of `entire checkpoint explain`: lines like "- `versions.py`"."""
    out, inside = [], False
    for line in text.splitlines():
        if line.startswith("## Files"):
            inside = True
            continue
        if inside:
            if line.startswith("- "):
                out.append(line[2:].strip().strip("`"))
            elif line.strip():
                break
    return out


def past_fixes(cwd, query, n=2) -> list[str]:
    """Entire as fix memory: past agent checkpoints for the same failure, and the files each one touched."""
    try:
        p = _entire(["checkpoint", "search", query, "--all-repos"], cwd)
        results = json.loads(p.stdout).get("results", [])
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return []
    out, seen = [], set()
    for r in results:
        d = r.get("data", {})
        cp = d.get("matchedCheckpointId")
        if not cp or cp in seen:
            continue
        seen.add(cp)
        try:
            files = _files_from_explain(_entire(["checkpoint", "explain", cp], cwd).stdout)
        except (OSError, subprocess.TimeoutExpired):
            files = []
        if any(TESTLIKE.search(f) for f in files):  # a "fix" that touched tests may be a cheat; don't teach it
            continue
        out.append(f'Entire checkpoint {cp} ({d.get("repo", "?")}): "{d.get("displayName", "")}"'
                   + (f", touched {files}" if files else ""))
        if len(out) >= n:
            break
    return out
