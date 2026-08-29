---
title: Local editor
description: Add python-vibe to VS Code and other OpenAI-compatible editors in one command. Tasks and a local MCP stay on this machine. Chat override of localhost is optional.
date: 2026-08-29
---

# Use python-vibe from an editor

Three easy paths. All stay on `127.0.0.1` unless you choose otherwise.

| Path | One command | What you get |
| --- | --- | --- |
| Editor tasks | `python-vibe editors vscode --project ~/app` | Command Palette → Run Task → ask / run / brief. Uses the **jail**. |
| Continue (VS Code) | `python-vibe editors continue --project ~/app` | Chat uses local Ollama 8B. Uses the **editor’s** tools. |
| Local MCP | `python-vibe editors cursor --project ~/app` | The editor starts `python -m harness mcp` as a child process. Uses the **jail**. No tunnel. |
| Zed | `python-vibe editors zed --project ~/app` | Merges a `context_servers` entry into `.zed/settings.json`. Same jail. |

`pip install -e .` first so `python-vibe` is on your PATH. Files land in `.vscode/`, `.continue/`, or `.cursor/` inside **your** app, not inside this repo.

Drop-in sources: [`editors/`](https://github.com/YauhenBichel/python-vibe/tree/HEAD/editors).

## 1. Pull the everyday brain

```bash
ollama pull llama3.1:8b
# or: ollama pull qwen2.5-coder:7b
# or: ollama pull qwen2.5-coder:14b
```

## 2. Easiest: tasks in the integrated terminal

```bash
python-vibe editors vscode --project /path/to/your/app
```

Then Run Task and type a task, for example:

- `what does compute_total return?`
- `write a weekday script from argv`
- `fetch json from the HTTP API`
- `tally counts by key from a csv`
- `implement binary search`

The same `tasks.json` works in VS Code and in other editors that read `.vscode/tasks.json`.

## 3. OpenAI-compatible chat (brain only)

Ollama already exposes:

`http://127.0.0.1:11434/v1/chat/completions`

A localhost proxy that defaults to the everyday model (and warns if you pick 0.5B):

```bash
PYTHONPATH=src python scripts/openai_compat.py
# http://127.0.0.1:8081/v1/chat/completions
```

Or let the **jail** answer chat (writes off unless `--allow-writes`):

```bash
python-vibe serve --project /path/to/your/app
# GET  http://127.0.0.1:8090/v1/models
# POST http://127.0.0.1:8090/v1/chat/completions
```

In the editor’s OpenAI-compatible settings:

- Base URL: `http://127.0.0.1:8081/v1` (proxy) or `http://127.0.0.1:8090/v1` (harness)
- API key: `ollama` (any non-empty string)
- Model: `llama3.1:8b`

Some hosted editors send the OpenAI request from a **remote** backend. Those cannot see `127.0.0.1`. Do not open a public tunnel to the jail. Use tasks or the local MCP instead.

## 4. Local MCP (jail, no tunnel)

```bash
python-vibe editors cursor --project /path/to/your/app
```

The editor launches `python3 -m harness mcp --project <abs path>`. Tools: `ask` (read-only) and `run` (needs `--allow-writes` on that command). Stdout is JSON-RPC only.

This is the editor calling python-vibe. It is **not** an Action the 8B may emit.

## 5. CLI (same jail, no editor)

```bash
python-vibe run /path/to/your/app "find a real NameError and fix it"
python-vibe run /path/to/your/app --scope src "what does apply_source refuse?"
```

`--tiny` / `--engine mlx` is smoke only.

## What python-vibe is good at

Kit skills for everyday laptop Python (stdlib, AAA tests):

| You say | Skill |
| --- | --- |
| write a weekday script / argparse / argv | `write-script` |
| fetch json / HTTP API / “like curl” | `call-http` (urllib only; never `curl\|sh`) |
| tally / group by / csv / analytics | `analyze-data` |
| binary search / stack / algorithm | `write-algorithm` |

Each write is followed by `write-tests` (`test_<unit>_<result>`, Act into `got`).

## Optional: your LoRA as GGUF / Ollama

Stand-in (this week): `export_ollama.py --create` is `FROM llama3.1:8b` plus the
agent system prompt. That is **not** a trained python-vibe-8b.

After you fuse a 7B-class MLX adapter to a folder:

1. Convert with [llama.cpp](https://github.com/ggml-org/llama.cpp) `convert_hf_to_gguf.py` (not in this repo).
2. `PYTHONPATH=src python scripts/export_ollama.py --from-gguf fused/everyday.gguf --create`

Do not call this everyday-ready until `scripts/eval_everyday.py --live` beats
untuned 8B on Action: parse rate.
