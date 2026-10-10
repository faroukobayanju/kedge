from kedge import chaos as chaos_mod
from kedge import checks, gitgh


def loop(cwd, test_cmd, plan, prompt_base, *, worker, guard=True, chaos=False, budget=0.5,
         max_rollbacks=3, max_steps=6, log=lambda rec: None, run_id="test") -> dict:
    ok, best, baseline_total = gitgh.run_tests(cwd, test_cmd)
    steps, notes, seen = [], [], set()
    cost, rollbacks, good = plan.get("cost_usd", 0.0), 0, gitgh.head(cwd)
    if ok:
        return {"status": "already_green", "steps": [], "cost_usd_total": cost, "rollbacks": 0}
    for step in range(1, max_steps + 1):
        prompt = prompt_base + "".join(f"\nRECOVERY NOTE: {n}" for n in notes)
        r = worker(prompt, cwd)
        cost += r["cost_usd"]
        if chaos and step == 1:
            chaos_mod.delete_one_test(cwd)
        ok, passed, total = gitgh.run_tests(cwd, test_cmd)
        files, h = gitgh.changed_files(cwd), gitgh.diff_hash(cwd)
        d = checks.drift(passed=passed, total=total, best_passed=best, baseline_total=baseline_total,
                         files=files, allowed=plan["allowed_files"], diff_hash=h, seen_hashes=seen,
                         cost_total=cost, budget=budget, guard=guard)
        rec = {"run_id": run_id, "step": step, "action": "worker_error" if r["error"] else "worker",
               "files_changed": files, "tests_passed": passed, "tests_total": total,
               "cost_usd": r["cost_usd"], "cost_usd_total": round(cost, 4), "tokens": r.get("tokens", 0), "drift": d,
               "rolled_back": False, "checkpoint_sha": good, "entire_checkpoint": ""}
        if d:
            gitgh.reset(cwd, good)
            seen.add(h)
            rec["rolled_back"] = d != "over_budget"
            steps.append(rec)
            log(rec)
            if d == "over_budget":
                break
            rollbacks += 1
            notes.append(checks.NOTES[d].format(allowed=plan["allowed_files"], files=files))
            if rollbacks > max_rollbacks:
                break
            continue
        if files:
            good, rec["entire_checkpoint"] = gitgh.commit(cwd, f"kedge {run_id} step {step}")
            rec["checkpoint_sha"] = good
            best = max(best, passed)
        steps.append(rec)
        log(rec)
        if ok:
            return {"status": "green", "steps": steps, "cost_usd_total": cost, "rollbacks": rollbacks}
    return {"status": "gave_up", "steps": steps, "cost_usd_total": cost, "rollbacks": rollbacks}
