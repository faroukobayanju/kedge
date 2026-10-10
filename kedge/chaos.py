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
