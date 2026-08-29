"""Where this repo is on disk. Deterministic. No model. Imports nothing.

Counting `parents[N]` from inside a module hard-codes that module's depth,
so moving it into a layer silently breaks it. Resolve the root once, here.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
KIT_SKILLS_DIR = REPO_ROOT / "skills"
EVAL_DIR = REPO_ROOT / "eval"
