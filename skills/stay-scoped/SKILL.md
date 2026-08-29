---
name: stay-scoped
description: Keeps work inside one subdirectory on a large tree. Use when the brief is Mode large, or the user names a folder, or grep hits are truncated.
---

# Stay scoped

Large trees are a harness problem, not a “read everything” problem.

1. `Action: map` (optional `Scope:`).
2. Pick one folder. Prefer `--scope` on the next run, or `Scope:` on map/grep/glob.
3. Tight `Query:` on grep. If you see `# … truncated`, narrow the query.
4. Do not `Action: done` after one tiny `__init__.py`.
5. Do not add a feature in a second package “while you are here”.
