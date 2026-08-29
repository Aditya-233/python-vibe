"""Project tools for the agent loop. Jail + no shell."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from harness.act.code import apply_source, read_project_file, resolve_project_file
from harness.paths import rel_posix
from harness.act.patch_fix import align_indent, find_match, miss_message
from harness.scan.project_brief import render_map, resolve_scope
from harness.scan.project_scan import SKIP_DIR
from harness.scan.repo_map import render_outline

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
            hits.append(rel_posix(path, root))
        if len(hits) >= MAX_HITS:
            return "\n".join(hits) + _TRUNC
    if not hits:
        # rglob if user passed **/...
        for path in base.rglob(pattern.removeprefix("**/")):
            if any(part in SKIP_DIR for part in path.parts):
                continue
            if path.is_file():
                hits.append(rel_posix(path, root))
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
                    rel = rel_posix(path, root)
                    lines.append(f"{rel}:{i}:{line.strip()[:160]}")
                    if len(lines) >= MAX_HITS:
                        return "\n".join(lines) + _TRUNC
    return "\n".join(lines) or "(no hits)"


def map_py(project: Path, scope: str = "") -> str:
    """File list plus a signature outline. Sizes do not tell it where to look."""
    return f"{render_map(project, scope)}\n\n{render_outline(project, scope)}"


def read_py(project: Path, rel: str) -> str:
    path = resolve_project_file(project, rel)
    return read_project_file(path)


_TEST_METH = re.compile(r"def\s+(test_\w+)\s*\(")
_ASSERT_CALL = re.compile(r"assertEqual\s*\(\s*([A-Za-z_]\w+)\s*\(")
_IMPORT_LINE = re.compile(r"^(from\s+\S+\s+import\s+)(.+)$")


def _add_import_symbol(text: str, name: str) -> str:
    if not name or name in {"self", "True", "False", "None"}:
        return text
    for line in text.splitlines():
        match = _IMPORT_LINE.match(line)
        if not match:
            continue
        imported = {part.strip() for part in match.group(2).split(",")}
        if name in imported:
            return text
        if any(skip in line for skip in ("unittest", "pathlib", "typing")):
            continue
        return text.replace(line, f"{match.group(1)}{match.group(2).rstrip()}, {name}", 1)
    return text


def repair_unittest_append(original: str, append: str) -> str | None:
    """8B Append: often lands after if __name__ and skips the import."""
    if "def test_" not in append:
        return None
    if "TestCase" not in original and "unittest" not in original:
        return None
    meth = _TEST_METH.search(append)
    if not meth or re.search(rf"def\s+{re.escape(meth.group(1))}\s*\(", original):
        return None
    lines = append.strip("\n").splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        return None
    base = len(lines[0]) - len(lines[0].lstrip())
    dedented = "\n".join(
        line[base:] if len(line) >= base else line.lstrip() for line in lines
    )
    method = "    " + dedented.replace("\n", "\n    ")
    called = _ASSERT_CALL.search(append)
    text = _add_import_symbol(original, called.group(1) if called else "")
    marker = "\nif __name__"
    if marker in text:
        return text.replace(marker, "\n" + method + "\n" + marker, 1)
    return text.rstrip() + "\n\n" + method + "\n"


def patch_py(
    project: Path, rel: str, find: str, replace: str, append: str = ""
) -> str:
    path = resolve_project_file(project, rel)
    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    text = original
    note = ""
    if find:
        if len(find) < 8:
            return (
                "Find: must be at least 8 characters. "
                "Use a unique full line such as: Find: return tota"
            )
        hits = text.count(find)
        if hits > 1:
            return f"Find: matches {hits} times — use a longer unique snippet"
        match = find_match(text, find)
        if match is None:
            return miss_message(text, find)
        text = text.replace(
            match.text,
            replace if match.exact else align_indent(match.text, replace),
            1,
        )
        if not match.exact:
            note = " (Find: matched after whitespace normalisation)"
        else:
            note = ""
    elif not append:
        return "patch needs Find: or Append:"
    if append:
        repaired = repair_unittest_append(text, append)
        text = (
            repaired
            if repaired is not None
            else text.rstrip() + "\n\n" + append.rstrip() + "\n"
        )
    apply_source(path, text, original=original)
    return (
        f"patched {rel_posix(path, project.resolve())} "
        f"(backup {path.name}.bak){note}"
    )


def edit_py(project: Path, rel: str, source: str) -> str:
    path = resolve_project_file(project, rel)
    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    apply_source(path, source, original=original)
    return f"wrote {rel_posix(path, project.resolve())} (backup {path.name}.bak)"


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
