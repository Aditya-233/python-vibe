---
name: use-archive
description: Adds one zipfile or tarfile helper that packs a folder or lists what an archive holds. Use for zip, unzip, tar, archive, compress, or extract. Stdlib only, no shell.
---

`zipfile` and `tarfile` are in the standard library. Never shell out to
`zip` or `tar`. Write paths relative to the folder, so the archive does not
carry the whole path from the machine that made it.

Action: edit
Path: pkg/make_zip.py
import zipfile
from pathlib import Path


def make_zip(folder: str, target: str) -> Path:
    """Write every file under folder into a zip at target."""
    root = Path(folder)
    destination = Path(target)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root).as_posix())
    return destination


def list_zip(path: str) -> list[str]:
    """The names held in a zip archive."""
    with zipfile.ZipFile(path) as archive:
        return sorted(archive.namelist())
