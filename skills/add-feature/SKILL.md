---
name: add-feature
description: Adds one requested function plus a test. Use when the task starts with add, implement, or introduce. Do not use for questions or one-line bugs.
---

Action: patch
Path: pkg/mathy.py
Append:
def multiply(left: int, right: int) -> int:
    return left * right
