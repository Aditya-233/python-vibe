---
license: apache-2.0
base_model: Qwen/Qwen2.5-Coder-0.5B-Instruct
library_name: mlx
pipeline_tag: text-generation
tags:
  - mlx
  - lora
  - qwen2.5-coder
  - python
  - code-generation
language:
  - en
---

# python-vibe-0.5b

Public **LoRA adapters** (step 100) on **Qwen2.5-Coder-0.5B-Instruct** (4-bit MLX)
for short Python vibe-coding drafts. Owned by
[YauhenBichel](https://huggingface.co/YauhenBichel).

This repo is the weights. The harness, `vibe.py`, and training code live in
[github.com/YauhenBichel/python-vibe](https://github.com/YauhenBichel/python-vibe).
Serve drafts through `PythonVibeGuard` (empty / leaked keys / `curl|sh`).

A longer train run overfit after this checkpoint. `adapters.safetensors` here
**is** step 100, not the last step.

## Download and use (Mac / MLX)

```bash
hf download YauhenBichel/python-vibe-0.5b --local-dir adapters/python-vibe
```

```python
from mlx_lm import load, generate

model, tokenizer = load(
    "mlx-community/Qwen2.5-Coder-0.5B-Instruct-4bit",
    adapter_path="adapters/python-vibe",
)
```

Or clone the GitHub repo and run the harnessed REPL (it pulls this repo if
`adapters/python-vibe` is missing):

```bash
git clone https://github.com/YauhenBichel/python-vibe.git
cd python-vibe
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python scripts/vibe.py
```

Linux / Windows without MLX: `ollama pull qwen2.5-coder:0.5b` and
`PYTHONPATH=src python scripts/serve.py` — that is the **base** coder plus the
harness, not these adapters.

Base weights: `Qwen/Qwen2.5-Coder-0.5B-Instruct` (Apache-2.0).

## Research notes (2026-08-29)

Write-up: [docs/research-vibe-review.md](https://github.com/YauhenBichel/python-vibe/blob/feat/initial-python-vibe/docs/research-vibe-review.md).

- ~45 train pairs. Val was best around **step 100**; this repo ships that checkpoint.
- Held-out vibe tasks (weekday, count `.md`, apply a docstring) **run through the harness** but the Python is often wrong. The adapter is a style prior, not a reliable pair.
- A real repo (OpenSRE) does not fit in context. Review is **one small `.py` file** (about 200–2500 bytes). `batch_review.py` loads the LoRA once and can walk **100** such files; `--fix` rewrites only when the review is not `no issues`, keeps a `.bak`, and refuses a tiny overwrite.
- Do not treat a 100-file `--fix` as a safe OpenSRE refactor. Read `scratch/batch-review.jsonl` first.

Issues: [45 pairs vs style prior](https://github.com/YauhenBichel/python-vibe/issues/9) · [guard evasion](https://github.com/YauhenBichel/python-vibe/issues/8).
