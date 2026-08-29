"""List the functions and classes each Python file defines.

`map` reports which files exist and how large they are. That is not enough
to choose a file to open. This module reports the signature of every
top-level function and class instead, which names the file's purpose.

Output is capped by file count and line count so it stays small enough to
send to a model with a limited context window.
"""

from __future__ import annotations

import ast
from pathlib import Path

from harness.paths import rel_posix
from harness.scan.project_brief import iter_text_files

MAX_OUTLINE_FILES = 24
MAX_PER_FILE = 10
MAX_OUTLINE_LINES = 120


def _signature(node: ast.AST) -> str:
    if isinstance(node, ast.ClassDef):
        return f"class {node.name}"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        head = f"{prefix} {node.name}({ast.unparse(node.args)})"
        if node.returns is not None:
            head += f" -> {ast.unparse(node.returns)}"
        return head
    return ""


def file_signatures(source: str, *, limit: int = MAX_PER_FILE) -> list[str]:
    """Top-level defs/classes plus one level of methods. [] if unparsable."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    out: list[str] = []
    for node in tree.body:
        sig = _signature(node)
        if not sig:
            continue
        out.append(sig)
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                child_sig = _signature(child)
                if child_sig and not child.name.startswith("_"):
                    out.append("    " + child_sig)
                if len(out) >= limit:
                    break
        if len(out) >= limit:
            break
    return out[:limit]


def render_outline(
    project: Path,
    scope: str = "",
    *,
    max_files: int = MAX_OUTLINE_FILES,
    max_lines: int = MAX_OUTLINE_LINES,
) -> str:
    root = project.resolve()
    found = [
        (path, size)
        for path, size in iter_text_files(project, scope)
        if path.suffix in {".py", ".pyi"}
    ]
    if not found:
        return "(no .py files in scope)"
    lines = ["outline (signatures only — read a file before you patch it):"]
    body = 0
    shown = 0
    for path, _size in found:
        if shown >= max_files or body >= max_lines:
            break
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        sigs = file_signatures(source)
        if not sigs:
            continue
        shown += 1
        lines.append(rel_posix(path, root))
        for sig in sigs:
            lines.append(f"  {sig}")
            body += 1
            if body >= max_lines:
                lines.append("# … outline truncated. Narrow Scope: or pass --scope")
                break
    if len(lines) == 1:
        return "(no top-level defs or classes in scope)"
    remaining = len(found) - shown
    if remaining > 0 and body < max_lines:
        lines.append(f"# … {remaining} more files. Narrow Scope: or pass --scope")
    return "\n".join(lines)
