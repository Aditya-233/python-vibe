"""Copy drop-in editor settings into a project. No model."""

from __future__ import annotations

import sys
from pathlib import Path

from harness.paths import REPO_ROOT

KINDS = ("vscode", "continue", "cursor")


def kit_dir() -> Path:
    packaged = Path(__file__).resolve().parent / "kit_editors"
    if packaged.is_dir():
        return packaged
    return REPO_ROOT / "editors"


def install_editors(project: Path, kind: str) -> list[Path]:
    """Write the drop-in files for `kind` into `project`. Returns written paths."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    root = project.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if kind == "vscode":
        dest = root / ".vscode" / "tasks.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            (kit_dir() / "vscode" / "tasks.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        written.append(dest)
        return written
    if kind == "continue":
        dest = root / ".continue" / "config.yaml"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            (kit_dir() / "vscode" / "continue.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        written.append(dest)
        return written
    dest = root / ".cursor" / "mcp.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_cursor_mcp(root), encoding="utf-8")
    written.append(dest)
    return written


def _cursor_mcp(project: Path) -> str:
    template = (kit_dir() / "cursor" / "mcp.json").read_text(encoding="utf-8")
    return (
        template.replace("__PYTHON__", Path(sys.executable).as_posix())
        .replace("__PROJECT__", project.as_posix())
    )
