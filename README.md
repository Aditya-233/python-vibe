# python-vibe

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)
[![CI](https://github.com/YauhenBichel/python-vibe/actions/workflows/ci.yml/badge.svg)](https://github.com/YauhenBichel/python-vibe/actions/workflows/ci.yml)

Everyday Python vibe coding on a laptop. Small repos: explore, edit, run.
Large repos: a scoped harness so the model never loads the whole tree.
The public 0.5B LoRA is a **style prior**. Daily work uses an **8B** Ollama
model plus the jail in `scripts/agent.py`.

Weights (public tiny): [YauhenBichel/python-vibe-0.5b](https://huggingface.co/YauhenBichel/python-vibe-0.5b).

| Track | What to run | Role |
| --- | --- | --- |
| Everyday (laptop) | `scripts/agent.py` (default `llama3.1:8b`) | Comfortable explore / edit / run; `--scope` on large trees |
| Local editor | [docs/local-editor.md](./docs/local-editor.md) | OpenAI-compatible Ollama on this machine |
| Tiny (Hub / smoke) | `scripts/vibe.py`, `serve.py`, `--tiny` | 0.5B drafts through `PythonVibeGuard` |

Join: [good first issue](https://github.com/YauhenBichel/python-vibe/labels/good%20first%20issue) ·
[Discussions](https://github.com/YauhenBichel/python-vibe/discussions). You do
not need a GPU to run tests.

Contributing: [CONTRIBUTING.md](./CONTRIBUTING.md) · security: [SECURITY.md](./SECURITY.md).
Vulnerabilities: open a **public** GitHub issue. Do not paste live keys.

## Everyday agent

`scripts/agent.py` defaults to `llama3.1:8b`. Pass `--tiny` only for smoke.

**Small** (≤40 first-party `.py`/`.md`, ≤200 KB): the agent gets a file list.
Questions → read → `Action: done`. Bugs → `Action: patch` → run.

**Large**: the agent gets top-level counts. Start with `Action: map`. Stay
inside `--scope`. Grep truncates; do not ask it to read the whole repo.

```bash
ollama pull llama3.1:8b
cd python-vibe

# see small vs large without calling a model
PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app --brief

# small repo — fix or ask
PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app \
  "find a real NameError and fix it"
PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app \
  "what does compute_total return?"

# large repo — stay in one folder
PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app \
  --scope src "what does apply_source refuse?"
```

Writes stay under `--project` and go through `PythonVibeGuard` + `.bak`.
One action per turn: `map` · `plan` · `skill` · `glob` · `grep` · `read` ·
`edit` · `patch` · `run` · `done`.

`map` returns a signature outline, not just sizes. A `Find:` that misses by
whitespace is retried and re-indented; one that misses outright comes back
with the closest real lines. A repeated read-only action is refused once.
Your project's own `AGENTS.md` is read first and outranks the kit skills.
Why each of those: [harness-comparison](./docs/investigations/harness-comparison.md).

Best-practice skills live in `skills/` (`add-feature`, `write-tests`,
`stay-scoped`, `new-package`, `fix-smell`, `read-issue`, `open-pr`,
`merge-pr`). The agent preloads them when the task says “add” / “test” /
“create a package” / “rename” / “issue” / “PR”, or you pass `--skill`.
`Action: skill` + `Name:` loads one mid-loop. Ship actions (`issue`,
`branch`, `commit`, `push`, `pr`, `merge`) are jailed: no force, not
`main`/`master`, no secret filenames.

```bash
PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app \
  --skill add-feature \
  "add a function multiply(a, b) and a unit test"
```

Point an OpenAI-compatible editor at the same 8B: [docs/local-editor.md](./docs/local-editor.md).

```bash
PYTHONPATH=src python3.13 scripts/eval_everyday.py
PYTHONPATH=src python3.13 scripts/eval_everyday.py --live
```

Do not call this everyday-ready until `--live` beats an untuned 8B on parse
rate and a real ≥1 KB fix. Notes:
[docs/investigations/everyday-laptop.md](./docs/investigations/everyday-laptop.md) ·
[docs/research-vibe-review.md](./docs/research-vibe-review.md).

## Tiny sidecar (0.5B)

Anyone can pull the adapters (no Hugging Face login) and start the harnessed REPL.
This track drafts **one small file**. It does not walk a repo.

```bash
git clone https://github.com/YauhenBichel/python-vibe.git
cd python-vibe
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
hf download YauhenBichel/python-vibe-0.5b --local-dir adapters/python-vibe
PYTHONPATH=src python3.13 scripts/vibe.py
```

`vibe.py` also downloads that Hub repo itself if `adapters/python-vibe` is empty.
Linux / Windows without MLX: `ollama pull qwen2.5-coder:0.5b` then
`PYTHONPATH=src python3.13 scripts/serve.py` (base coder + harness, not the LoRA).

```
client → harness :8080 → ollama qwen2.5-coder:0.5b
              ↓
     pass / revise / block
     block twice → fixed fallback
```

The harness blocks empty drafts, leaked keys, `curl|sh`, and lesion diagnosis
(wrong surface). It does not rewrite style.

### Interactive `/run`

Every draft goes through `PythonVibeGuard`. `/run` executes the last Python
block in `scratch/last.py`.

```
vibe> print the weekday for a YYYY-MM-DD date from argv
vibe> /run 2026-08-29
vibe> also accept --short for Mon
vibe> /run 2026-08-29 --short
```

```bash
PYTHONPATH=src python3.13 scripts/vibe.py --run --then \
  "print the weekday for argv YYYY-MM-DD" -- 2026-08-29
```

`--then` sends the traceback back once if `/run` fails. `--engine ollama`
uses the pulled `qwen2.5-coder:0.5b` base instead of the LoRA.

### One file in your project

```bash
PYTHONPATH=src python3.13 scripts/vibe.py --project /path/to/your/app
```

```
vibe> /open src/app.py
vibe> add a docstring to the main function and keep the rest
vibe> /apply
```

```bash
PYTHONPATH=src python3.13 scripts/vibe.py \
  --project /path/to/your/app \
  --file src/app.py \
  --apply \
  "add type hints to main(); do not change behaviour"
```

### Review up to 100 files (still one file per call)

`batch_review.py` loads the LoRA once and walks the smallest first-party `.py`
files (skips `.venv`). Review first. `--fix` rewrites only when the review is
not `no issues`, keeps a `.bak`, and refuses a tiny overwrite.

```bash
PYTHONPATH=src python3.13 scripts/batch_review.py \
  --project /path/to/your/app \
  --limit 100
```

Report: `scratch/batch-review.jsonl`. Read it before you keep any `--fix` write.

## Train (Mac / MLX 3.13)

Tiny style prior:

```bash
PYTHONPATH=src python3.13 scripts/build_data.py
PYTHONPATH=src python3.13 scripts/train.py
```

Everyday tool loop (7B-class, after you record traces):

```bash
PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app \
  --record data/agent-loop/extra.jsonl \
  "find a real NameError and fix it"
PYTHONPATH=src python3.13 scripts/build_agent_data.py
PYTHONPATH=src python3.13 scripts/train.py --everyday
```

`extra.jsonl` is gitignored. Do not commit live paths or keys.

## Test

Harness only (no GPU, no Ollama):

```bash
PYTHONPATH=src python3.13 -m unittest discover -s tests -q
PYTHONPATH=src python3.13 scripts/validate.py
```

Live Ollama (base 0.5B through `PythonVibeGuard`):

```bash
ollama pull qwen2.5-coder:0.5b
PYTHONPATH=src python3.13 scripts/smoke.py --live
```

LoRA on Mac (MLX, Python 3.13). `--best` uses
`adapters/python-vibe/0000100_adapters.safetensors` when that checkpoint is
present.

```bash
PYTHONPATH=src python3.13 scripts/smoke.py --mlx
```

## Serve (tiny sidecar)

```bash
ollama pull qwen2.5-coder:0.5b
PYTHONPATH=src python3.13 scripts/serve.py
```

```bash
curl -s localhost:8080/health
curl -s localhost:8080/v1/python-vibe \
  -H 'content-type: application/json' \
  -d '{"prompt":"jsonl reader that skips bad lines"}'
```

Binds **127.0.0.1**. Do not change the default to `0.0.0.0`.

## Hugging Face

Public adapters: [YauhenBichel/python-vibe-0.5b](https://huggingface.co/YauhenBichel/python-vibe-0.5b)
(`adapters.safetensors` is the step-100 checkpoint).

```bash
hf download YauhenBichel/python-vibe-0.5b --local-dir adapters/python-vibe
PYTHONPATH=src python3.13 scripts/pull_hf.py python-vibe
```

To publish a new train (needs `hf auth login` and write access to **your**
namespace — set `HF_USER` / `HF_REPO`, never implied as the official account):

```bash
PYTHONPATH=src python3.13 scripts/push_hf.py python-vibe --what adapters --public
```
