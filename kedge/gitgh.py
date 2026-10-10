import hashlib
import json
import os
import subprocess

from kedge.checks import parse_summary


def sh(args, cwd=None, check=True) -> str:
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True).stdout


def head(cwd) -> str:
    return sh(["git", "rev-parse", "HEAD"], cwd).strip()


def changed_files(cwd) -> list[str]:
    out = sh(["git", "status", "--porcelain", "--untracked-files=all"], cwd)
    return [line[3:].split(" -> ")[-1] for line in out.splitlines() if line]


def diff_hash(cwd) -> str:
    sh(["git", "add", "-A", "-N"], cwd)  # intent-to-add so new files appear in the diff
    return hashlib.sha256(sh(["git", "diff", "HEAD"], cwd).encode()).hexdigest()[:12]


def commit(cwd, msg) -> tuple[str, str]:
    sh(["git", "add", "-A"], cwd)
    sh(["git", "commit", "-qm", msg], cwd)
    cp = sh(["git", "log", "-1", "--format=%(trailers:key=Entire-Checkpoint,valueonly)"], cwd).strip()
    return head(cwd), cp


def reset(cwd, sha) -> None:
    sh(["git", "reset", "-q", "--hard", sha], cwd)
    sh(["git", "clean", "-qfd"], cwd)


def exclude(cwd, patterns) -> None:
    """Hide tool config (Entire, OpenCode) from drift checks; ignored files also survive `git clean -fd`."""
    with open(os.path.join(cwd, ".git", "info", "exclude"), "a") as f:
        f.write("\n".join(patterns) + "\n")


# Test-run artifacts must not look like agent edits (excluded per clone in cli.run_one).
ARTIFACTS = ["__pycache__/", "*.pyc", ".pytest_cache/", "node_modules/"]


def test_output(cwd, test_cmd, max_lines=200) -> str:
    """Local failing-test output: ground truth for the planner, even when CI is unavailable."""
    p = subprocess.run(test_cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=600,
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return "\n".join((p.stdout + p.stderr).splitlines()[-max_lines:])


def run_tests(cwd, test_cmd) -> tuple[bool, int, int]:
    p = subprocess.run(test_cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=600,
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    passed, total = parse_summary(p.stdout + p.stderr)
    return p.returncode == 0, passed, total


def clone_pr(pr_url, dest) -> dict:
    info = json.loads(sh(["gh", "pr", "view", pr_url, "--json", "title,baseRefName,headRefName,url"]))
    repo = "/".join(pr_url.split("/")[3:5])
    sh(["gh", "repo", "clone", repo, dest, "--", "-q"])
    sh(["gh", "pr", "checkout", pr_url.rsplit("/", 1)[1]], dest)
    return {"title": info["title"], "base": info["baseRefName"], "head": info["headRefName"], "repo": repo}


def ci_log(pr_url, head_branch, repo) -> str:
    runs = json.loads(sh(["gh", "run", "list", "-R", repo, "--branch", head_branch,
                          "--status", "failure", "--limit", "1", "--json", "databaseId"]))
    if not runs:
        return "(no failed CI run found)"
    log = sh(["gh", "run", "view", str(runs[0]["databaseId"]), "-R", repo, "--log-failed"], check=False)
    return "\n".join(log.splitlines()[-200:])


def open_draft_pr(cwd, fork, branch, title, body_path) -> str:
    sh(["git", "remote", "add", "fork", f"https://github.com/{fork}.git"], cwd, check=False)
    sh(["git", "push", "-qf", "fork", f"HEAD:{branch}"], cwd)
    base = json.loads(sh(["gh", "repo", "view", fork, "--json", "defaultBranchRef"]))["defaultBranchRef"]["name"]
    return sh(["gh", "pr", "create", "-R", fork, "--head", branch, "--base", base,
               "--draft", "--title", f"[kedge] {title}", "--body-file", body_path]).strip()
