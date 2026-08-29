"""Qwen2.5-Coder-0.5B 4-bit — fits a cheap cloud box (~400 MB)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from finetune.paths import ADAPTERS_ROOT, FUSED_ROOT
from finetune.systems import PYTHON_VIBE_SYSTEM

# Published weights anyone may download. Not a contributor identity.
# Uploads never use this unless HF_REPO / HF_USER / `hf auth login` say so.
OFFICIAL_HF_REPO = "YauhenBichel/python-vibe-0.5b"


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

    @property
    def hf_slug(self) -> str:
        return self.hf_repo.rsplit("/", 1)[-1]


def logged_in_hf_user() -> str | None:
    try:
        from huggingface_hub import whoami

        info = whoami()
    except Exception:
        return None
    if isinstance(info, dict):
        name = info.get("name")
        if isinstance(name, str) and name:
            return name
    return None


def publish_hf_repo(spec: ModelSpec) -> str:
    """Where *this machine* may upload. Never defaults to the official account."""
    override = (os.environ.get("HF_REPO") or os.environ.get("PYTHON_VIBE_HF_REPO") or "").strip()
    if override:
        return override
    user = (os.environ.get("HF_USER") or "").strip() or logged_in_hf_user()
    if not user:
        raise SystemExit(
            "Refusing to upload to the official Hub repo. Set HF_USER or HF_REPO "
            f"to your namespace (example: HF_USER=alice → alice/{spec.hf_slug}), "
            "or run `hf auth login` as yourself. "
            f"People download official weights from {spec.hf_repo}."
        )
    return f"{user}/{spec.hf_slug}"


SPECS: dict[str, ModelSpec] = {
    "python-vibe": ModelSpec(
        name="python-vibe",
        mlx_base="mlx-community/Qwen2.5-Coder-0.5B-Instruct-4bit",
        ollama_base="qwen2.5-coder:0.5b",
        hf_repo=OFFICIAL_HF_REPO,
        system=PYTHON_VIBE_SYSTEM,
        adapter_path=ADAPTERS_ROOT / "python-vibe",
        fused_path=FUSED_ROOT / "python-vibe",
        ram_mb=400,
    ),
}
