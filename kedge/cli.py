import argparse
import json
import os
import re
import sys
import tempfile
import time
import uuid

from kedge import gitgh, report, supervisor, trace, worker

PROMPT = ("You are fixing a failing dependency-bump PR.\nPR: {title}\nPlan: {hyp}\n"
          "Only edit files matching: {allowed}\nFailure output:\n{log}\n"
          "Do ONE step toward making the tests pass, then stop. Never delete or skip tests.")


def _targets(path="targets.json"):
    return {t["pr_url"]: t for t in json.load(open(path))} if os.path.exists(path) else {}


def run_one(pr_url, test_cmd, fork, *, setup_cmd=None, guard, chaos, budget, max_rollbacks, max_steps) -> dict:
    run_id = time.strftime("%Y%m%d-%H%M") + "-" + uuid.uuid4().hex[:4]
    run_dir = os.path.abspath(os.path.join("runs", run_id))
    os.makedirs(run_dir)
    cwd = os.path.join(tempfile.gettempdir(), "kedge", run_id)
    pr = gitgh.clone_pr(pr_url, cwd)
    agent = "claude-code" if os.environ.get("KEDGE_WORKER") == "claude" else "opencode"
    gitgh.exclude(cwd, [".entire/", ".opencode/", ".claude/", *gitgh.ARTIFACTS])
    if setup_cmd:  # install deps once, not on every test run
        gitgh.sh(["sh", "-c", setup_cmd], cwd, check=False)
    gitgh.sh(["entire", "enable", "--agent", agent], cwd, check=False)
    plugin = os.path.join(cwd, ".opencode", "plugins", "entire.ts")
    if agent == "opencode" and not os.path.exists(plugin):  # seen once: hooks "installed" but plugin file missing
        gitgh.sh(["entire", "enable", "--agent", agent, "--force"], cwd, check=False)
    print(f"entire plugin present: {os.path.exists(plugin)}", file=sys.stderr)
    log_tail = "Local test output:\n" + gitgh.test_output(cwd, test_cmd)
    ci = gitgh.ci_log(pr_url, pr["head"], pr["repo"])
    if ci.strip() and not ci.startswith("(no failed CI"):
        log_tail += "\n\nCI log:\n" + ci
    pr_files = gitgh.sh(["git", "diff", "--name-only", f"origin/{pr['base']}...HEAD"], cwd, check=False).split()
    plan = worker.make_plan(pr["title"], log_tail, pr_files, cwd)
    json.dump(plan, open(os.path.join(run_dir, "plan.json"), "w"))
    trace.start(run_id, {"pr_url": pr_url, "guard": "on" if guard else "off", "chaos": "on" if chaos else "off"})
    steps_f = open(os.path.join(run_dir, "steps.jsonl"), "a")

    def log(rec):
        steps_f.write(json.dumps(rec) + "\n")
        steps_f.flush()
        trace.record(rec)
    prompt = PROMPT.format(title=pr["title"], hyp=plan["hypothesis"], allowed=plan["allowed_files"], log=log_tail)
    with trace.run_span(run_id, pr_url):
        res = supervisor.loop(cwd, test_cmd, plan, prompt, worker=worker.run_edit_step, guard=guard, chaos=chaos,
                              budget=budget, max_rollbacks=max_rollbacks, max_steps=max_steps, log=log, run_id=run_id)
    steps_f.close()
    cp = next((s["entire_checkpoint"] for s in reversed(res["steps"]) if s["entire_checkpoint"]), "")
    explain = gitgh.sh(["entire", "checkpoint", "explain", cp], cwd, check=False) if cp else "(no Entire checkpoint)"
    trace.finish()
    meta = {"run_id": run_id, "pr_url": pr_url, "status": res["status"], "cost_usd_total": res["cost_usd_total"],
            "rollbacks": res["rollbacks"], "trace_url": trace.trace_url(run_id), "entire_explain": explain}
    _, md = report.render(run_dir, meta)
    res.update(run_id=run_id, pr_url=pr_url, draft_pr=None)
    if res["status"] == "green":
        res["draft_pr"] = gitgh.open_draft_pr(cwd, fork, f"kedge/{run_id}", pr["title"], md)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="kedge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "batch"):
        p = sub.add_parser(name)
        p.add_argument("target")
        p.add_argument("--chaos", action="store_true")
        p.add_argument("--no-guard", action="store_true")
        p.add_argument("--budget", type=float, default=0.50)
        p.add_argument("--max-rollbacks", type=int, default=3)
        p.add_argument("--max-steps", type=int, default=6)
    a = ap.parse_args(argv)
    worker.use_pinned_opencode(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    kw = dict(guard=not a.no_guard, chaos=a.chaos, budget=a.budget, max_rollbacks=a.max_rollbacks,
              max_steps=a.max_steps)
    if a.cmd == "run":
        if not re.fullmatch(r"https://github\.com/[^/]+/[^/]+/pull/\d+", a.target):
            print("error: expected https://github.com/<owner>/<repo>/pull/<n>", file=sys.stderr)
            return 2
        t = _targets().get(a.target)
        if not t:
            print("error: PR not in targets.json allowlist", file=sys.stderr)
            return 2
        res = run_one(a.target, t["test_cmd"], t["fork"], setup_cmd=t.get("setup_cmd"), **kw)
        print(json.dumps({k: res[k] for k in ("run_id", "status", "cost_usd_total", "rollbacks", "draft_pr")}))
        return 0 if res["status"] in ("green", "already_green") else 1
    results = []
    for t in json.load(open(a.target)):
        try:
            r = run_one(t["pr_url"], t["test_cmd"], t["fork"], setup_cmd=t.get("setup_cmd"), **kw)
        except Exception as e:  # one broken target must not stop the batch
            r = {"pr_url": t["pr_url"], "status": f"error: {e}", "cost_usd_total": 0.0, "rollbacks": 0, "steps": []}
        results.append(r)
        print(json.dumps({k: r.get(k) for k in ("pr_url", "status", "cost_usd_total", "rollbacks", "draft_pr")}))
    green = [r for r in results if r["status"] == "green"]
    drifts = sum(1 for r in results for s in r["steps"] if s["drift"] and s["drift"] != "over_budget")
    cost = sum(r["cost_usd_total"] for r in results)
    print(json.dumps({"green": len(green), "total": len(results), "drifts_caught": drifts,
                      "usd_per_green": round(cost / len(green), 3) if green else None}))
    return 0
