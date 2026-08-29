# Use a local everyday model in an OpenAI-compatible editor

The 0.5B LoRA is a style prior, not a daily coding brain. Point your editor
at **Ollama 8B+** on this machine. The write jail in `scripts/agent.py` is a
separate CLI loop for comfortable explore / edit / run.

## 1. Pull the everyday brain

```bash
ollama pull llama3.1:8b
# or: ollama pull qwen2.5-coder:7b
# or: ollama pull qwen2.5-coder:14b
```

Optional name with the agent system prompt baked in:

```bash
PYTHONPATH=src python scripts/export_ollama.py --create
# → ollama run python-vibe-everyday
```

## 2. OpenAI-compatible endpoint

Ollama already exposes this:

`http://127.0.0.1:11434/v1/chat/completions`

A localhost proxy that defaults to the everyday model (and warns if you pick
0.5B):

```bash
PYTHONPATH=src python scripts/openai_compat.py
# http://127.0.0.1:8081/v1/chat/completions
```

## 3. Editor model override

In your editor’s OpenAI-compatible settings:

- Enable the OpenAI-compatible API
- Base URL: `http://127.0.0.1:8081/v1` (proxy) or
  `http://127.0.0.1:11434/v1` (Ollama direct)
- API key: `ollama` (any non-empty string; Ollama ignores it)
- Model: `llama3.1:8b` or `python-vibe-everyday`

The editor then uses **its** tools (read / edit / terminal). `scripts/agent.py`
is the same job with **our** jail if you stay in the terminal.

## 4. CLI agent (guarded writes)

```bash
PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app \
  "find a real NameError and fix it"
# large repo
PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app \
  --scope src "what does apply_source refuse?"
```

Small projects get a file list and can answer questions (`Action: done`)
without editing. Large projects start with `Action: map` and stay inside
`--scope`. That is the harness; the model does not load the whole tree.

`--tiny` / `--engine mlx` is smoke only.

Record redacted turns for a future 7B–14B LoRA:

```bash
PYTHONPATH=src python scripts/agent.py --project /path/to/your/app \
  --record data/agent-loop/extra.jsonl \
  "find a real NameError and fix it"
PYTHONPATH=src python scripts/build_agent_data.py
PYTHONPATH=src python scripts/train.py --everyday
```

`extra.jsonl` is gitignored. Do not commit live paths or keys.

## 5. Optional: your LoRA as GGUF / Ollama

Stand-in (this week): `export_ollama.py --create` is `FROM llama3.1:8b` plus the
agent system prompt. That is **not** a trained python-vibe-8b.

After you fuse a 7B-class MLX adapter to a folder:

1. Convert with [llama.cpp](https://github.com/ggml-org/llama.cpp) `convert_hf_to_gguf.py` (not in this repo).
2. `PYTHONPATH=src python scripts/export_ollama.py --from-gguf fused/everyday.gguf --create`

Do not call this everyday-ready until `scripts/eval_everyday.py --live` beats
untuned 8B on Action: parse rate.
