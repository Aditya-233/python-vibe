"""What the user asked for. Deterministic. No model. Imports nothing.

This is the bottom of the harness. Every other layer reads the task the
same way, so the predicates live here and not in whichever module happened
to need them first — that is what let `project_brief`, `skills`, and
`style` import each other in a circle.

One rule holds the set together: a question is never a write. Every
`looks_like_*` writer predicate returns False for a question.
"""

from __future__ import annotations

import re

QUESTION_PREFIXES = (
    "what ",
    "why ",
    "how ",
    "where ",
    "which ",
    "explain ",
    "list ",
    "who ",
)
_SYMBOL = re.compile(r"\b([a-z_][a-z0-9_]{4,})\b")
_SYMBOL_SKIP = frozenset(
    {
        "about",
        "after",
        "apply",
        "before",
        "does",
        "explain",
        "feature",
        "from",
        "function",
        "refuse",
        "return",
        "source",
        "that",
        "this",
        "what",
        "where",
        "which",
        "with",
    }
)
_ADD_START = re.compile(r"^(please\s+)?(add|implement|introduce|create)\b|new feature")
_SMELL = re.compile(
    r"\b(code smell|smell|rename|readable name|human[- ]readable|clean up|cleanup)\b"
)
_PACKAGE = re.compile(
    r"\b(scaffold|new package|new project|"
    r"create a package|create a project|create a pkg)\b"
)
_REVIEW = re.compile(
    r"\b(review|system design|architecture|project structure|design review)\b"
)
_REFACTOR = re.compile(
    r"\b(refactor|extract (a )?function|split (the )?module|move function)\b"
)
_RENAME = re.compile(
    r"\brename\s+([A-Za-z_][A-Za-z0-9_]*)\s+to\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.I,
)


def looks_like_question(task: str) -> bool:
    text = task.strip().lower()
    return text.endswith("?") or text.startswith(QUESTION_PREFIXES)


def question_symbol(task: str) -> str:
    """The first word in the task that could be a symbol name."""
    hits = [word for word in _SYMBOL.findall(task.lower()) if word not in _SYMBOL_SKIP]
    return hits[0] if hits else ""


def looks_like_new_package(task: str) -> bool:
    if looks_like_question(task):
        return False
    return bool(_PACKAGE.search(task.strip().lower()))


def looks_like_fix_smell(task: str) -> bool:
    if looks_like_question(task):
        return False
    return bool(_SMELL.search(task.strip().lower()))


_SHIP = re.compile(
    r"(#\d+|\bissue\s+#?\d+|\bpr\s+#?\d+|\bpull request\b|"
    r"\bopen a pr\b|\bcreate a pr\b|\bcommit\b|\bpush\b|\bmerge\b)",
    re.I,
)
_ISSUE_NUM = re.compile(r"(?:#|issue\s+#?|pr\s+#?)(\d+)", re.I)


def looks_like_ship(task: str) -> bool:
    if looks_like_question(task) or looks_like_new_package(task):
        return False
    return bool(_SHIP.search(task))


def looks_like_merge(task: str) -> bool:
    return looks_like_ship(task) and bool(re.search(r"\bmerge\b", task, re.I))


def issue_number(task: str) -> str:
    match = _ISSUE_NUM.search(task)
    return match.group(1) if match else ""


def looks_like_refactor(task: str) -> bool:
    if looks_like_question(task) or looks_like_new_package(task) or looks_like_ship(task):
        return False
    return bool(_REFACTOR.search(task.lower()))


def looks_like_review(task: str) -> bool:
    if looks_like_new_package(task) or looks_like_ship(task):
        return False
    if looks_like_refactor(task) and not re.search(r"\breview\b", task, re.I):
        return False
    return bool(_REVIEW.search(task.lower()))


def looks_like_add_feature(task: str) -> bool:
    text = task.strip().lower()
    if looks_like_question(text):
        return False
    if (
        looks_like_new_package(text)
        or looks_like_fix_smell(text)
        or looks_like_ship(text)
        or looks_like_review(text)
        or looks_like_refactor(text)
    ):
        return False
    return bool(_ADD_START.search(text))


def rename_pair(task: str) -> tuple[str, str]:
    """`rename calc to total_price` -> ("calc", "total_price")."""
    match = _RENAME.search(task)
    return (match.group(1), match.group(2)) if match else ("", "")


_SMELL_SKIP = frozenset(
    {
        "and",
        "clean",
        "cleanup",
        "code",
        "for",
        "human",
        "into",
        "name",
        "names",
        "readable",
        "rename",
        "smell",
        "that",
        "the",
        "this",
        "with",
    }
)


def smell_symbol(task: str) -> str:
    """The name a rename task is about: `rename calc to x` -> "calc"."""
    old, _new = rename_pair(task)
    if old:
        return old
    names = re.findall(r"\b([a-z_][a-z0-9_]{2,})\b", task.lower())
    hits = [name for name in names if name not in _SMELL_SKIP]
    return hits[-1] if hits else ""


def rename_target(task: str) -> str:
    """The name a rename task wants: `rename calc to x` -> "x"."""
    return rename_pair(task)[1]
