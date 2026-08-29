---
name: write-paths
description: Adds one pathlib helper for venv, home, or project paths on Windows, macOS, and Linux. Use for filesystem and platform work. Do not use for questions.
---

One module. pathlib. No os.path.join. No /Users/ or C:\. No /tmp.

Action: edit
Path: pkg/paths.py
import os
from pathlib import Path


def interpreter_in_venv(venv: Path, *, windows: bool | None = None) -> Path:
    on_windows = os.name == "nt" if windows is None else windows
    if on_windows:
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def user_home() -> Path:
    return Path.home()
