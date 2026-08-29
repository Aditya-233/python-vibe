"""Locations inside this repository.

A module that finds the repository root by counting parent directories
stops working when the module is moved to a different directory depth. The
root is resolved once here and imported everywhere else.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
KIT_SKILLS_DIR = REPO_ROOT / "skills"
EVAL_DIR = REPO_ROOT / "eval"
