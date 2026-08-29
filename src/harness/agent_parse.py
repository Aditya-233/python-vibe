"""Parse one agent turn. Deterministic. No model."""

from __future__ import annotations

import re
from dataclasses import dataclass

from harness.code import extract_python

_ACTION = re.compile(r"^Action:\s*(\w+)\s*$", re.MULTILINE | re.IGNORECASE)
_FIELD = re.compile(
    r"^(Path|Query|Pattern|Argv|Summary|Find|Replace):\s*(.+)$", re.MULTILINE
)


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
        find=fields.get("find", ""),
        replace=fields.get("replace", ""),
    )
