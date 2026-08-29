"""Small vs large project brief. Deterministic. No model.

Small repos get a file list (comfortable daily explore / edit / run).
Large repos get a harness: map, --scope, do not read everything.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from harness.project_scan import SKIP_DIR

TEXT_SUFFIXES = {".py", ".pyi", ".md"}
SMALL_MAX_FILES = 40
SMALL_MAX_BYTES = 200_000
MAP_MAX_ENTRIES = 80
QUESTION_PREFIXES = ("what ", "why ", "how ", "where ", "which ", "explain ", "list ", "who ")
_SYMBOL = re.compile(r"\b([a-z_][a-z0-9_]{4,})\b")
_SYMBOL_SKIP = frozenset(
    {
        "what",
        "does",
        "this",
        "that",
        "with",
        "from",
        "return",
        "where",
        "which",
        "explain",
        "refuse",
        "about",
        "after",
        "before",
        "source",
        "apply",
    }
)


@dataclass(frozen=True)
class ProjectBrief:
    kind: str
    files: int
    bytes: int
    listed: tuple[tuple[str, int], ...]
    tops: tuple[tuple[str, int], ...]


def resolve_scope(project: Path, scope: str) -> Path:
    root = project.resolve()
    if not scope or scope in {".", "./"}:
        return root
    path = (root / scope).resolve() if not Path(scope).is_absolute() else Path(scope).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{path} is outside {root}") from exc
    if path.is_file():
        rel = path.relative_to(root)
        parent = rel.parent.as_posix() if rel.parent != Path(".") else "."
        raise ValueError(
            f"scope is a file ({rel}). Use Path: {rel} or Scope: {parent}"
        )
    if not path.is_dir():
        raise ValueError(f"scope is not a directory: {scope}")
    return path


def looks_like_question(task: str) -> bool:
    text = task.strip().lower()
    return text.endswith("?") or text.startswith(QUESTION_PREFIXES)


def question_symbol(task: str) -> str:
    hits = [
        word
        for word in _SYMBOL.findall(task.lower())
        if word not in _SYMBOL_SKIP
    ]
    return hits[0] if hits else ""


def iter_text_files(project: Path, scope: str = "") -> list[tuple[Path, int]]:
    root = project.resolve()
    base = resolve_scope(project, scope) if scope else root
    found: list[tuple[Path, int]] = []
    for suffix in ("*.py", "*.pyi", "*.md"):
        for path in base.rglob(suffix):
            if not path.is_file():
                continue
            if any(part in SKIP_DIR for part in path.parts):
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            found.append((path, size))
    found.sort(key=lambda item: str(item[0].relative_to(root)))
    return found


def classify_project(project: Path, scope: str = "") -> ProjectBrief:
    root = project.resolve()
    found = iter_text_files(project, scope)
    total = sum(size for _path, size in found)
    listed = tuple(
        (str(path.relative_to(root)), size) for path, size in found[:SMALL_MAX_FILES]
    )
    counts: dict[str, int] = {}
    for path, _size in found:
        rel = path.relative_to(root)
        top = rel.parts[0] if len(rel.parts) > 1 else str(rel)
        counts[top] = counts.get(top, 0) + 1
    tops = tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:16])
    kind = "small" if len(found) <= SMALL_MAX_FILES and total <= SMALL_MAX_BYTES else "large"
    return ProjectBrief(
        kind=kind,
        files=len(found),
        bytes=total,
        listed=listed,
        tops=tops,
    )


def _kb(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    return f"{n / 1024:.1f} KB"


def render_brief(brief: ProjectBrief, *, scope: str = "") -> str:
    header = (
        f"Mode: {brief.kind}  files={brief.files}  size={_kb(brief.bytes)}"
        + (f"  scope={scope}" if scope else "")
    )
    if brief.kind == "small":
        lines = [
            header,
            "Small project — explore, edit, and run on this laptop.",
            "You can read every listed file. Prefer Action: patch for one-line fixes.",
            "Questions: read, then Action: done with the answer. Do not edit unless asked.",
            "Files:",
        ]
        for rel, size in brief.listed:
            lines.append(f"  {rel}  {_kb(size)}")
        return "\n".join(lines)
    lines = [
        header,
        "Large project — use the harness. Do not read the whole repo.",
        "Start with Action: map. Then Action: grep with a tight Query.",
        "Pass --scope <subdir> (or Action: map + Scope:) to stay inside one tree.",
        "Do not Action: done after one tiny __init__.py.",
        "Top-level (file counts):",
    ]
    for name, count in brief.tops:
        lines.append(f"  {name}/  {count}" if not name.endswith((".py", ".md")) else f"  {name}  {count}")
    return "\n".join(lines)


def render_map(project: Path, scope: str = "", *, max_entries: int = MAP_MAX_ENTRIES) -> str:
    root = project.resolve()
    found = iter_text_files(project, scope)
    if not found:
        return "(no .py/.md files in scope)"
    lines = [f"map {scope or '.'}  {len(found)} files  {_kb(sum(s for _p, s in found))}"]
    for path, size in found[:max_entries]:
        lines.append(f"  {path.relative_to(root)}  {_kb(size)}")
    if len(found) > max_entries:
        lines.append(
            f"# … {len(found) - max_entries} more. Narrow Scope: or pass --scope"
        )
    return "\n".join(lines)


def start_hint(brief: ProjectBrief, task: str) -> str:
    if brief.kind == "large":
        return "Start with Action: map, then grep. Do not Action: done yet."
    if looks_like_question(task):
        symbol = question_symbol(task)
        if symbol:
            return (
                f"This is a question. First Action: grep Query: {symbol}. "
                "Then Action: read the file that defines it. "
                "Then Action: done with the answer. Do not edit unless asked."
            )
        return (
            "This is a question. Read what you need, then Action: done with the answer. "
            "Do not edit unless asked."
        )
    from harness.skills import looks_like_add_feature

    if looks_like_add_feature(task):
        return (
            "This is an add-feature task. Grep first. If it is missing, add the "
            "smallest change plus a test, then run. Do not invent extras."
        )
    return "Start with Action: grep or Action: read. Prefer patch for one-line bugs."
