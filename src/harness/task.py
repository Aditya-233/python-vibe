"""Read the user's task and report what kind of work it asks for.

Every layer needs to know whether the task is a question, a request to add
code, a rename, or a request to create a package. These functions are the
single place that decision is made, so the layers above agree with each
other. This module imports nothing from the rest of the harness.

Rule shared by all of the writer functions below: a question is never a
write, so each one returns False when the task is a question.
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


def looks_like_design_loop(task: str) -> bool:
    """Review, then one-split, then review again until the scan is clean."""
    return looks_like_review(task) or looks_like_refactor(task)


def looks_like_review(task: str) -> bool:
    if looks_like_new_package(task) or looks_like_ship(task):
        return False
    if looks_like_refactor(task) and not re.search(r"\breview\b", task, re.I):
        return False
    return bool(_REVIEW.search(task.lower()))


_BUG = re.compile(r"\b(fix|bug|nameerror|crash|defect)\b", re.I)


def looks_like_bugfix(task: str) -> bool:
    """A concrete fix that is not a rename, package, review, or ship."""
    if looks_like_question(task):
        return False
    if (
        looks_like_new_package(task)
        or looks_like_fix_smell(task)
        or looks_like_ship(task)
        or looks_like_review(task)
        or looks_like_refactor(task)
    ):
        return False
    return bool(_BUG.search(task))


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


_REVIEW_CODE = re.compile(r"\b(review|check|find bugs?|defects?|audit)\b")


def looks_like_review_code(task: str) -> bool:
    """True when the task asks for problems to be reported, not fixed."""
    text = task.strip().lower()
    if looks_like_new_package(text) or looks_like_ship(text):
        return False
    if looks_like_add_feature(text) or looks_like_fix_smell(text):
        return False
    return bool(_REVIEW_CODE.search(text))


_IDENTIFIER = re.compile(r"[A-Za-z_]\w*_\w+|\w+\s*\(|\S+\.py\b|\b[A-Za-z]\w*/\S+")


def names_something_concrete(task: str) -> bool:
    """True when the task names a file, a call, or a snake_case identifier.

    `question_symbol` will return any five-letter word, including ordinary
    English like "clean", so it cannot be used on its own to decide whether
    the agent has been told what to work on.
    """
    return bool(_IDENTIFIER.search(task))


def looks_unclear(task: str) -> bool:
    """True when the task is short and names nothing the agent can search for.

    A task like "clean this up" gives the agent no file and no symbol, so
    asking one question is better than guessing which file to change.
    """
    text = task.strip()
    if looks_like_question(text) or looks_like_ship(text):
        return False
    if names_something_concrete(text):
        return False
    # If the kind of work is recognised, the agent has a skill and a first
    # action for it, so a short task is still workable.
    known = (
        looks_like_add_feature,
        looks_like_fix_smell,
        looks_like_new_package,
        looks_like_review_code,
        looks_like_design_loop,
        looks_like_bugfix,
    )
    if any(check(text) for check in known):
        return False
    return len(text.split()) <= 6


_TASK_PATH = re.compile(r"[\w./\\-]+\.(?:py|pyi|md)\b")


def task_paths(task: str) -> tuple[str, ...]:
    """File paths named in the task, with forward slashes, in order.

    A task that says "in src/harness/model/engine.py ..." has already told
    the agent which file to open. Searching for a word out of that path
    instead finds every file in the project.
    """
    seen: list[str] = []
    for hit in _TASK_PATH.findall(task):
        cleaned = hit.replace("\\", "/").strip("./,;:()[]'\"")
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return tuple(seen)


def named_project_file(task: str, project) -> str:
    """The one file the task names that exists in the project, or "".

    Empty when the task names none, or names more than one, because then
    there is nothing unambiguous to act on.
    """
    from pathlib import Path as _Path

    root = _Path(project).resolve()
    found = [rel for rel in task_paths(task) if (root / rel).is_file()]
    return found[0] if len(found) == 1 else ""
