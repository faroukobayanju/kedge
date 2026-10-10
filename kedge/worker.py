import json
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
    return True


def parse_opencode(jsonl: str) -> dict:
    """Sum step costs and keep the last text event from `opencode run --format json`."""
    cost, text = 0.0, ""
    for line in jsonl.splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("type") == "step_finish":
            cost += float(e.get("part", {}).get("cost") or 0.0)
        elif e.get("type") == "text":
            text = e.get("part", {}).get("text", text)
    return {"result": text, "total_cost_usd": round(cost, 6)}


def _agent(prompt, cwd, edit) -> dict:
    # KEDGE_WORKER=claude switches to headless Claude Code; default is OpenCode (free models).
    if os.environ.get("KEDGE_WORKER") == "claude":
        args = ["claude", "-p", prompt, "--output-format", "json"]
        args += ["--permission-mode", "acceptEdits", "--max-turns", "15"] if edit else ["--model", "haiku", "--max-turns", "1"]
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=300 if edit else 120)
        return json.loads(p.stdout)
    model = os.environ.get("KEDGE_MODEL", "opencode/big-pickle")
    args = ["opencode", "run", "--format", "json"] + (["--auto"] if edit else ["--agent", "plan"]) + ["-m", model, prompt]
    # free models occasionally stall; a step is short, so fail fast and let the loop retry
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=300 if edit else 120)
    return parse_opencode(p.stdout)


def run_edit_step(prompt, cwd) -> dict:
    try:
        d = _agent(prompt, cwd, edit=True)
        return {"cost_usd": float(d.get("total_cost_usd", 0.0)), "text": d.get("result", ""), "error": None}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
        return {"cost_usd": 0.0, "text": "", "error": type(e).__name__}


def make_plan(title, ci_log, files, cwd) -> dict:
    prompt = (
        "A dependency-bump PR fails CI. Reply with ONLY a JSON object "
        '{"hypothesis": str, "allowed_files": [glob, ...]} listing the minimal file globs a fix may touch.\n'
        f"PR title: {title}\nFiles in PR: {files}\nFailing CI log tail:\n{ci_log[-4000:]}"
    )
    try:
        d = _agent(prompt, cwd, edit=False)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        d = {"result": "", "total_cost_usd": 0.0}
    cost, text = float(d.get("total_cost_usd", 0.0)), d.get("result", "")
    try:
        plan = json.loads(text[text.index("{"): text.rindex("}") + 1])
        return {"hypothesis": plan["hypothesis"], "allowed_files": plan["allowed_files"], "cost_usd": cost}
    except (ValueError, KeyError):
        return {"hypothesis": "unknown", "allowed_files": FALLBACK_ALLOWED, "cost_usd": cost}
