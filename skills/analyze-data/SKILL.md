---
name: analyze-data
description: Adds one tally or group-by over rows (csv or list of dicts). Use for analytics, counters, histograms. Stdlib only.
---

One function. Readable names. collections.Counter. No pandas unless the project already has it.

Action: edit
Path: pkg/tally.py
from collections import Counter


def counts_by_key(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key, "")) for row in rows))
