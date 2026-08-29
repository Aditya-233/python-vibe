"""Parse one agent turn. Deterministic. No model."""

from __future__ import annotations

import re
from dataclasses import dataclass

from harness.code import extract_python

_ACTION = re.compile(r"^Action:\s*(\w+)\s*$", re.MULTILINE | re.IGNORECASE)
_FIELD = re.compile(
    r"^(Path|Query|Pattern|Argv|Summary|Scope|Name):\s*(.+)$",
    re.MULTILINE,
)
_STOP = re.compile(
    r"^(Action|Path|Query|Pattern|Argv|Summary|Scope|Name|Find|Replace|Append|Add):\s*",
    re.IGNORECASE,
)


def _block(text: str, key: str) -> str:
    match = re.search(rf"^{key}:\s*(.*)$", text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    lines: list[str] = []
    first = match.group(1).rstrip()
    if first:
        lines.append(first)
    for line in text[match.end() :].lstrip("\n").splitlines():
        if _STOP.match(line):
            break
        lines.append(line.rstrip())
    return "\n".join(lines).rstrip()


@dataclass(frozen=True)
class AgentTurn:
    action: str
    path: str = ""
    query: str = ""
    pattern: str = ""
    argv: tuple[str, ...] = ()
    summary: str = ""
    source: str | None = None
    find: str = ""
    replace: str = ""
    scope: str = ""
    name: str = ""
    append: str = ""


_PREFERRED_WRITE = ("patch", "edit", "run", "locate", "done")
_PREFERRED_QUESTION = ("done", "locate", "grep", "read")


def parse_turn(text: str) -> AgentTurn | None:
    match = _ACTION.search(text)
    if not match:
        return None
    action = match.group(1).lower()
    fields = {m.group(1).lower(): m.group(2).strip() for m in _FIELD.finditer(text)}
    argv = tuple(part for part in fields.get("argv", "").split() if part)
    source = extract_python(text) if action == "edit" else None
    return AgentTurn(
        action=action,
        path=fields.get("path", ""),
        query=fields.get("query", ""),
        pattern=fields.get("pattern", ""),
        argv=argv,
        summary=fields.get("summary", ""),
        source=source,
        find=_block(text, "Find"),
        replace=_block(text, "Replace"),
        scope=fields.get("scope", ""),
        name=fields.get("name", ""),
        append=_block(text, "Append") or _block(text, "Add"),
    )


def parse_turn_smart(text: str, *, question: bool = False) -> AgentTurn | None:
    """Small models paste the Action menu. Pick one block by task kind."""
    matches = list(_ACTION.finditer(text))
    if len(matches) <= 1:
        return parse_turn(text)
    prefer = _PREFERRED_QUESTION if question else _PREFERRED_WRITE
    chosen = matches[0]
    for match in matches:
        if match.group(1).lower() in prefer:
            chosen = match
            break
    start = chosen.start()
    end = len(text)
    for match in matches:
        if match.start() > start:
            end = match.start()
            break
    return parse_turn(text[start:end])
