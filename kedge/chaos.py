from pathlib import Path

PATTERNS = ["test_*.py", "*_test.py", "*.test.js", "*.test.ts", "*.spec.js", "*.spec.ts"]


def delete_one_test(cwd) -> str | None:
    root = Path(cwd)
    found = sorted(p for pat in PATTERNS for p in root.rglob(pat)
                   if "node_modules" not in p.parts and ".git" not in p.parts)
    if not found:
        return None
    found[0].unlink()
    return found[0].relative_to(root).as_posix()


MODES = ("delete-test", "skip-test", "stray-edit")


def storm(mode, cwd) -> str | None:
    root = Path(cwd)
    if mode == "delete-test":
        return delete_one_test(cwd)
    if mode == "skip-test":
        found = sorted(p for p in root.rglob("test_*.py") if ".git" not in p.parts)
        if not found:
            return None
        found[0].write_text("import pytest\npytestmark = pytest.mark.skip\n" + found[0].read_text())
        return found[0].relative_to(root).as_posix()
    if mode == "stray-edit":
        (root / "STORM.md").write_text("the agent wandered off course\n")
        return "STORM.md"
    raise ValueError(f"unknown storm mode {mode!r}; pick one of {MODES}")
