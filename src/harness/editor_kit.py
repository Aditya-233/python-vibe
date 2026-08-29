"""Copy drop-in editor settings into a project. No model."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from harness.paths import REPO_ROOT

KINDS = ("vscode", "continue", "cursor", "zed")


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
    if kind == "zed":
        dest = root / ".zed" / "settings.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(_zed_settings(root, dest), encoding="utf-8")
        written.append(dest)
        return written
    dest = root / ".cursor" / "mcp.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_mcp_json(root, kit_dir() / "cursor" / "mcp.json"), encoding="utf-8")
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


def _stdio_server(project: Path) -> dict:
    """Command an editor will spawn. Absolute interpreter + project."""
    server = {
        "command": Path(sys.executable).as_posix(),
        "args": ["-m", "harness", "mcp", "--project", project.as_posix()],
    }
    if not _harness_is_importable():
        server["env"] = {"PYTHONPATH": (REPO_ROOT / "src").as_posix()}
    return server


def _fill_server(server: dict, project: Path) -> dict:
    server["command"] = Path(sys.executable).as_posix()
    server["args"] = [
        project.as_posix() if arg == "__PROJECT__" else arg
        for arg in server["args"]
    ]
    if not _harness_is_importable():
        server["env"] = {"PYTHONPATH": (REPO_ROOT / "src").as_posix()}
    return server


def _mcp_json(project: Path, template_path: Path) -> str:
    template = json.loads(template_path.read_text(encoding="utf-8"))
    server = template["mcpServers"]["python-vibe"]
    template["mcpServers"]["python-vibe"] = _fill_server(server, project)
    return json.dumps(template, indent=2) + "\n"


def _zed_settings(project: Path, dest: Path) -> str:
    """Merge python-vibe into .zed/settings.json. Do not drop other keys."""
    incoming = _stdio_server(project)
    data: dict = {}
    if dest.is_file():
        try:
            loaded = json.loads(dest.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            loaded = {}
        if isinstance(loaded, dict):
            data = loaded
    servers = data.setdefault("context_servers", {})
    if not isinstance(servers, dict):
        servers = {}
        data["context_servers"] = servers
    servers["python-vibe"] = incoming
    return json.dumps(data, indent=2) + "\n"
