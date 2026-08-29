# Architecture

`src/harness/` is ordered bottom-up. **A module may import a layer strictly
below it, never one above or beside it.** That rule is enforced by
`tests/test_architecture.py`, so a refactor that rots fails the merge gate
rather than the next reader.

```
observe/   what a run leaves behind      trace_record, report_md, eval_gate
locate.py  find the symbol before acting
act/       intent becomes a change       parse, tools, patch_fix, code
skillkit/  the skill kit                 catalog, target, style
scan/      facts about a tree            project_scan, project_brief,
                                         repo_map, project_docs, layout
guard/     what ships, what is refused   python_vibe, run, types,
                                         fallbacks, loop_guard
task.py    what the user asked for       (leaf)
paths.py   where this repo is on disk    (leaf)
model/     talking to weights            engine, ollama_generate,
ship/      git and PR helpers            openai_compat / git_ship  (leaves)
```

Read a layer top-down and you learn what the harness does. Read it
bottom-up and you learn what it refuses.

## Why `task.py` is the bottom

Every layer needs to know whether the user asked a question or asked for a
change. Before, whichever module needed a predicate first owned it, so
`project_brief`, `skills`, and `style` imported each other in a circle,
broken only by function-local imports that hid the cycle from every reader.

Pulling the predicates into one leaf removed all three cycles. One rule
holds the set together: **a question is never a write** — every
`looks_like_*` writer predicate returns `False` for a question.

## Why `guard/` cannot import `act/`

`guard/` is the safety boundary. If it could import a layer that writes
files, a refusal could be routed around by whatever it imported. The rule
is a test (`test_the_guard_layer_cannot_write`), not a convention.

## Why nothing counts `parents[N]`

A module that resolves the repo root by counting parent directories breaks
silently the moment it moves into a layer. `harness/paths.py` resolves it
once; `test_no_module_counts_its_own_depth` keeps it that way.

## The same check, pointed at your project

`Action: layout` runs `harness/scan/layout.py` against the tree in front of
the agent and reports the same four things, worst first, then names **one**
move:

| Finding | What it means |
| --- | --- |
| `cycle` | two modules import each other; neither can be read alone |
| `flat` | one package holding many modules with no grouping |
| `god` | one module far larger than its neighbours |
| `no-tests` | code with no `test_*.py` anywhere |

```bash
PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/your/app \
  --skill readable-layout "why is this project hard to follow?"
```

One move per turn is deliberate. Handed four findings an 8B rewrites the
tree; handed one it does the one.
