"""Default locations for this project's outputs."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"
ADAPTERS_ROOT = PROJECT_ROOT / "adapters"
FUSED_ROOT = PROJECT_ROOT / "fused"
CONFIGS_ROOT = PROJECT_ROOT / "configs"
