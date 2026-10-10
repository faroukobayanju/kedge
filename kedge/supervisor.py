import json
import os

from kedge import chaos as chaos_mod
from kedge import checks, gitgh


def decide_next(history, max_rollbacks) -> str:
    """Pick the next action from the run so far: edit, replan, or give_up."""
    if history and history[-1].get("drift") == "over_budget":
        return "give_up"
    if sum(1 for s in history if s.get("rolled_back")) > max_rollbacks:
        return "give_up"
    if len(history) >= 2 and all(s.get("rolled_back") for s in history[-2:]):
        return "replan"
    return "edit"


def lessons_for(path, repo, n=3) -> list[str]:
    if not os.path.exists(path):
        return []
    rows = [json.loads(line) for line in open(path) if line.strip()]
    return [r["note"] for r in rows][-n:]


def record_lessons(path, repo, steps, notes, status) -> None:
    # a note is a lesson only if it preceded a rollback that the run then recovered from
    if status != "green" or not any(s.get("rolled_back") for s in steps):
        return
    with open(path, "a") as f:
        for n in notes:
            f.write(json.dumps({"repo": repo, "note": n}) + "\n")


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
         base_total=-1) -> dict:
    s = state
    if not s:
        ok, best, baseline_total = gitgh.run_tests(cwd, test_cmd)
        s = {"step": 0, "good": gitgh.head(cwd), "notes": [], "seen": [], "cost": plan.get("cost_usd", 0.0),
             "best": best, "baseline_total": max(baseline_total, base_total), "plan": plan, "plan_idx": 0, "steps": []}
        if ok:
            return _finish("already_green", s)
        save(s)
    else:
        gitgh.reset(cwd, s["good"])  # discard half-finished work from the crashed step
    while s["step"] < max_steps:
        action = decide_next(s["steps"], max_rollbacks)
        if action == "give_up":
            break
        if action == "replan" and replanner:
            s["plan"] = replanner(s["plan"], s["notes"], cwd)
            s["cost"] += s["plan"].get("cost_usd", 0.0)
            s["plan_idx"] = 0
            rec = _rec(run_id, s["step"], "replan", s)
            s["steps"].append(rec)
            log(rec)
            save(s)
            continue
        s["step"] += 1
        save(s)
        steps_list = s["plan"].get("steps") or []
        current = steps_list[min(s["plan_idx"], len(steps_list) - 1)] if steps_list else "make the tests pass"
        prompt = (prompt_base + f"\nCURRENT PLAN STEP: {current}"
                  + "".join(f"\nRECOVERY NOTE: {n}" for n in s["notes"][-3:]))
        r = worker(prompt, cwd)
        s["cost"] += r["cost_usd"]
        if storm and s["step"] == 1:
            chaos_mod.storm(storm, cwd)
        ok, passed, total = gitgh.run_tests(cwd, test_cmd)
        files, h = gitgh.changed_files(cwd), gitgh.diff_hash(cwd)
        d = checks.drift(passed=passed, total=total, best_passed=s["best"], baseline_total=s["baseline_total"],
                         files=files, allowed=s["plan"]["allowed_files"], diff_hash=h, seen_hashes=set(s["seen"]),
                         cost_total=s["cost"], budget=budget, guard=guard)
        if ok and not d and guard:  # verification: a green result must reproduce
            ok2, _, total2 = gitgh.run_tests(cwd, test_cmd)
            if not ok2 or (total2 >= 0 and total2 < s["baseline_total"]):
                d = "verify_failed"
        rec = _rec(run_id, s["step"], "worker_error" if r["error"] else "worker", s, files_changed=files,
                   tests_passed=passed, tests_total=total, cost_usd=r["cost_usd"], tokens=r.get("tokens", 0),
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
                s["notes"].append(checks.NOTES[d].format(allowed=s["plan"]["allowed_files"], files=files))
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
