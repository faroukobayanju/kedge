import argparse
import json
import os
import re
import sys
import tempfile
import time
import uuid

from kedge import chaos, gitgh, report, shiplog, supervisor, trace, trails, worker

PROMPT = ("You are fixing a failing dependency-bump PR.\nPR: {title}\nPlan: {hyp}\n"
          "Only edit files matching: {allowed}\nFailure output:\n{log}\n"
          "Do ONE step toward making the tests pass, then stop. Never delete or skip tests.")
LESSONS = os.path.abspath(os.path.join("runs", "lessons.jsonl"))
DEFAULTS = dict(guard=True, storm=None, budget=0.50, max_rollbacks=3, max_steps=6)


def load_dotenv(path=".env") -> None:
    """Minimal .env loader (KEY=VALUE lines); real environment variables win."""
    if not os.path.exists(path):
        return
    for line in open(path):
        k, sep, v = line.strip().partition("=")
        if sep and k and not k.startswith("#"):
            os.environ.setdefault(k.strip(), v.strip())


def _targets(path="targets.json"):
    return {t["pr_url"]: t for t in json.load(open(path))} if os.path.exists(path) else {}


def run_one(pr_url, test_cmd, fork, *, setup_cmd=None, guard, storm, budget, max_rollbacks, max_steps) -> dict:
    run_id = time.strftime("%Y%m%d-%H%M") + "-" + uuid.uuid4().hex[:4]
    run_dir = os.path.abspath(os.path.join("runs", run_id))
    os.makedirs(run_dir)
    cwd = os.path.join(tempfile.gettempdir(), "kedge", run_id)
    pr = gitgh.clone_pr(pr_url, cwd)
    agent = "claude-code" if os.environ.get("KEDGE_WORKER") == "claude" else "opencode"
    gitgh.exclude(cwd, [".entire/", ".opencode/", ".claude/", *gitgh.ARTIFACTS])
    if setup_cmd:  # one-time setup only; dependency installs belong in test_cmd so each run sees the agent's change
        gitgh.sh(["sh", "-c", setup_cmd], cwd, check=False)
    gitgh.sh(["entire", "enable", "--agent", agent], cwd, check=False)
    plugin = os.path.join(cwd, ".opencode", "plugins", "entire.ts")
    if agent == "opencode" and not os.path.exists(plugin):  # seen once: hooks "installed" but plugin file missing
        gitgh.sh(["entire", "enable", "--agent", agent, "--force"], cwd, check=False)
    log_tail = "Local test output:\n" + gitgh.test_output(cwd, test_cmd)
    base_total = gitgh.base_total(cwd, f"origin/{pr['base']}", test_cmd)
    print(f"🧪 base branch has {base_total if base_total >= 0 else 'unknown'} tests", file=sys.stderr, flush=True)
    ci = gitgh.ci_log(pr_url, pr["head"], pr["repo"])
    if ci.strip() and not ci.startswith("(no failed CI"):
        log_tail += "\n\nCI log:\n" + ci
    pr_files = gitgh.sh(["git", "diff", "--name-only", f"origin/{pr['base']}...HEAD"], cwd, check=False).split()
    plan = worker.make_plan(pr["title"], log_tail, pr_files, cwd)
    json.dump(plan, open(os.path.join(run_dir, "plan.json"), "w"))
    json.dump({"pr_url": pr_url, "test_cmd": test_cmd, "fork": fork, "cwd": cwd, "pr": pr, "log_tail": log_tail, "base_total": base_total,
               "kw": dict(guard=guard, storm=storm, budget=budget, max_rollbacks=max_rollbacks, max_steps=max_steps)},
              open(os.path.join(run_dir, "meta.json"), "w"))
    kw = dict(guard=guard, storm=storm, budget=budget, max_rollbacks=max_rollbacks, max_steps=max_steps)
    return _drive(run_id, run_dir, cwd, pr, plan, pr_url, test_cmd, fork, log_tail, None, base_total=base_total, **kw)


def _drive(run_id, run_dir, cwd, pr, plan, pr_url, test_cmd, fork, log_tail, state, base_total=-1, **kw) -> dict:
    trace.start(run_id, {"pr_url": pr_url, "guard": "on" if kw["guard"] else "off",
                         "storm": kw["storm"] or "off"})
    print(shiplog.header(pr["head"], kw["budget"]), file=sys.stderr, flush=True)
    steps_f = open(os.path.join(run_dir, "steps.jsonl"), "a")

    def log(rec):
        steps_f.write(json.dumps(rec) + "\n")
        steps_f.flush()
        trace.record(rec)
        print(shiplog.line(rec), file=sys.stderr, flush=True)

    def save(s):
        json.dump(s, open(os.path.join(run_dir, "state.json"), "w"))
    prompt = PROMPT.format(title=pr["title"], hyp=plan["hypothesis"], allowed=plan["allowed_files"], log=log_tail)
    prompt += "".join(f"\nLESSON FROM PAST RUNS: {lesson}" for lesson in supervisor.lessons_for(LESSONS, pr["repo"]))
    with trace.run_span(run_id, pr_url):
        res = supervisor.loop(cwd, test_cmd, plan, prompt, worker=worker.run_edit_step, replanner=worker.replan,
                              log=log, run_id=run_id, state=state, save=save, base_total=base_total, **kw)
    steps_f.close()
    supervisor.record_lessons(LESSONS, pr["repo"], res["steps"], res["notes"], res["status"])
    cp = next((s["entire_checkpoint"] for s in reversed(res["steps"]) if s["entire_checkpoint"]), "")
    explain = gitgh.sh(["entire", "checkpoint", "explain", cp], cwd, check=False) if cp else "(no Entire checkpoint)"
    trace.finish()
    meta = {"run_id": run_id, "pr_url": pr_url, "status": res["status"], "cost_usd_total": res["cost_usd_total"],
            "rollbacks": res["rollbacks"], "trace_url": trace.trace_url(run_id), "entire_explain": explain}
    _, md = report.render(run_dir, meta)
    res.update(run_id=run_id, pr_url=pr_url, draft_pr=None)
    if res["status"] == "green":
        branch = f"kedge/{run_id}"
        base = gitgh.push_branch(cwd, fork, branch)
        trail = trails.open_trail(cwd, fork, branch, base, pr["title"], open(md).read())
        if trail:  # Entire Trail opens the draft PR itself; drifts become findings on it
            res["trail"] = trail
            res["findings"] = trails.post_findings(cwd, fork, branch, res["steps"])
            res["draft_pr"] = trail
        else:  # Trails not enabled for this repo (early access): plain draft PR
            res["draft_pr"] = gitgh.open_draft_pr(cwd, fork, branch, pr["title"], md)
        if res["draft_pr"].startswith("https://github.com/"):  # a trail selector is not a PR URL
            meta["ci_status"] = gitgh.wait_ci(res["draft_pr"])
        report.render(run_dir, meta)  # re-render with real CI verdict
    res["ci_status"] = meta.get("ci_status", "not run")
    json.dump({**meta, "draft_pr": res["draft_pr"], "trail": res.get("trail"), "guard": kw["guard"],
               "storm": kw.get("storm"), "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S")},
              open(os.path.join(run_dir, "result.json"), "w"))  # read by `kedge ui`
    print(shiplog.footer(res, meta["trace_url"]), file=sys.stderr, flush=True)
    return res


def resume(run_id) -> dict:
    run_dir = os.path.abspath(os.path.join("runs", run_id))
    m = json.load(open(os.path.join(run_dir, "meta.json")))
    state = json.load(open(os.path.join(run_dir, "state.json")))
    return _drive(run_id, run_dir, m["cwd"], m["pr"], state["plan"], m["pr_url"], m["test_cmd"], m["fork"],
                  m["log_tail"], state, **m.get("kw", DEFAULTS))  # keep --no-guard/--storm


def _summary(res):
    return {k: res.get(k) for k in ("run_id", "status", "cost_usd_total", "rollbacks", "draft_pr")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="kedge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "batch"):
        p = sub.add_parser(name)
        p.add_argument("target")
        p.add_argument("--storm", choices=chaos.MODES)
        p.add_argument("--no-guard", action="store_true")
        p.add_argument("--budget", type=float, default=0.50)
        p.add_argument("--max-rollbacks", type=int, default=3)
        p.add_argument("--max-steps", type=int, default=6)
    sub.add_parser("resume").add_argument("run_id")
    up = sub.add_parser("ui")
    up.add_argument("--port", type=int, default=8711)
    a = ap.parse_args(argv)
    if a.cmd == "ui":
        from kedge import server
        server.serve(port=a.port)
        return 0
    load_dotenv()
    worker.use_pinned_opencode(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if a.cmd == "resume":
        if not os.path.exists(os.path.join("runs", a.run_id, "state.json")):
            print(f"error: no saved state for run {a.run_id}", file=sys.stderr)
            return 2
        res = resume(a.run_id)
        print(json.dumps(_summary(res)))
        return 0 if res["status"] in ("green", "already_green") else 1
    kw = dict(guard=not a.no_guard, storm=a.storm, budget=a.budget, max_rollbacks=a.max_rollbacks,
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
        print(json.dumps(_summary(res)))
        return 0 if res["status"] in ("green", "already_green") else 1
    results = []
    for t in json.load(open(a.target)):
        t0 = time.time()
        try:
            r = run_one(t["pr_url"], t["test_cmd"], t["fork"], setup_cmd=t.get("setup_cmd"), **kw)
        except Exception as e:  # one broken target must not stop the batch
            r = {"pr_url": t["pr_url"], "status": f"error: {e}", "cost_usd_total": 0.0, "rollbacks": 0, "steps": []}
        r["minutes"] = round((time.time() - t0) / 60, 2)
        results.append(r)
        print(json.dumps({k: r.get(k) for k in ("pr_url", "status", "cost_usd_total", "rollbacks", "draft_pr",
                                                 "minutes")}), flush=True)
    green = [r for r in results if r["status"] == "green"]
    drifts = sum(1 for r in results for s in r["steps"] if s["drift"] and s["drift"] != "over_budget")
    cost = sum(r["cost_usd_total"] for r in results)
    steps = [sum(1 for s in r["steps"] if s["action"] != "replan") for r in results]
    tokens = sum(s.get("tokens", 0) for r in results for s in r["steps"])
    mins = [r["minutes"] for r in results]
    print(json.dumps({"green": len(green), "total": len(results), "drifts_caught": drifts,
                      "false_claims": sum(1 for r in results for s in r["steps"] if s.get("false_claim")),
                      "usd_total": round(cost, 4), "usd_per_green": round(cost / len(green), 3) if green else None,
                      "tokens_total": tokens, "tokens_per_green": tokens // len(green) if green else None,
                      "mean_steps": round(sum(steps) / len(steps), 2) if steps else None,
                      "mean_minutes": round(sum(mins) / len(mins), 2) if mins else None}))
    return 0
