---
title: Start
description: Install python-vibe on macOS, Linux or Windows. Everyday path is Ollama llama3.1:8b and the python-vibe command. Tests run with no GPU.
permalink: /start/
date: 2026-08-29
---

# Start

Everyday explore / edit / run needs Ollama and an 8B coder. Harness tests need neither a GPU nor a model.

## You need

<ul class="need">
  <li>Python 3.11 or newer, on macOS, Linux or Windows</li>
  <li><a href="https://ollama.com" rel="noreferrer">Ollama</a> and about 5 GB disk for <code>llama3.1:8b</code></li>
  <li>A small Python tree to point <code>--project</code> at</li>
</ul>

## Everyday agent

The harness uses only the standard library, so the install builds nothing
and is the same on every platform.

```bash
ollama pull llama3.1:8b
git clone https://github.com/YauhenBichel/python-vibe.git
cd python-vibe
pip install -e .
```

```bash
python-vibe brief  /path/to/your/app
python-vibe ask    /path/to/your/app "what does compute_total return?"
python-vibe run    /path/to/your/app --scope src "find a real NameError and fix it"
```

`python -m harness ...` does the same thing without the installed command.
`scripts/agent.py` still works from a source checkout, with `PYTHONPATH=src`
on macOS and Linux.

Training on Apple Silicon needs MLX, which does not install on Linux or
Windows, so it is a separate extra: `pip install -e ".[train]"`.

`--tiny` is the 0.5B sidecar. Do not use it for daily work.

The agent loads kit [skills]({{ '/skills/' | relative_url }}) from the wording
of the task (`add-feature`, `write-tests`, `answer-question`, and the rest),
or you pass `--skill`. `--brief` prints the pick with no model.

Same 8B in an OpenAI-compatible editor: [local editor]({{ '/local-editor/' | relative_url }}).

## Tests (no model)

After `pip install -e .`, on any platform:

```bash
python -m unittest discover -s tests -q
python scripts/validate.py
```

`validate.py` is what CI runs: the unit tests, the smoke check, then the
offline everyday gate. CI runs it on macOS, Linux and Windows across
Python 3.11 to 3.13.

Do not call the project everyday-ready until `scripts/eval_everyday.py --live` beats an untuned 8B on Action parse rate and a real ≥1 KB fix.

## Tiny sidecar (not daily work)

```bash
hf download YauhenBichel/python-vibe-0.5b --local-dir adapters/python-vibe
PYTHONPATH=src python3.13 scripts/vibe.py
```

Linux without MLX: `ollama pull qwen2.5-coder:0.5b` then `scripts/serve.py`. That path is the base coder plus the harness, not the LoRA.
