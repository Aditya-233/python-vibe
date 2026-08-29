---
name: compare-things
description: Adds one helper that reports the difference between two files, two folders, or two dicts. Use for compare, diff, changed, missing, or what is different. Returns the differences, it does not print them.
---

Return the differences so a caller can act on them. `difflib` for text,
set arithmetic for keys.

Action: edit
Path: pkg/compare.py
from pathlib import Path


def diff_lines(left: str, right: str) -> list[str]:
    """Lines present in left but not in right, in order."""
    right_lines = set(Path(right).read_text(encoding="utf-8").splitlines())
    return [
        line
        for line in Path(left).read_text(encoding="utf-8").splitlines()
        if line not in right_lines
    ]


def changed_keys(left: dict, right: dict) -> list[str]:
    """Keys whose values differ, including keys missing from either side."""
    missing = object()
    return sorted(
        key
        for key in set(left) | set(right)
        if left.get(key, missing) != right.get(key, missing)
    )
