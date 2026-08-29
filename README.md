# python-vibe

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)
[![CI](https://github.com/YauhenBichel/python-vibe/actions/workflows/ci.yml/badge.svg)](https://github.com/YauhenBichel/python-vibe/actions/workflows/ci.yml)

LoRA on **Qwen2.5-Coder-0.5B** (~400 MB 4-bit) for short Python vibe-coding answers,
plus a tiny `PythonVibeGuard` sidecar.

Weights (public): [YauhenBichel/python-vibe-0.5b](https://huggingface.co/YauhenBichel/python-vibe-0.5b).
Skin-health Q&A is a separate repo: [MoleCare/skincare-qa](https://github.com/MoleCare/skincare-qa).

## Download and use

Anyone can pull the adapters (no Hugging Face login) and start the harnessed REPL.

```bash
git clone https://github.com/YauhenBichel/python-vibe.git
cd python-vibe
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
hf download YauhenBichel/python-vibe-0.5b --local-dir adapters/python-vibe
PYTHONPATH=src python scripts/vibe.py
```

`vibe.py` also downloads that Hub repo itself if `adapters/python-vibe` is empty.
Linux / Windows without MLX: `ollama pull qwen2.5-coder:0.5b` then
`PYTHONPATH=src python scripts/serve.py` (base coder + harness, not the LoRA).

Contributing: [CONTRIBUTING.md](./CONTRIBUTING.md) · security: [SECURITY.md](./SECURITY.md).
Vulnerabilities go to **info@molecare.co.uk**, not a public issue.

Issues: [good first issue](https://github.com/YauhenBichel/python-vibe/labels/good%20first%20issue) ·
Discussions: [research and ideas](https://github.com/YauhenBichel/python-vibe/discussions)

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
git clone https://github.com/YauhenBichel/python-vibe.git
cd python-vibe
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python scripts/build_data.py
PYTHONPATH=src python scripts/train.py
```

## Vibe on this laptop

Interactive session on the step-100 LoRA (MLX) or Ollama if MLX is missing. Every draft goes through `PythonVibeGuard`. `/run` executes the last Python block in `scratch/last.py`.

```bash
cd python-vibe
PYTHONPATH=src python scripts/vibe.py
```

```
vibe> print the weekday for a YYYY-MM-DD date from argv
vibe> /run 2026-08-29
vibe> also accept --short for Mon
vibe> /run 2026-08-29 --short
```

One-shot (generate + execute). `--then` sends the traceback back once if `/run` fails — that is the usual 0.5B loop:

```bash
PYTHONPATH=src python scripts/vibe.py --run --then \
  "print the weekday for argv YYYY-MM-DD" -- 2026-08-29
```

`--engine ollama` uses the pulled `qwen2.5-coder:0.5b` base instead of the LoRA.

### Review and edit a file in your project

The 0.5B model can only hold **one small `.py` file**. It rewrites that file; it does not walk the repo.

```bash
cd ~/DevBox/python-vibe
source .venv/bin/activate
PYTHONPATH=src python scripts/vibe.py --project /path/to/your/app
```

```
vibe> /open src/app.py
vibe> add a docstring to the main function and keep the rest
vibe> /apply
```

One shot (writes the file, keeps `src/app.py.bak`):

```bash
PYTHONPATH=src python scripts/vibe.py \
  --project /path/to/your/app \
  --file src/app.py \
  --apply \
  "add type hints to main(); do not change behaviour"
```

### Review or fix up to 100 files

The model still sees **one file per call**. `batch_review.py` loads the LoRA once and walks the smallest first-party `.py` files (skips `.venv`). Review first. `--fix` rewrites only when the review is not `no issues`, keeps a `.bak`, and refuses a tiny overwrite.

```bash
cd ~/DevBox/molecare/python-vibe
PYTHONPATH=src python scripts/batch_review.py \
  --project /Users/yauhenbichel/DevBox/tracer-cloud/opensre \
  --limit 100
```

```bash
PYTHONPATH=src python scripts/batch_review.py \
  --project /Users/yauhenbichel/DevBox/tracer-cloud/opensre \
  --limit 100 --fix
```

Report: `scratch/batch-review.jsonl`. A 100-file `--fix` on OpenSRE will invent edits. Read the report before you keep any write.

Research write-up (what we measured, what we shipped):
[docs/research-vibe-review.md](./docs/research-vibe-review.md). Same notes live on the
Hub card: [YauhenBichel/python-vibe-0.5b](https://huggingface.co/YauhenBichel/python-vibe-0.5b).

## Test

Harness only (no GPU, no Ollama):

```bash
PYTHONPATH=src python -m unittest discover -s tests -q
PYTHONPATH=src python scripts/smoke.py
```

Live Ollama (base 0.5B through `PythonVibeGuard`):

```bash
ollama pull qwen2.5-coder:0.5b
PYTHONPATH=src python scripts/smoke.py --live
PYTHONPATH=src python scripts/chat.py "jsonl reader that skips bad lines"
```

LoRA on Mac (MLX, Python 3.13). Uses `adapters/python-vibe/0000100_adapters.safetensors` when you pass `--best` — that checkpoint had the better val loss.

```bash
PYTHONPATH=src python scripts/generate_mlx.py "jsonl reader that skips bad lines" --best
PYTHONPATH=src python scripts/smoke.py --mlx
```

## Serve

```bash
ollama pull qwen2.5-coder:0.5b
PYTHONPATH=src python scripts/serve.py
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

Public adapters: [YauhenBichel/python-vibe-0.5b](https://huggingface.co/YauhenBichel/python-vibe-0.5b)
(`adapters.safetensors` is the step-100 checkpoint).

```bash
hf download YauhenBichel/python-vibe-0.5b --local-dir adapters/python-vibe
PYTHONPATH=src python scripts/pull_hf.py python-vibe
```

To publish a new train (needs `hf auth login` and write access):

```bash
PYTHONPATH=src python scripts/push_hf.py python-vibe --what adapters --public
```
