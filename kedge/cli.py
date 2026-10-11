import argparse
import json
import os
import re
import sys
import tempfile
import time
import uuid

from kedge import chaos, gitgh, money, report, shiplog, supervisor, trace, trails, worker

PROMPT = ("You are fixing a failing dependency-bump PR.\nPR: {title}\nPlan: {hyp}\n"
          "Only edit files matching: {allowed}\nFailure output:\n{log}\n"
          "Do ONE step toward making the tests pass, then stop. Never delete or skip tests.")
LEDGER = os.path.abspath(os.path.join("runs", "ledger.csv"))
DEFAULTS = dict(guard=True, storm=None, budget=None, max_rollbacks=3, max_steps=6, allow_unproven=False)


def dep_of(title, head) -> str:
    """The bumped dependency: "bump packaging from 21.3 to 24.2" -> packaging; else the branch's last part."""
    m = re.search(r"bump (\S+) from", title, re.I)
    return m.group(1) if m else head.rsplit("/", 1)[-1]


def budget_or_cfo(budget) -> float:
    """--budget wins; otherwise the cfo.ai model in pricing.json decides what one PR may spend."""
    return budget if budget is not None else money.model_budget(money.load_pricing())


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


def run_one(pr_url, test_cmd, fork, *, setup_cmd=None, guard, storm, budget, max_rollbacks, max_steps,
            allow_unproven=False) -> dict:
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
    # memory: what past runs on this repo or dependency did (neatlogs), and past agent fixes for it (Entire)
    pr["dep"] = dep_of(pr["title"], pr["head"])
    # agent-influenced text from past runs: one line each, capped, so it can't forge prompt sections
    memory = [" ".join(m.split())[:300] for m in
              trace.memory(pr["repo"], pr["dep"], run_id) + trails.past_fixes(cwd, f"fix {pr['title']}")]
    for line in memory:
        print(f"🧠 {line}", file=sys.stderr, flush=True)
    meter = money.Meter()
    before = meter.read()
    plan = worker.make_plan(pr["title"], log_tail, pr_files, cwd, memory=memory)
    after = meter.read()
    if before is not None and after is not None:
        plan["cost_usd"] = round(after - before, 6)  # the real bill, not the agent CLI's estimate
    json.dump(plan, open(os.path.join(run_dir, "plan.json"), "w"))
    kw = dict(guard=guard, storm=storm, budget=budget_or_cfo(budget), max_rollbacks=max_rollbacks,
              max_steps=max_steps, allow_unproven=allow_unproven)
    json.dump({"pr_url": pr_url, "test_cmd": test_cmd, "fork": fork, "cwd": cwd, "pr": pr, "log_tail": log_tail,
               "base_total": base_total, "memory": memory, "model": os.environ.get("KEDGE_MODEL", ""), "kw": kw},
              open(os.path.join(run_dir, "meta.json"), "w"))
    return _drive(run_id, run_dir, cwd, pr, plan, pr_url, test_cmd, fork, log_tail, None, base_total=base_total,
                  memory=memory, **kw)


def proof_of(steps, trace_id) -> dict:
    """No proof, no PR: a neatlogs trace, and an Entire checkpoint on every commit Kedge kept."""
    kept = [s for s in steps if s["action"] == "worker" and s["files_changed"] and not s["rolled_back"]]
    missing = []
    if trace_id == "unavailable":
        missing.append("neatlogs trace")
    unchecked = [s["step"] for s in kept if not s["entire_checkpoint"]]
    if unchecked:
        missing.append(f"Entire checkpoint on step {', '.join(map(str, unchecked))}")
    return {"trace": trace_id, "checkpoints": [s["entire_checkpoint"] for s in kept if s["entire_checkpoint"]],
            "missing": missing}


def _ship(run_dir, cwd, fork, run_id, pr, meta, res) -> None:
    """Push the branch and open the review: an Entire Trail if the repo has Trails, else a draft PR."""
    _, md = report.render(run_dir, meta)
    branch = f"kedge/{run_id}"
    base = gitgh.push_branch(cwd, fork, branch)
    trail = trails.open_trail(cwd, fork, branch, base, pr["title"], open(md).read())
    if trail:  # Entire Trail opens the draft PR itself; drifts become findings on it
        res["trail"] = trail
        res["findings"] = trails.post_findings(cwd, fork, branch, res["steps"])
        res["draft_pr"] = trail
    else:  # Trails not enabled for this repo: plain draft PR
        res["draft_pr"] = gitgh.open_draft_pr(cwd, fork, branch, pr["title"], md)
    if res["draft_pr"].startswith("https://github.com/"):  # a trail selector is not a PR URL
        meta["ci_status"] = gitgh.wait_ci(res["draft_pr"])
    report.render(run_dir, meta)  # re-render with the real CI verdict


def _drive(run_id, run_dir, cwd, pr, plan, pr_url, test_cmd, fork, log_tail, state, base_total=-1, memory=(),
           allow_unproven=False, **kw) -> dict:
    dep = pr.get("dep") or dep_of(pr["title"], pr["head"])
    trace.start(run_id, {"pr_url": pr_url, "repo": pr["repo"], "dep": dep, "guard": "on" if kw["guard"] else "off",
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
    prompt += "".join(f"\nFROM PAST RUNS (neatlogs, Entire): {line}" for line in memory)
    model = os.environ.get("KEDGE_MODEL")
    try:
        with trace.run_span(run_id, pr_url) as span:
            res = supervisor.loop(cwd, test_cmd, plan, prompt, worker=worker.run_edit_step, replanner=worker.replan,
                                  log=log, run_id=run_id, state=state, save=save, base_total=base_total,
                                  meter=money.Meter(), **kw)
            trace.summarize_run(span, res)
    finally:  # a model switch on replan is for this run only; the next PR in a batch starts cheap again
        if model is None:
            os.environ.pop("KEDGE_MODEL", None)
        else:
            os.environ["KEDGE_MODEL"] = model
    steps_f.close()
    cp = next((s["entire_checkpoint"] for s in reversed(res["steps"]) if s["entire_checkpoint"]), "")
    explain = gitgh.sh(["entire", "checkpoint", "explain", cp], cwd, check=False) if cp else "(no Entire checkpoint)"
    trace.finish()
    proving = res["status"] == "green" and kw["guard"] and not allow_unproven
    trace_id = trace.trace_url(run_id, wait_s=180 if proving and os.environ.get("NEATLOGS_API_KEY") else 0)
    trace.verdict(trace_id, res["steps"], res["status"])
    pricing = money.load_pricing()
    proof = proof_of(res["steps"], trace_id)
    proof["margin"] = money.margin_line(res["cost_usd_total"], pricing)
    if proving and proof["missing"]:
        res["status"] = "green_unproven"  # no proof, no PR: push the work, open nothing; `kedge prove` later
    meta = {"run_id": run_id, "pr_url": pr_url, "status": res["status"], "cost_usd_total": res["cost_usd_total"],
            "rollbacks": res["rollbacks"], "trace_url": trace_id, "entire_explain": explain, "proof": proof}
    report.render(run_dir, meta)
    res.update(run_id=run_id, pr_url=pr_url, draft_pr=None)
    if res["status"] == "green":
        _ship(run_dir, cwd, fork, run_id, pr, meta, res)
    elif res["status"] == "green_unproven":
        gitgh.push_branch(cwd, fork, f"kedge/{run_id}")
        print(f"🔒 no PR: missing {', '.join(proof['missing'])}. Run `kedge prove {run_id}` once it exists.",
              file=sys.stderr, flush=True)
    res["ci_status"] = meta.get("ci_status", "not run")
    json.dump({**meta, "draft_pr": res["draft_pr"], "trail": res.get("trail"), "guard": kw["guard"],
               "storm": kw.get("storm"), "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S")},
              open(os.path.join(run_dir, "result.json"), "w"))  # read by `kedge ui`
    money.ledger_append(LEDGER, {"run_id": run_id, "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 "repo": pr["repo"], "pr_url": pr_url, "status": res["status"],
                                 "model": os.environ.get("KEDGE_MODEL", "opencode/big-pickle"),
                                 "real_cost_usd": round(res["cost_usd_total"], 4),
                                 "steps": sum(1 for s in res["steps"] if s["action"] != "replan"),
                                 "rollbacks": res["rollbacks"], "price_usd": pricing["price_per_green_usd"],
                                 "margin": pricing["target_gross_margin"]})
    print(shiplog.footer(res, trace_id), file=sys.stderr, flush=True)
    return res


def prove(run_id) -> int:
    """Open the PR for a green_unproven run once its proof exists."""
    run_dir = os.path.abspath(os.path.join("runs", run_id))
    m = json.load(open(os.path.join(run_dir, "meta.json")))
    result = json.load(open(os.path.join(run_dir, "result.json")))
    if result["status"] != "green_unproven":
        print(f"error: run {run_id} is {result['status']}, not green_unproven", file=sys.stderr)
        return 2
    steps = [json.loads(line) for line in open(os.path.join(run_dir, "steps.jsonl")) if line.strip()]
    proof = proof_of(steps, trace.trace_url(run_id))
    if proof["missing"]:
        print(f"still missing: {', '.join(proof['missing'])}", file=sys.stderr)
        return 1
    proof["margin"] = result.get("proof", {}).get("margin", "")
    meta = {**{k: result[k] for k in ("run_id", "pr_url", "cost_usd_total", "rollbacks", "entire_explain")},
            "status": "green", "trace_url": proof["trace"], "proof": proof}
    res = {"steps": steps, "draft_pr": None}
    _ship(run_dir, m["cwd"], m["fork"], run_id, m["pr"], meta, res)
    json.dump({**result, **meta, "draft_pr": res["draft_pr"], "trail": res.get("trail")},
              open(os.path.join(run_dir, "result.json"), "w"))
    pricing = money.load_pricing()
    money.ledger_append(LEDGER, {"run_id": run_id, "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 "repo": m["pr"]["repo"], "pr_url": result["pr_url"], "status": "green",
                                 "model": m.get("model", ""), "real_cost_usd": round(result["cost_usd_total"], 4),
                                 "steps": sum(1 for s in steps if s["action"] != "replan"),
                                 "rollbacks": result["rollbacks"], "price_usd": pricing["price_per_green_usd"],
                                 "margin": pricing["target_gross_margin"]})
    print(json.dumps({"run_id": run_id, "status": "green", "draft_pr": res["draft_pr"]}))
    return 0


def resume(run_id) -> dict:
    run_dir = os.path.abspath(os.path.join("runs", run_id))
    m = json.load(open(os.path.join(run_dir, "meta.json")))
    state = json.load(open(os.path.join(run_dir, "state.json")))
    kw = {**DEFAULTS, **m.get("kw", {})}  # keep --no-guard/--storm and the budget the run started with
    kw["budget"] = budget_or_cfo(kw["budget"])
    return _drive(run_id, run_dir, m["cwd"], m["pr"], state["plan"], m["pr_url"], m["test_cmd"], m["fork"],
                  m["log_tail"], state, memory=m.get("memory", ()), **kw)


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
        p.add_argument("--budget", type=float, default=None,
                       help="model spend per PR in USD (default: from the cfo.ai model in pricing.json)")
        p.add_argument("--max-rollbacks", type=int, default=3)
        p.add_argument("--max-steps", type=int, default=6)
        p.add_argument("--allow-unproven", action="store_true",
                       help="open a PR even without a neatlogs trace and Entire checkpoints (local dev only)")
    sub.add_parser("resume").add_argument("run_id")
    sub.add_parser("prove").add_argument("run_id")
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
    if a.cmd == "prove":
        if not os.path.exists(os.path.join("runs", a.run_id, "result.json")):
            print(f"error: no finished run {a.run_id}", file=sys.stderr)
            return 2
        return prove(a.run_id)
    kw = dict(guard=not a.no_guard, storm=a.storm, budget=a.budget, max_rollbacks=a.max_rollbacks,
              max_steps=a.max_steps, allow_unproven=a.allow_unproven)
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
