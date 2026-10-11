import os

from kedge import chaos as chaos_mod
from kedge import checks, gitgh, money


def decide_next(history, max_rollbacks) -> str:
    """Pick the next action from the run so far: edit, replan, or give_up."""
    if history and history[-1].get("drift") == "over_budget":
        return "give_up"
    if sum(1 for s in history if s.get("rolled_back")) > max_rollbacks:
        return "give_up"
    if len(history) >= 2 and all(s.get("rolled_back") for s in history[-2:]):
        return "replan"
    return "edit"


def _rec(run_id, step, action, s, **kw):
    rec = {"run_id": run_id, "step": step, "action": action, "files_changed": [], "tests_passed": -1,
           "tests_total": -1, "cost_usd": 0.0, "cost_usd_total": round(s["cost"], 4), "tokens": 0, "drift": None,
           "rolled_back": False, "checkpoint_sha": s["good"], "entire_checkpoint": "", "plan_step": s["plan_idx"],
           "false_claim": False, "claim": ""}
    rec.update(kw)
    return rec


def _finish(status, s):
    return {"status": status, "steps": s["steps"], "cost_usd_total": s["cost"],
            "rollbacks": sum(1 for x in s["steps"] if x.get("rolled_back")), "notes": s["notes"]}


def loop(cwd, test_cmd, plan, prompt_base, *, worker, replanner=None, guard=True, storm=None, budget=0.5,
         max_rollbacks=3, max_steps=6, log=lambda rec: None, run_id="test", state=None, save=lambda s: None,
         base_total=-1, meter=None) -> dict:
    s = state
    if not s:
        ok, best, baseline_total = gitgh.run_tests(cwd, test_cmd)
        s = {"step": 0, "good": gitgh.head(cwd), "notes": [], "seen": [], "cost": plan.get("cost_usd", 0.0),
             "best": best, "baseline_total": baseline_total, "base_total": base_total, "plan": plan, "plan_idx": 0, "steps": []}
        if ok:
            return _finish("already_green", s)
        save(s)
    else:
        gitgh.reset(cwd, s["good"])  # discard half-finished work from the crashed step
        if s.get("model"):
            os.environ["KEDGE_MODEL"] = s["model"]
    while s["step"] < max_steps:
        action = decide_next(s["steps"], max_rollbacks)
        if action == "give_up":
            break
        if action == "replan" and replanner:
            # two rollbacks in a row: the cheap model isn't getting there, so the budget pays for the stronger one
            if os.environ.get("KEDGE_ESCALATE_MODEL"):
                s["model"] = os.environ["KEDGE_MODEL"] = os.environ["KEDGE_ESCALATE_MODEL"]
                s["step_costs"] = []  # cheap-model step costs would underestimate the stronger model
            before = meter.read() if meter else None
            s["plan"] = replanner(s["plan"], s["notes"], cwd)
            after = meter.read() if meter else None
            s["cost"] += round(after - before, 6) if before is not None and after is not None else s["plan"].get("cost_usd", 0.0)
            s["plan_idx"] = 0
            rec = _rec(run_id, s["step"], "replan", s)
            s["steps"].append(rec)
            log(rec)
            save(s)
            continue
        # stop before a step the cfo.ai budget can't cover, instead of finding out after paying for it
        expected = money.predict(s.setdefault("step_costs", []))
        if s["steps"] and expected and s["cost"] + expected > budget:
            rec = _rec(run_id, s["step"], "budget_stop", s, drift="over_budget")
            s["steps"].append(rec)
            log(rec)
            save(s)
            break
        s["step"] += 1
        save(s)
        steps_list = s["plan"].get("steps") or []
        current = steps_list[min(s["plan_idx"], len(steps_list) - 1)] if steps_list else "make the tests pass"
        prompt = (prompt_base + f"\nCURRENT PLAN STEP: {current}"
                  + "".join(f"\nRECOVERY NOTE: {n}" for n in s["notes"][-3:]))
        before = meter.read() if meter else None
        r = worker(prompt, cwd)
        after = meter.read() if meter else None
        if before is not None and after is None:
            after = meter.read()  # one retry: the agent CLI's own estimate is far below the real bill
        cost = round(after - before, 6) if before is not None and after is not None else r["cost_usd"]
        s["cost"] += cost
        s["step_costs"].append(cost)
        if storm and s["step"] == 1:
            chaos_mod.storm(storm, cwd)
        ok, passed, total = gitgh.run_tests(cwd, test_cmd)
        files, h = gitgh.changed_files(cwd), gitgh.diff_hash(cwd)
        d = checks.drift(passed=passed, total=total, best_passed=s["best"], baseline_total=s["baseline_total"],
                         files=files, allowed=s["plan"]["allowed_files"], diff_hash=h, seen_hashes=set(s["seen"]),
                         cost_total=s["cost"], budget=budget, guard=guard, base_total=s.get("base_total", -1))
        if ok and not d and guard:  # verification: a green result must reproduce
            ok2, _, total2 = gitgh.run_tests(cwd, test_cmd)
            if not ok2 or (total2 >= 0 and total2 < max(s["baseline_total"], s.get("base_total", -1))):
                d = "verify_failed"
        rec = _rec(run_id, s["step"], "worker_error" if r["error"] else "worker", s, files_changed=files,
                   tests_passed=passed, tests_total=total, cost_usd=cost, tokens=r.get("tokens", 0),
                   cost_usd_total=round(s["cost"], 4), drift=d)
        claim = checks.claimed_success(r.get("text", ""))
        rec["claim"] = claim or ""
        rec["false_claim"] = bool(claim) and (not ok or (total >= 0 and total < s["baseline_total"]))
        if rec["false_claim"] and guard:
            s["notes"].append(checks.NOTES["false_claim"])
        if d:
            gitgh.reset(cwd, s["good"])
            s["seen"].append(h)
            rec["rolled_back"] = d != "over_budget"
            if d != "over_budget":
                note = checks.NOTES[d].format(allowed=s["plan"]["allowed_files"], files=files)
                if r.get("text"):  # hold the agent to its own words
                    note += f' Your last reply said: "{" ".join(r["text"].split())[:240]}"'
                s["notes"].append(note)
            s["steps"].append(rec)
            log(rec)
            save(s)
            continue
        if files:
            s["good"], rec["entire_checkpoint"] = gitgh.commit(cwd, f"kedge {run_id} step {s['step']}")
            rec["checkpoint_sha"] = s["good"]
            if passed > s["best"]:
                s["best"] = passed
                s["plan_idx"] += 1  # progress: move to the next plan step
        s["steps"].append(rec)
        log(rec)
        save(s)
        if ok:
            return _finish("green", s)
    return _finish("gave_up", s)
