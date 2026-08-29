# AGENTS.md

Guidance for humans and coding agents working in **python-vibe**.

This repo is a **0.5B LoRA + a deterministic harness**, not a Cursor/Grok
replacement. Treat the model as a style prior. Treat `PythonVibeGuard` as the
safety boundary.

## Commands

Harness tests need no GPU, no Ollama, and no Hugging Face token:

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python scripts/validate.py
```

`validate.py` is what CI runs: unit tests, `scripts/smoke.py`, then
`scripts/eval_everyday.py` (offline gate).

Live paths (optional):

```bash
PYTHONPATH=src python scripts/smoke.py --live
PYTHONPATH=src python scripts/smoke.py --mlx
```

## Non-negotiable

- The harness stays **deterministic**. Do not add a prompt-side router that
  skips `PythonVibeGuard`.
- Do not commit `.safetensors`, `.env`, tokens, hostnames, or adapter folders.
- Do not teach the model to discuss moles or lesions (PV004). That belongs to
  [MoleCare/skincare-qa](https://github.com/MoleCare/skincare-qa).
- Do not add `curl | sh` examples (PV003).
- `scripts/serve.py` binds **127.0.0.1**. Do not change the default to `0.0.0.0`.
- Tests must not write into `scratch/` (gitignored; missing on CI). Use
  `tempfile.TemporaryDirectory`.
- Docs and GitHub Pages must not contain personal paths (`/Users/…`, `DevBox/…`).

## Layout

| Path | Role |
| --- | --- |
| `src/harness/` | Guard, serve helpers, agent parse/tools, report formatter |
| `src/finetune/` | Specs, splits, Hub card, agent system prompt |
| `scripts/vibe.py` | Laptop REPL (`/run`, `--then`, `--project`) |
| `scripts/serve.py` | Local HTTP sidecar |
| `scripts/agent.py` | Cursor-like loop (use a **larger** Ollama model) |
| `scripts/batch_review.py` | One-file-at-a-time review of up to 100 files |
| `data/python-vibe/` | Short stdlib train/valid/test JSONL |
| `docs/` | GitHub Pages + investigations |
| `tests/` | Fast unit tests (the merge gate) |

## How to change things

**Harness rule.** Add a regex in `src/harness/python_vibe.py` and **two** tests:
one string that must `block`, one near-miss that must `pass`. Bump
`RULESET_VERSION` only if the public meaning of a verdict changes.

**Training pair.** Short stdlib Python, type hints, no secrets. One pair is a
style prior, not a capability unlock. See investigation
[45 pairs vs style prior](docs/investigations/style-prior.md).

**HTTP sidecar.** Keep stdlib `http.server`. Cap POST bodies (`MAX_BODY`). New
routes need a test in `tests/test_serve.py` that does not call Ollama.

**Agent loop.** `scripts/agent.py` defaults to `llama3.1:8b`. `--tiny` / mlx
0.5B is smoke only. Cursor wiring: [docs/cursor-local.md](./docs/cursor-local.md).
Train the 7B-class tool LoRA with `scripts/agent.py --record data/agent-loop/extra.jsonl`,
then `scripts/build_agent_data.py` and `scripts/train.py --everyday`. Name it in
Ollama with `scripts/export_ollama.py --create`. Do not spend more 0.5B train
steps expecting Grok quality.

**Investigations.** New measurement pages go in `docs/investigations/`. Add the
file to `tests/test_pages.py`. Do not claim the LoRA audited a real repo.

## What not to “fix”

- Do not put an LLM-as-judge on the serve path.
- Do not run `batch_review.py --fix` on someone else’s project from CI.
- Do not treat a hundred `no issues` on 200-byte files as a review.
- Do not fuse / push GGUF unless the discussion on public fused weights agrees.

## Security

Report privately — [SECURITY.md](./SECURITY.md). Email **info@molecare.co.uk**.
Never paste live keys into issues, tests, or Pages.
