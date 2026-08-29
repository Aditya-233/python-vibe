---
name: refactor-split
description: Splits one god module into pkg/<concern>.py. Use when the task is refactor or extract. Do not rewrite the whole tree.
---

Action: edit
Path: pkg/pricing.py
```python
def total_price(quantity: int, unit_price: int) -> int:
    return quantity * unit_price
```
