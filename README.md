# python-vibe

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)
[![CI](https://github.com/YauhenBichel/python-vibe/actions/workflows/ci.yml/badge.svg)](https://github.com/YauhenBichel/python-vibe/actions/workflows/ci.yml)

LoRA on **Qwen2.5-Coder-0.5B** (~400 MB 4-bit) for short Python vibe-coding answers,
plus a tiny `PythonVibeGuard` sidecar.

Weights: [YauhenBichel/python-vibe-0.5b](https://huggingface.co/YauhenBichel/python-vibe-0.5b).
Skin-health Q&A is a separate repo: [MoleCare/skincare-qa](https://github.com/MoleCare/skincare-qa).

```
client → harness :8080 → ollama qwen2.5-coder:0.5b
              ↓
     pass / revise / block
     block twice → fixed fallback
```

The harness blocks empty drafts, leaked keys, `curl|sh`, and lesion diagnosis
(wrong surface). It does not rewrite style.

## Train (Mac / MLX 3.13)

```bash
cd ~/DevBox/molecare/python-vibe
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python scripts/build_data.py
PYTHONPATH=src python scripts/train.py
```

## Serve

```bash
ollama pull qwen2.5-coder:0.5b
PYTHONPATH=src python scripts/serve.py
PYTHONPATH=src python -m unittest discover -s tests -q
```

```bash
curl -s localhost:8080/health
curl -s localhost:8080/v1/python-vibe \
  -H 'content-type: application/json' \
  -d '{"prompt":"jsonl reader that skips bad lines"}'
```

```bash
PYTHONPATH=src python scripts/chat.py "write a jsonl reader"
```

## Hugging Face

```bash
hf auth login
PYTHONPATH=src python scripts/init_hf_repos.py
PYTHONPATH=src python scripts/fuse_and_export.py python-vibe --hf
```
