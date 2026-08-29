---
title: What to improve
description: Harness work that can close a gap with a hosted agent, and work that cannot. Do not train more 0.5B for agency.
permalink: /investigations/what-to-improve/
date: 2026-08-29
type: article
---

# What to improve

The product gap is not closable. The harness gap is.

A hosted IDE agent has native tools, extra servers, a browser, and a large context window. python-vibe is a local loop: twenty typed Actions, a write jail, twenty steps, 700 tokens, `.py`/`.md` only. Improving this project means making the **8B loop reliable on small Python trees** — not growing a browser Action or pretending 8B is a frontier model.

Related: [local loop vs hosted agents]({{ '/investigations/local-vs-cloud/' | relative_url }}) · [harness comparison]({{ '/investigations/harness-comparison/' | relative_url }}).

<nav class="toc" aria-label="On this page">
<p>On this page</p>
<ol>
  <li><a href="#what-to-copy-what-to-refuse">What to copy, what to refuse</a></li>
  <li><a href="#closest-score-on-the-same-jobs">Closest score on the same jobs</a></li>
  <li><a href="#work-already-in-the-tree">Work already in the tree</a></li>
  <li><a href="#what-not-to-spend-a-week-on">What not to spend a week on</a></li>
  <li><a href="#two-success-bars">Two success bars</a></li>
</ol>
</nav>

## What to copy, what to refuse

Published harness notes in this repo already said the quiet part: **edit format and context assembly** move small-model pass rates. A free shell tool does not transfer to an 8B on a laptop working tree.

| Hosted-agent behavior | Copy into python-vibe? | Local lever | Status (29 Aug 2026) |
| --- | --- | --- | --- |
| Read the defining file before answering | Yes | `prelude()` locate + refuse a shallow `done` (must quote the `->` type) | Wired. `listen_addr` finishes in one step after the hint fix. Still omits env + argv. |
| Patch one function, then add a test, then run | Yes, scoped — not a stranger’s full suite | `pick_skills` + write-tests inject + refuse `done` before a passing run | Wired for add-feature and new-package. Not for every bugfix or refactor. |
| Review structure, then one split, then review again | Yes | Design scan + refuse `done` while findings remain | Predicate and scan exist. Review-only still blocks edits. The loop is not wired. |
| Show a repo map of signatures | Yes | `Action: map` (120-line outline) | Wired. Large trees still need `--scope`. |
| Recover a near-miss edit | Yes | `Find:` whitespace retry + closest-line hint | Wired. Keep exact `Find:` (fails loud). Do not add fuzzy patches. |
| Extra tools, browser, any language, 100k–1M context | No | None. Jail and step budget stay. | Out of scope on purpose. `openai_compat.py` does not add these. |
| Free-form terminal | No | Typed `run` only (no `-c`, pip, pipes) | Correct for an 8B on a laptop tree. |
| Train the brain to emit the protocol | Later, after traces | `train.py --everyday` on ~2k redacted `--record` turns | 30 train rows + 40 seed templates. No `python-vibe-8b` adapters. |

## Closest score on the same jobs

Score is “would a daily user get the same outcome,” not model size. 0–5. “After harness” is the recommended local work, not a new weight.

| Job | 8B + harness today | After recommended harness | Hosted IDE agent |
| --- | --- | --- | --- |
| Typed question | 4 | 4 | 5 |
| Add a function + test | 3 | 4 | 5 |
| Rename / smell | 3 | 4 | 5 |
| One-split refactor | 1 | 3 | 5 |
| 100-file review | 1 | 2 | 5 |
| Extra tools / browser / any language | 0 | 0 | 5 |

## Work already in the tree

Ship these before training another model.

1. **Design loop.** After each one-split edit, re-run the deterministic design scan. Refuse `Action: done` while findings remain. Allow edits on review tasks (today a review-only task blocks `patch` / `edit` / `run`).
2. **Auto-pick** `review-design`, `refactor-split`, and `readable-layout`. Wire the thin-review refuse in the `done` handler.
3. **Verify writes.** On add / bug / rename: after a successful impl patch, inject tests or `run`. Refuse `done` until a passing unittest on those task kinds. New-package already does this.
4. **Deeper small-file reads.** On small projects, raise the 3500-character read cap or include nearby constants so a question quotes env and argv, not “a tuple.”
5. **Measure bigger local models.** Same three probes on `qwen2.5-coder:7b` (pull) and any 30B coder already on disk. Do not change the default until 8B is still the best laptop tradeoff.
6. **Raise the live parse floor.** `eval/action_prompts.jsonl` has three rows. Live parse is 2/3. Everyday-ready means beating an untuned 8B on parse **and** a real ≥1 KB fix.
7. **Traces, then a 7B LoRA.** Only after the loop is stable. `--record` into `data/agent-loop/extra.jsonl` (gitignored). Thirty seed rows are not enough.

## What not to spend a week on

- More 0.5B train steps. The adapter is a style prior. Held-out vibe tasks failed. It misses `Action:` lines.
- Training `python-vibe-8b` on the thirty seed rows and calling it everyday-ready.
- A bash tool, a browser Action, or extra-tool bridges. Those make the laptop jail weaker and do not move the measured jobs.
- Raising `--steps` as a substitute for a review → one-split → review loop.

## Two success bars

| Bar | python-vibe (local) | Hosted IDE agent |
| --- | --- | --- |
| Ready for daily use | Small Python tree. First Action correct on Q&A / add / rename / one-split. Writes jailed. Offline. | Any repo, any language, extra tools, browser. Precise multi-site quotes. You pay a usage pool. |
| How you know | `skill_probe.py` shows the intended Action with prelude on; live eval beats the 8B baseline; a design loop reaches “no structure findings” without rewriting the tree. | Already there. Pointing an editor at Ollama does not move this bar. |
