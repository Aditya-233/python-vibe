---
name: add-feature
description: Adds a requested function or behavior and a test. Use when the user says add, implement, introduce, or new feature. Do not use for questions or one-line bugfixes.
---

# Add a feature

Add only what was asked. Do not invent extras.

## When to add

- The task names a function or behavior that is **not** in the repo.
- Words like add / implement / introduce / new feature.

## When not to add

- The task is a question (what / why / how) → read, then `Action: done`.
- The task is a one-line bug (`NameError`, typo) → `Action: patch` only.
- Large project with no `--scope` → `Action: map` first, then add inside one tree.

## Steps

1. `Action: grep` for the name. If it already exists, say so and stop.
2. Read the module you will change and its tests.
3. Follow [write-tests](../write-tests/SKILL.md): add or extend `tests/test_*.py`.
4. Implement the smallest change. To add a function at the end of a file:

       Action: patch
       Path: pkg/mathy.py
       Append:
       def multiply(a: int, b: int) -> int:
           return a * b

   For a one-line swap, `Find:` must be a **full unique line**, not a prefix
   like `def add(`. New file: `Action: edit`. Keep existing functions.
5. `Action: run` with `Argv: -m unittest discover -s tests -q`.
6. If tests or syntax fail, fix them. Do not `Action: done` on a red run.
7. `Action: done` with what you added and the test result.

Stdlib-style Python. No new dependencies. Path stays in the project.
