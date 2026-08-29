"""Recover a near-miss `Find:` block. Deterministic. No model.

Exact-string replace is the right primitive — it fails loudly instead of
silently editing the wrong line. What it must not do is fail *unhelpfully*.
A small model reproduces the words of a line and loses its indentation, so
this module retries on whitespace-normalised lines and, when it still
cannot match, hands back the closest lines in the file so the next turn is
a fix rather than another guess.

Ambiguity is still refused: a normalised match that hits twice is not a
match.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

MAX_SUGGESTIONS = 3
MIN_RATIO = 0.6


def normalize(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


@dataclass(frozen=True)
class Match:
    text: str
    exact: bool


def _windows(lines: list[str], size: int) -> list[tuple[int, int]]:
    return [(i, i + size) for i in range(0, len(lines) - size + 1)]


def find_match(text: str, find: str) -> Match | None:
    """The literal `find` if unique, else a unique whitespace-only variant."""
    if not find:
        return None
    hits = text.count(find)
    if hits == 1:
        return Match(find, True)
    if hits > 1:
        return None
    wanted = [normalize(line) for line in find.strip("\n").splitlines()]
    if not wanted or not any(wanted):
        return None
    lines = text.splitlines()
    if len(wanted) > len(lines):
        return None
    found: list[str] = []
    for start, end in _windows(lines, len(wanted)):
        if [normalize(line) for line in lines[start:end]] == wanted:
            found.append("\n".join(lines[start:end]))
            if len(found) > 1:
                return None
    if len(found) != 1:
        return None
    return Match(found[0], False)


def suggestions(text: str, find: str, *, limit: int = MAX_SUGGESTIONS) -> list[str]:
    """Closest real lines, as `line_no: content`, for the refusal message."""
    head = normalize(find.strip("\n").splitlines()[0]) if find.strip() else ""
    if not head:
        return []
    scored: list[tuple[float, int, str]] = []
    for number, line in enumerate(text.splitlines(), 1):
        candidate = normalize(line)
        if not candidate:
            continue
        ratio = difflib.SequenceMatcher(None, head, candidate).ratio()
        if ratio >= MIN_RATIO:
            scored.append((ratio, number, line.rstrip()))
    scored.sort(key=lambda item: (-item[0], item[1]))
    if scored:
        return [f"{number}: {line}" for _ratio, number, line in scored[:limit]]
    return _same_opener(text, head, limit)


def _same_opener(text: str, head: str, limit: int) -> list[str]:
    """Nothing scored. Show lines that at least start the same way."""
    first = head.split(" ", 1)[0]
    if not first:
        return []
    out: list[str] = []
    for number, line in enumerate(text.splitlines(), 1):
        if normalize(line).startswith(first):
            out.append(f"{number}: {line.rstrip()}")
        if len(out) >= limit:
            break
    return out


def miss_message(text: str, find: str) -> str:
    close = suggestions(text, find)
    if not close:
        return (
            "Find: string not in file. Action: read that Path: first, "
            "then copy one whole line from it."
        )
    listed = "\n".join(f"  {item}" for item in close)
    return (
        "Find: string not in file. Closest lines in this file — copy one "
        f"whole line verbatim:\n{listed}"
    )


def align_indent(matched: str, replace: str) -> str:
    """Re-indent a Replace: that lost the leading whitespace of its target."""
    if not matched or not replace.strip():
        return replace
    first = matched.splitlines()[0]
    indent = first[: len(first) - len(first.lstrip())]
    if not indent:
        return replace
    lines = replace.splitlines()
    if lines[0].startswith((" ", "\t")):
        return replace
    return "\n".join(indent + line if line.strip() else line for line in lines)
