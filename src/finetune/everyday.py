"""Everyday laptop brain vs the public 0.5B sidecar."""

from __future__ import annotations

import os

# 0.5B stays on the Hub and in smoke. This is what agent.py should use daily.
DEFAULT_EVERYDAY_OLLAMA = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
TINY_OLLAMA = "qwen2.5-coder:0.5b"
EVERYDAY_OLLAMA_CHOICES = (
    "llama3.1:8b",
    "qwen2.5-coder:7b",
    "qwen2.5-coder:14b",
    "qwen2.5-coder:32b",
)
EVERYDAY_MLX_BASE = "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"
EVERYDAY_SLUG = "python-vibe-8b"
TINY_MODELS = frozenset(
    {
        TINY_OLLAMA,
        "qwen2.5-coder:0.5b",
        "python-vibe",
        "python-vibe-0.5b",
    }
)


def is_tiny_model(name: str) -> bool:
    lowered = name.strip().lower()
    return lowered in TINY_MODELS or lowered.endswith(":0.5b") or lowered.endswith("-0.5b")
