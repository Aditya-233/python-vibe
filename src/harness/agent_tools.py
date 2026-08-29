"""Project tools for the agent loop. Jail + no shell."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from harness.code import apply_source, read_project_file, resolve_project_file
from harness.project_brief import render_map, resolve_scope
from harness.project_scan import SKIP_DIR

MAX_HITS = 30
_TRUNC = "\n# … truncated. Narrow Query or pass --scope"


def glob_py(project: Path, pattern: str, scope: str = "") -> str:
    root = project.resolve()
    base = resolve_scope(project, scope) if scope else root
    hits: list[str] = []
    for path in base.glob(pattern):
        if any(part in SKIP_DIR for part in path.parts):
            continue
        if path.is_file():
            hits.append(str(path.relative_to(root)))
        if len(hits) >= MAX_HITS:
            return "\n".join(hits) + _TRUNC
    if not hits:
        # rglob if user passed **/...
        for path in base.rglob(pattern.removeprefix("**/")):
            if any(part in SKIP_DIR for part in path.parts):
                continue
            if path.is_file():
                hits.append(str(path.relative_to(root)))
            if len(hits) >= MAX_HITS:
                return "\n".join(hits) + _TRUNC
    return "\n".join(hits) or "(no files)"


def grep_py(project: Path, query: str, scope: str = "") -> str:
    root = project.resolve()
    base = resolve_scope(project, scope) if scope else root
    try:
        rx = re.compile(query)
    except re.error as exc:
        return f"bad regex: {exc}"
    lines: list[str] = []
    for suffix in ("*.py", "*.pyi", "*.md"):
        for path in base.rglob(suffix):
            if any(part in SKIP_DIR for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    rel = path.relative_to(root)
                    lines.append(f"{rel}:{i}:{line.strip()[:160]}")
                    if len(lines) >= MAX_HITS:
                        return "\n".join(lines) + _TRUNC
    return "\n".join(lines) or "(no hits)"


def map_py(project: Path, scope: str = "") -> str:
    return render_map(project, scope)


def read_py(project: Path, rel: str) -> str:
    path = resolve_project_file(project, rel)
    return read_project_file(path)


def patch_py(
    project: Path, rel: str, find: str, replace: str, append: str = ""
) -> str:
    path = resolve_project_file(project, rel)
    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    text = original
    if find:
        if len(find) < 8:
            return (
                "Find: must be at least 8 characters. "
                "Use a unique full line such as: Find: return tota"
            )
        hits = text.count(find)
        if hits == 0:
            return "Find: string not in file"
        if hits > 1:
            return f"Find: matches {hits} times — use a longer unique snippet"
        text = text.replace(find, replace, 1)
    elif not append:
        return "patch needs Find: or Append:"
    if append:
        text = text.rstrip() + "\n\n" + append.rstrip() + "\n"
    apply_source(path, text, original=original)
    return f"patched {path.relative_to(project.resolve())} (backup {path.name}.bak)"


def edit_py(project: Path, rel: str, source: str) -> str:
    path = resolve_project_file(project, rel)
    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    apply_source(path, source, original=original)
    return f"wrote {path.relative_to(project.resolve())} (backup {path.name}.bak)"


def run_python(project: Path, argv: tuple[str, ...]) -> str:
    if not argv:
        return "Argv required, e.g. -m unittest discover -s tests -q"
    blocked = {"-c", "-m pip", "http.server"}
    joined = " ".join(argv)
    if any(tok in joined for tok in blocked) or "|" in joined or ";" in joined:
        return "refusing that argv"
    if "unittest" in joined and "tests" in joined and not (project / "tests").is_dir():
        return "no tests/ directory in this project — add tests/test_*.py first"
    try:
        proc = subprocess.run(
            [sys.executable, *argv],
            cwd=project,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "timed out (60s)"
    out = (proc.stdout or "") + (proc.stderr or "")
    return f"exit {proc.returncode}\n{out[-4000:]}"
