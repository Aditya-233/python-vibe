# Investigation: can python-vibe be everyday Cursor Grok?

**Answer:** no — not this 0.5B LoRA. Everyday Grok-like use needs a larger
model, tool-use training, and Cursor wiring. Keep python-vibe-0.5b as a
cheap draft + harness.

Related: [research-vibe-review](../research-vibe-review.md) · issues
[#8](https://github.com/YauhenBichel/python-vibe/issues/8),
[#9](https://github.com/YauhenBichel/python-vibe/issues/9).

## What “every day as Grok” means

In Cursor you open a repo and talk. The model explores, edits many files,
runs tests, uses MCP, and keeps a plan. That is the product. The weights
are large and trained to emit tool calls.

python-vibe today is a **400 MB style prior** plus scripts:

| Surface | What it does |
| --- | --- |
| `vibe.py` | One prompt → one small Python draft → `/run` |
| `batch_review.py` | One small file at a time, up to 100 |
| `agent.py` | Text protocol: glob / grep / read / edit / run / done |

The 0.5B model misses `Action:` lines. `agent.py` only feels Grok-like when
`--model` is something like `llama3.1:8b`.

## Measured gap

Held-out laptop tasks (LoRA + harness): weekday name, count `.md`, jsonl
reader, tiny docstring apply — **all failed** (wrong `main()`, month-as-
weekday, filtered the word `"bad"`, junk docstring). Base
`qwen2.5-coder:0.5b` failed the same class.

OpenSRE: 100 smallest first-party files (200–2500 bytes) → **100× “no
issues”**, 0 applied. That is not a review.

## What will not work

- More steps on the 0.5B run (already overfit after step 100).
- More short stdlib pairs only (issue #9: this is a style prior).
- Asking the 0.5B weights to plan a repo.

## What to do

1. **This week.** `scripts/agent.py` defaults to `llama3.1:8b`. Cursor:
   [cursor-local.md](../cursor-local.md). `scripts/openai_compat.py` proxies
   `/v1/chat/completions`. `scripts/export_ollama.py --create` names
   `python-vibe-everyday`.
2. **Your model.** `scripts/build_agent_data.py` writes seed tool traces
   (`data/agent-loop`). `scripts/train.py --everyday` is the 7B-class LoRA.
   Append redacted Cursor sessions before claiming 2k traces. Fuse/GGUF:
   `export_ollama.py --from-gguf`.
3. **Eval.** `scripts/eval_everyday.py` (offline in CI). `--live` must beat
   untuned 8B on parse rate before anyone says daily Grok.

0.5B stays public for download, CI, and the harness demo. It is not the
everyday brain.

## Shipped in this repo (laptop path)

- `scripts/agent.py` defaults to `llama3.1:8b`. `--tiny` is the sidecar.
- `scripts/openai_compat.py` + [cursor-local.md](../cursor-local.md) for Cursor.
- Seed tool traces + `--record` → `data/agent-loop/extra.jsonl` (gitignored).
- `scripts/train.py --everyday` (7B-class MLX). `export_ollama.py --create`
  names the stand-in; GGUF of *your* LoRA is `--from-gguf`.
- `scripts/eval_everyday.py`: gold weekday + count-md `/run`, ≥1 KB NameError
  fixture, Action: parse fixtures. `--live` on this machine (29 Aug 2026):
  `llama3.1:8b` parsed **2 / 3** prompts (above the 50% floor). That is not
  Grok. Do not ship “daily Grok” until live beats a clean 8B baseline on a
  real ≥1 KB fix *and* parse rate.

Live `agent.py` + `llama3.1:8b` loops on this machine (29 Aug 2026):

1. NameError fixture copy: read → `Find: return tota` → tests OK → done (4 steps).
2. This repo: patched `scripts/agent.py` docstring to `python3.13`.
3. Failed: full-file `edit` wiped `tests/test_agent_tools.py` (20% length
   guard was too weak). Guard is now 2/3 of original; file restored by hand.
4. This repo: patched `resolve_project_file` to allow `.md`.
5. This repo: patched README agent example to `python3.13`.

We still do not call this Grok. The loop works on **scoped patch tasks**.
