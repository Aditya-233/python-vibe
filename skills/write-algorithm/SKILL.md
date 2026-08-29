---
name: write-algorithm
description: Adds one named algorithm (binary search, stack, tally of edges) plus a later AAA test. Use for data structures and algorithms.
---

One function. Readable names. Return a useful value. Do not write the test in this Action.

Action: edit
Path: pkg/index_of.py
def index_of(sorted_items: list[int], target: int) -> int:
    low, high = 0, len(sorted_items) - 1
    while low <= high:
        mid = (low + high) // 2
        if sorted_items[mid] == target:
            return mid
        if sorted_items[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
