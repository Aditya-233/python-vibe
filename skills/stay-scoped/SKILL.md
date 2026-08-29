---
name: stay-scoped
description: Stays in one folder on a large tree. Use when Mode is large, grep is truncated, or the user names a folder.
---

Copy this first:

Action: map
Scope: src

Then:

Action: locate
Query: the_symbol_from_the_task

Do not Action: done after `__init__.py`. Do not edit a second package.
