---
name: fix-smell
description: Renames one opaque function to readable snake_case. Use when the task is smell, rename, or clean up. Do not use for add or questions.
---

Action: patch
Path: pkg/mathy.py
Find: def calc(x, y):
Replace: def total_price(quantity: int, unit_price: int) -> int:
