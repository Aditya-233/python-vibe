"""Qwen2.5-Coder-0.5B 4-bit — fits a cheap cloud box (~400 MB)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from finetune.paths import ADAPTERS_ROOT, FUSED_ROOT
from finetune.systems import PYTHON_VIBE_SYSTEM


HF_USER = "YauhenBichel"


@dataclass(frozen=True)
class ModelSpec:
    name: str
    mlx_base: str
    ollama_base: str
    hf_repo: str
    system: str
    adapter_path: Path
    fused_path: Path
    ram_mb: int


SPECS: dict[str, ModelSpec] = {
    "python-vibe": ModelSpec(
        name="python-vibe",
        mlx_base="mlx-community/Qwen2.5-Coder-0.5B-Instruct-4bit",
        ollama_base="qwen2.5-coder:0.5b",
        hf_repo=f"{HF_USER}/python-vibe-0.5b",
        system=PYTHON_VIBE_SYSTEM,
        adapter_path=ADAPTERS_ROOT / "python-vibe",
        fused_path=FUSED_ROOT / "python-vibe",
        ram_mb=400,
    ),
}
