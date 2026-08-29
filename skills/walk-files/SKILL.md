---
name: walk-files
description: Adds one pathlib helper that walks every file under a folder, such as finding by suffix, totalling sizes, or listing newest first. Use for file system work that says under, inside, recursively, or every file in a folder. Do not use for a single known path.
---

`rglob` reaches files in subfolders. `listdir` and `glob` only see the top
one, which is the usual reason an answer comes back short.

Action: edit
Path: pkg/find_files.py
from pathlib import Path


def find_files(folder: str, suffix: str) -> list[Path]:
    """Every file under folder whose name ends in suffix, sorted."""
    root = Path(folder)
    return sorted(path for path in root.rglob(f"*{suffix}") if path.is_file())


def folder_size(folder: str) -> int:
    """Total bytes of every file under folder."""
    return sum(path.stat().st_size for path in Path(folder).rglob("*") if path.is_file())
