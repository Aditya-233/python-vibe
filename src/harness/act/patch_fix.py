"""Match a `Find:` block against a file, and explain a failed match.

`patch` replaces an exact substring. Exact matching is deliberate: it fails
instead of editing a line the user did not mean. The cost is that a small
model, which often reproduces the words of a line but not its indentation,
gets no way forward when the match fails.

These functions add two recoveries that do not weaken the guarantee:

* Retry the match ignoring differences in whitespace only. If that matches
  in exactly one place, use it. If it matches in more than one place, the
  match is rejected rather than guessed.
* When there is still no match, return the lines in the file that are most
  similar, so the next attempt can copy a real line.
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
    """Find where `find` occurs in `text`.

    Returns the exact text to replace, and whether it matched exactly.
    Returns None when there is no match, or when a whitespace-insensitive
    match occurs in more than one place.
    """
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
    """Return the lines in `text` most similar to `find`, for an error message.

    Each entry is formatted as "line number: line content".
    """
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
    """Give `replace` the leading whitespace of the line it will replace.

    A small model often reproduces a line without its indentation. If the
    replacement has no leading whitespace and the matched text does, the
    replacement is indented to match.
    """
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
