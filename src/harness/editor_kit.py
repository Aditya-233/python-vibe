"""Copy drop-in editor settings into a project. No model."""

from __future__ import annotations

import json
import os
import subprocess
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


def _harness_is_importable() -> bool:
    """True when a bare interpreter can `import harness` with no help.

    An editor starts the server as a plain subprocess, without whatever
    PYTHONPATH the person had set when they generated the file.
    """
    probe = subprocess.run(
        [sys.executable, "-c", "import harness"],
        capture_output=True,
        env={"PATH": os.environ.get("PATH", "")},
        check=False,
    )
    return probe.returncode == 0


def _cursor_mcp(project: Path) -> str:
    template = json.loads(
        (kit_dir() / "cursor" / "mcp.json").read_text(encoding="utf-8")
    )
    server = template["mcpServers"]["python-vibe"]
    server["command"] = Path(sys.executable).as_posix()
    server["args"] = [
        project.as_posix() if arg == "__PROJECT__" else arg
        for arg in server["args"]
    ]
    if not _harness_is_importable():
        # Running from a source checkout. Carry the path the editor will not
        # have, so the file works without `pip install -e .` as well.
        server["env"] = {"PYTHONPATH": (REPO_ROOT / "src").as_posix()}
    return json.dumps(template, indent=2) + "\n"
