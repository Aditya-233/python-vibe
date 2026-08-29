---
name: fix-smell
description: Renames one opaque function to readable snake_case. Use when the task is smell, rename, or clean up. Do not use for add or questions.
---

Action: patch
Path: pkg/mathy.py
Find: def calc(
Replace: def multiply(

Keep the rest of the def line. Do not rewrite the parameter list.
