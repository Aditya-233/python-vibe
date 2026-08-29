---
name: readable-layout
description: Reports why a project is hard to read — import cycles, an ungrouped package, a god module, no tests — and names one move. Use when the task is structure, layout, layers, organise, or refactor. Do not use for adding one function.
---

Look before you move anything.

Action: layout
Scope: {{scope}}

It answers with findings worst-first and one next move. Do that one move.
Do not restructure a second folder in the same turn.

A readable package is one folder per job, each with an `__init__.py` whose
docstring says what the folder is for, and imports that only point at
folders below it. Two modules that import each other share something: put
that shared thing in a third module they both import.
