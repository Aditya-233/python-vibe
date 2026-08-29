---
name: write-tests
description: Adds one unittest method for a new function. Use when adding a feature or when the user asks for tests.
---

Action: patch
Path: tests/test_mathy.py
Find: from pkg.mathy import add
Replace: from pkg.mathy import add, multiply
Append:
    def test_multiply(self) -> None:
        self.assertEqual(multiply(2, 3), 6)
