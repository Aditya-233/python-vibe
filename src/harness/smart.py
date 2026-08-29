"""Deterministic first steps for a small everyday model. No LLM."""

from __future__ import annotations

import re
from pathlib import Path

from harness.agent_tools import grep_py, read_py
from harness.project_brief import looks_like_question, question_symbol
from harness.skills import looks_like_add_feature

_DEF = re.compile(r"\b(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")


def def_hit_path(grep_text: str, symbol: str) -> str:
    wanted = symbol.strip()
    if not wanted or grep_text.startswith(("(no hits)", "bad regex")):
        return ""
    fallback = ""
    for line in grep_text.splitlines():
        if line.startswith("#") or line.count(":") < 2:
            continue
        path, _ln, content = line.split(":", 2)
        if not fallback:
            fallback = path
        if re.search(rf"\b(?:def|class)\s+{re.escape(wanted)}\b", content):
            return path
    return fallback


def locate_py(project: Path, query: str, scope: str = "") -> tuple[str, str]:
    if not query.strip():
        return "locate needs Query:", ""
    hits = grep_py(project, query, scope=scope)
    symbol = query.removeprefix("def ").removeprefix("class ").split()[0]
    path = def_hit_path(hits, symbol)
    if not path:
        return hits, ""
    body = read_py(project, path)
    return f"{hits}\n\n# auto-read {path}\n{body}", path


def prelude(project: Path, task: str, scope: str = "") -> tuple[str, str]:
    """Run locate before the model. Small models skip the first grep."""
    symbol = question_symbol(task)
    if not symbol and looks_like_add_feature(task):
        symbol = question_symbol(task) or ""
    if not symbol:
        return "", ""
    text, path = locate_py(project, symbol, scope)
    kind = "question" if looks_like_question(task) else "add-feature"
    header = f"Harness locate ({kind}) Query: {symbol}"
    if looks_like_question(task) and path:
        header += (
            "\nNext Action must be done. Do not locate, grep, or read."
        )
    elif looks_like_add_feature(task):
        header += (
            "\nNext Action must be patch with Append: (see the skill). "
            "Do not grep."
        )
    return f"{header}\n\n{text}", path


def refuse_early_done(task: str, last_path: str, located_path: str) -> str:
    if not looks_like_question(task):
        return ""
    symbol = question_symbol(task)
    if not symbol:
        return ""
    if located_path or (last_path and symbol.replace("_", "") in last_path.replace("_", "").lower()):
        return ""
    return (
        f"not done. Harness or you must locate {symbol} first. "
        f"Action: locate Query: {symbol}"
    )
