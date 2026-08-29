---
title: Start
description: Install python-vibe. Everyday path is Ollama llama3.1:8b and scripts/agent.py. Tests run with no GPU.
permalink: /start/
date: 2026-08-29
---

# Start

Everyday explore / edit / run needs Ollama and an 8B coder. Harness tests need neither a GPU nor a model.

## You need

<ul class="need">
  <li>Python 3.13</li>
  <li><a href="https://ollama.com" rel="noreferrer">Ollama</a> and about 5 GB disk for <code>llama3.1:8b</code></li>
  <li>A small Python tree to point <code>--project</code> at</li>
</ul>

## Everyday agent

```bash
ollama pull llama3.1:8b
git clone https://github.com/YauhenBichel/python-vibe.git
cd python-vibe
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app --brief
PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app \
  "what does compute_total return?"
PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app \
  --scope src "find a real NameError and fix it"
```

`--tiny` is the 0.5B sidecar. Do not use it for daily work.

Same 8B in an OpenAI-compatible editor: [local editor]({{ '/local-editor/' | relative_url }}).

## Tests (no model)

```bash
PYTHONPATH=src python3.13 -m unittest discover -s tests -q
PYTHONPATH=src python3.13 scripts/validate.py
```

Do not call the project everyday-ready until `scripts/eval_everyday.py --live` beats an untuned 8B on Action parse rate and a real ≥1 KB fix.

## Tiny sidecar (not daily work)

```bash
hf download YauhenBichel/python-vibe-0.5b --local-dir adapters/python-vibe
PYTHONPATH=src python3.13 scripts/vibe.py
```

Linux without MLX: `ollama pull qwen2.5-coder:0.5b` then `scripts/serve.py`. That path is the base coder plus the harness, not the LoRA.
