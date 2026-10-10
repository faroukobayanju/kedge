def header(branch, budget) -> str:
    return f"⚓ kedge  {branch}  ·  budget ${budget:.2f}"


def _line(rec) -> str:
    if rec["action"] == "replan":
        return "🧭 replanning after 2 drifts"
    if rec.get("drift") == "over_budget":
        return "💸 out of budget, dropping anchor"
    tests = f"tests {rec['tests_passed']}/{rec['tests_total']}"
    if rec.get("drift"):
        files = ", ".join(rec["files_changed"][:3])
        return f"🌊 DRIFT  {rec['drift']} · {tests} · {files}\n⚓ hauled back to {rec['checkpoint_sha'][:7]}"
    if rec["action"] == "worker_error":
        return f"⛈  step {rec['step']}  worker error · {tests}"
    return f"⛵ step {rec['step']}  edited {len(rec['files_changed'])} files · {tests}"


def line(rec) -> str:
    base = _line(rec)
    if rec.get("false_claim"):
        return f'🤥 agent claimed "{rec["claim"]}", reality {rec["tests_passed"]}/{rec["tests_total"]}\n' + base
    return base


def footer(res, trace_url) -> str:
    where = res.get("draft_pr") or "no PR"
    return f"🏁 {res['status']} · ${res['cost_usd_total']:.2f} · {where} · trace {trace_url}"
