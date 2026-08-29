"""Deterministic first steps for a small everyday model. No LLM."""

from __future__ import annotations

import re
from pathlib import Path

from harness.agent_tools import grep_py, read_py
from harness.project_brief import looks_like_question, question_symbol
from harness.skills import looks_like_add_feature
from harness.style import looks_like_fix_smell, looks_like_new_package, smell_symbol

_DEF = re.compile(r"\b(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")


def signature_line(text: str, symbol: str) -> str:
    if not symbol:
        return ""
    needle = f"def {symbol}("
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            continue
        if raw.count(":") >= 2 and not raw.lstrip().startswith(("def ", "class ", "async ")):
            line = raw.split(":", 2)[-1].strip()
        if needle in line:
            return line.rstrip()
    return ""


def return_annotation(signature: str) -> str:
    if "->" not in signature:
        return ""
    return signature.split("->", 1)[1].rstrip(":").strip()


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def refuse_shallow_done(task: str, summary: str, signature: str) -> str:
    if not looks_like_question(task):
        return ""
    wanted = return_annotation(signature)
    if not wanted:
        return ""
    if _compact(wanted) in _compact(summary or ""):
        return ""
    return (
        f"too thin. Action: done Summary: must quote {wanted} "
        f"from {signature}"
    )


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
    if looks_like_new_package(task):
        return "", ""
    symbol = smell_symbol(task) if looks_like_fix_smell(task) else question_symbol(task)
    if not symbol and looks_like_add_feature(task):
        symbol = question_symbol(task) or ""
    if not symbol:
        return "", ""
    text, path = locate_py(project, symbol, scope)
    if looks_like_question(task):
        kind = "question"
    elif looks_like_fix_smell(task):
        kind = "fix-smell"
    else:
        kind = "add-feature"
    header = f"Harness locate ({kind}) Query: {symbol}"
    if looks_like_question(task) and path:
        header += (
            "\nNext Action must be done. Do not locate, grep, or read."
        )
        sig = signature_line(text, symbol)
        if return_annotation(sig):
            header += f"\nSummary must quote the -> type from: {sig}"
    elif looks_like_fix_smell(task) and path:
        header += (
            "\nNext Action must be patch Find: the old def line "
            "Replace: a readable snake_case name. Do not grep."
        )
    elif looks_like_add_feature(task):
        header += (
            "\nNext Action must be patch with Append: (see the skill). "
            "Do not grep."
        )
    return f"{header}\n\n{text}", path


_QUESTION_WRITE = frozenset({"patch", "edit", "run"})
_QUESTION_REEXPLORE = frozenset({"read", "locate", "grep"})


def refuse_redundant_locate(task: str, action: str, prelude_ran: bool) -> str:
    if action != "locate" or not prelude_ran:
        return ""
    if looks_like_question(task):
        return (
            "already located. Action: done Summary: quote the -> type."
        )
    if looks_like_add_feature(task):
        return (
            "already located. Action: patch Path: + Append: the new function."
        )
    return ""


def refuse_question_write(task: str, action: str) -> str:
    if looks_like_question(task) and action in _QUESTION_WRITE:
        return (
            "Questions do not edit. "
            "Action: done Summary: quote return or refuse from # auto-read."
        )
    return ""


def refuse_redundant_explore(
    task: str, action: str, path: str, located_path: str
) -> str:
    if not looks_like_question(task) or not located_path:
        return ""
    if action not in _QUESTION_REEXPLORE:
        return ""
    rel = path.replace("\\", "/").lstrip("./")
    located = located_path.replace("\\", "/").lstrip("./")
    same = (not rel) or rel == located or located.endswith(rel) or rel.endswith(located)
    if not same:
        return ""
    return (
        f"already have # auto-read {located}. "
        "Action: done Summary: quote return or refuse from that file."
    )


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
