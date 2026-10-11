import json
import re
import os
import subprocess

FALLBACK_ALLOWED = ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
                    "requirements*.txt", "pyproject.toml", "poetry.lock", "uv.lock", "src/**/*"]


def use_pinned_opencode(root) -> bool:
    """Put the pinned OpenCode v1 (scripts/setup-opencode.sh) first on PATH, with its own data dirs.

    Entire's commit hook runs `opencode export`, so every subprocess must resolve the same binary.
    """
    home = os.path.join(os.path.abspath(root), ".tools", "opencode")
    bin_dir = os.path.join(home, "node_modules", ".bin")
    if not os.path.exists(os.path.join(bin_dir, "opencode")):
        return False
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    for k in ("DATA", "STATE", "CACHE"):
        os.environ[f"XDG_{k}_HOME"] = os.path.join(home, k.lower())
    # extra providers (the neatHack LiteLLM endpoint): KEDGE_MODEL=litellm/<model>, key in LITELLM_API_KEY
    os.environ.setdefault("OPENCODE_CONFIG", os.path.join(os.path.dirname(__file__), "opencode.json"))
    return True


def parse_opencode(jsonl: str) -> dict:
    """Sum step costs and keep the last text event from `opencode run --format json`."""
    cost, text, tokens = 0.0, "", 0
    for line in jsonl.splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("type") == "step_finish":
            part = e.get("part", {})
            cost += float(part.get("cost") or 0.0)
            t = part.get("tokens") or {}
            tokens += int(t.get("input") or 0) + int(t.get("output") or 0) + int(t.get("reasoning") or 0)
        elif e.get("type") == "text":
            text = e.get("part", {}).get("text", text)
    return {"result": text, "total_cost_usd": round(cost, 6), "tokens": tokens}


def _agent(prompt, cwd, edit) -> dict:
    # KEDGE_WORKER=claude switches to headless Claude Code; default is OpenCode (free models).
    if os.environ.get("KEDGE_WORKER") == "claude":
        args = ["claude", "-p", prompt, "--output-format", "json"]
        args += ["--permission-mode", "acceptEdits", "--max-turns", "15"] if edit else ["--model", "haiku", "--max-turns", "1"]
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=300 if edit else 120,
                       stdin=subprocess.DEVNULL)  # an inherited stdin stops OpenCode loading Entire's plugin
        return json.loads(p.stdout)
    model = os.environ.get("KEDGE_MODEL", "opencode/big-pickle")
    args = (["opencode", "run", "--format", "json", "--dir", cwd] + (["--auto"] if edit else ["--agent", "plan"])
            + ["-m", model, prompt])
    # OpenCode resolves its project from PWD, not the process cwd: without --dir/PWD it edits (and loads
    # plugins from) the caller's directory, so Entire's plugin in the clone never sees the session.
    # Free models occasionally stall; a step is short, so fail fast and let the loop retry.
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=300 if edit else 120,
                       stdin=subprocess.DEVNULL, env={**os.environ, "PWD": os.path.abspath(cwd)})
    return parse_opencode(p.stdout)


def run_edit_step(prompt, cwd) -> dict:
    try:
        d = _agent(prompt, cwd, edit=True)
        return {"cost_usd": float(d.get("total_cost_usd", 0.0)), "text": d.get("result", ""),
                "tokens": int(d.get("tokens", 0)), "error": None}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
        return {"cost_usd": 0.0, "text": "", "tokens": 0, "error": type(e).__name__}


SCHEMA = '{"hypothesis": str, "allowed_files": [glob, ...], "steps": [1-4 short imperative steps]}'
DEFAULT_STEPS = ["make the failing tests pass"]


SRC = re.compile(r"([\w./-]+\.(?:py|js|jsx|ts|tsx|mjs|cjs|go|rs|rb|java))\b")
TESTLIKE = re.compile(r"(^|/)(tests?|__tests__|spec)/|(^|/)test_[^/]*$|_test\.|\.(test|spec)\.")


def files_in_log(log) -> list[str]:
    """Non-test source files the failure output points at: the fallback plan may edit these."""
    out = []
    for f in SRC.findall(log or ""):
        f = f.lstrip("./")
        if "site-packages" in f or "node_modules" in f or f.startswith("/") or TESTLIKE.search(f) or f in out:
            continue
        out.append(f)
    return out[:10]


def _plan_call(prompt, cwd, extra_allowed=()) -> dict:
    try:
        d = _agent(prompt, cwd, edit=False)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        d = {"result": "", "total_cost_usd": 0.0}
    cost, text = float(d.get("total_cost_usd", 0.0)), d.get("result", "")
    try:
        p = json.loads(text[text.index("{"): text.rindex("}") + 1])
        return {"hypothesis": p["hypothesis"], "allowed_files": p["allowed_files"],
                "steps": p.get("steps") or DEFAULT_STEPS, "cost_usd": cost}
    except (ValueError, KeyError):
        return {"hypothesis": "unknown", "allowed_files": FALLBACK_ALLOWED + list(extra_allowed),
                "steps": DEFAULT_STEPS, "cost_usd": cost}


def make_plan(title, ci_log, files, cwd, memory=()) -> dict:
    past = "".join(f"\n- {m}" for m in memory)
    return _plan_call(
        f"A dependency-bump PR fails its tests. Reply with ONLY a JSON object {SCHEMA}. "
        "allowed_files lists the minimal file globs a fix may touch.\n"
        f"PR title: {title}\nFiles in PR: {files}\nFailure output:\n{ci_log[-4000:]}"
        + (f"\nWhat past runs on this repo or dependency did (from neatlogs traces and Entire checkpoints):{past}"
           if past else ""), cwd,
        extra_allowed=files_in_log(ci_log))


def replan(plan, notes, cwd) -> dict:
    return _plan_call(
        f"The previous plan failed twice. Reply with ONLY a JSON object {SCHEMA} for a DIFFERENT approach.\n"
        f"Previous plan: {json.dumps({k: plan.get(k) for k in ('hypothesis', 'allowed_files', 'steps')})}\n"
        f"What went wrong: {notes[-3:]}", cwd, extra_allowed=plan.get("allowed_files", []))
