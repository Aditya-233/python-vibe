"""Append redacted agent turns. Never store raw keys or home paths."""

from __future__ import annotations

import json
import re
from pathlib import Path

_SECRET = re.compile(
    r"(AKIA[0-9A-Z]{16}|sk-ant-[A-Za-z0-9_\-]{20,}|ghp_[A-Za-z0-9]{20,}"
    r"|HF_TOKEN=|-----BEGIN )"
)
_HOME = re.compile(r"/Users/[^/\s]+")


def redact(text: str) -> str:
    if _SECRET.search(text):
        return "[redacted]"
    return _HOME.sub("/Users/you", text)


def append_turn(path: Path, row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = {key: redact(str(value)) for key, value in row.items()}
    if any(v == "[redacted]" for v in clean.values()):
        return
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(clean, ensure_ascii=False) + "\n")
