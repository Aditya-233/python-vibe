"""Load MLX LoRA or Ollama once; reuse for a batch of prompts."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from finetune.huggingface_store import BEST_ADAPTER, ensure_adapters
from finetune.models import SPECS
from finetune.paths import PROJECT_ROOT


def mlx_pythons() -> list[str]:
    home = Path.home()
    return [
        sys.executable,
        str(PROJECT_ROOT / ".venv" / "bin" / "python"),
        str(home / "DevBox/python-vibe/.venv/bin/python"),
        str(home / "DevBox/tracer-cloud/llm-finetunes/.venv/bin/python"),
        str(home / "DevBox/molecare/skincare-qa/.venv/bin/python"),
    ]


def has_mlx(exe: str) -> bool:
    if not Path(exe).is_file():
        return False
    probe = subprocess.run([exe, "-c", "import mlx_lm"], capture_output=True)
    return probe.returncode == 0


def reexec_for_mlx() -> None:
    try:
        import mlx_lm  # noqa: F401
        return
    except ImportError:
        pass
    for exe in mlx_pythons():
        if exe == sys.executable:
            continue
        if has_mlx(exe):
            os.execv(exe, [exe, *sys.argv])
    sys.exit("mlx-lm missing. Use the Homebrew 3.13 venv or pass --engine ollama")


def _stage_best(adapter_dir: Path) -> Path:
    ckpt = adapter_dir / BEST_ADAPTER
    if not ckpt.is_file():
        sys.exit(f"no best checkpoint: {ckpt}")
    staging = adapter_dir.parent / "python-vibe-100"
    staging.mkdir(parents=True, exist_ok=True)
    dest = staging / "adapters.safetensors"
    cfg = staging / "adapter_config.json"
    src_cfg = adapter_dir / "adapter_config.json"
    if dest.exists() or dest.is_symlink():
        dest.unlink()
    dest.symlink_to(ckpt.resolve())
    if src_cfg.is_file():
        if cfg.exists() or cfg.is_symlink():
            cfg.unlink()
        cfg.symlink_to(src_cfg.resolve())
    return staging


def make_generate(engine: str, max_tokens: int) -> tuple[str, Callable[[str], str]]:
    if engine == "auto":
        engine = "mlx" if any(has_mlx(p) for p in mlx_pythons()) else "ollama"
    if engine == "mlx":
        return _mlx_generate(max_tokens)
    return _ollama_generate()


def _mlx_generate(max_tokens: int) -> tuple[str, Callable[[str], str]]:
    reexec_for_mlx()
    from mlx_lm import generate, load

    spec = SPECS["python-vibe"]
    local = ensure_adapters(spec)
    adapter = _stage_best(local) if (local / BEST_ADAPTER).is_file() else local
    model, tokenizer = load(spec.mlx_base, adapter_path=str(adapter))
    history: list[dict[str, str]] = []

    def generate_once(prompt: str) -> str:
        messages = (
            [{"role": "system", "content": spec.system}]
            + history
            + [{"role": "user", "content": prompt}]
        )
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        return generate(model, tokenizer, prompt=text, max_tokens=max_tokens)

    generate_once.history = history  # type: ignore[attr-defined]
    return f"mlx-lora:{adapter.name}", generate_once


def _ollama_generate() -> tuple[str, Callable[[str], str]]:
    from harness.ollama_generate import OllamaGenerate

    spec = SPECS["python-vibe"]
    backend = OllamaGenerate(spec.ollama_base, spec.system)
    if not backend.healthy():
        sys.exit(f"ollama {backend.host} is down")
    history: list[dict[str, str]] = []

    def generate_once(prompt: str) -> str:
        return backend(prompt, history)

    generate_once.history = history  # type: ignore[attr-defined]
    return f"ollama:{spec.ollama_base}", generate_once
