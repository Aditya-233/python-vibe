---
title: Everyday Python on a laptop
description: A local explore / edit / run loop for small Python trees, plus a scoped harness for large ones. Public 0.5B LoRA is a style prior. Daily work is an 8B model plus scripts/agent.py.
date: 2026-08-29
---

# Everyday Python on a laptop

Small repos: explore, edit, run. Large repos stay inside `--scope`. The public 0.5B LoRA is a style prior. Daily work is an 8B local model plus the jail in `scripts/agent.py`.

<p class="cta">
  <a href="{{ '/start/' | relative_url }}">Install and run</a>
  <a href="https://github.com/YauhenBichel/python-vibe" rel="noreferrer">Source on GitHub</a>
</p>

```bash
ollama pull llama3.1:8b
PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app \
  "what does compute_total return?"
```

<div class="stats">
  <div class="stat"><b>8B</b><span>Everyday default (Ollama)</span></div>
  <div class="stat"><b>0.5B</b><span>Public Hub sidecar</span></div>
  <div class="stat"><b>2 / 3</b><span>8B live Action parse (29 Aug 2026)</span></div>
  <div class="stat"><b>0 / 4</b><span>0.5B held-out vibe tasks</span></div>
</div>

<div class="tracks">
  <section class="track">
    <h2>Everyday</h2>
    <p><code>scripts/agent.py</code> with <code>llama3.1:8b</code>. Typed Actions, a write jail, skills, and a locate prelude. Comfortable on trees of ≤40 first-party <code>.py</code>/<code>.md</code> files and ≤200 KB.</p>
    <p><a href="{{ '/start/' | relative_url }}">Full install</a></p>
  </section>
  <section class="track">
    <h2>Tiny sidecar</h2>
    <p>Hub adapters <a href="https://huggingface.co/YauhenBichel/python-vibe-0.5b" rel="noreferrer">YauhenBichel/python-vibe-0.5b</a>. One small draft through <code>PythonVibeGuard</code>. Smoke, CI, and demos — not a daily coding brain.</p>
    <p><a href="{{ '/research-vibe-review/' | relative_url }}">0.5B measurements</a></p>
  </section>
</div>

## When this is the right tool

Use python-vibe for a cheap **offline** loop on a small Python tree, writes jailed, no cloud API. Keep 0.5B for Hub demos. Pull a 7B or 14B coder if 8B answers stay shallow.

Use a hosted IDE agent when the job is multi-file across languages, needs extra tools or a browser, or you must quote more than one call site. Pointing a local editor at Ollama changes the brain, not the tools.

[Local loop vs hosted agents]({{ '/investigations/local-vs-cloud/' | relative_url }}) · [What to improve]({{ '/investigations/what-to-improve/' | relative_url }})

## Honest limits

- No general shell. `Action: run` is Python argv only.
- Writes are `.py` / `.pyi` / `.md` under `--project`, with `.bak`, a 2/3-length guard, and `ast.parse`.
- Large trees need `--scope` and `Action: map`. An 8B will not walk a hundred files.
- The 7B everyday LoRA (`python-vibe-8b`) is a config. It is not trained.
- Live parse on this kit (29 Aug 2026) is **2 / 3**. That is not everyday-ready.

## Research

- [Local loop vs hosted agents]({{ '/investigations/local-vs-cloud/' | relative_url }}) — every shipped path, same jobs
- [What to improve]({{ '/investigations/what-to-improve/' | relative_url }}) — harness work that closes a gap, and work that does not
- [Everyday laptop]({{ '/investigations/everyday-laptop/' | relative_url }}) — why 0.5B is not daily work
- [Everyday skills]({{ '/investigations/everyday-skills/' | relative_url }}) — skills written for an 8B
- [Harness comparison]({{ '/investigations/harness-comparison/' | relative_url }}) — what transfers from other agent harnesses
- [Architecture]({{ '/architecture/' | relative_url }}) — layer rule
