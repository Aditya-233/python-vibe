---
name: write-tests
description: Adds one unittest method for a new function. Use when adding a feature or when the user asks for tests.
---

Append: only. The harness inserts the method inside the class and adds the
name to the existing import. Do not write a Find:.

Action: patch
Path: {{test}}
Append:
    def test_multiply(self) -> None:
        self.assertEqual(multiply(2, 3), 6)
