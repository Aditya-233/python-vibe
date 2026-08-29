---
name: write-tests
description: Adds or extends unittest files for a change. Use when adding a feature, changing behavior, or when the user asks for tests.
---

# Write tests

Use `unittest`. Put files in `tests/test_*.py`.

## Steps

1. Read existing tests so you match imports and style.
2. One test method per behavior. Assert a real return value, not only “no exception”.
3. New test file: `Action: edit` (parents are created). Existing file: `Action: patch` with a unique `Find:` of at least 8 characters.
4. Run `Argv: -m unittest discover -s tests -q`.
5. If there is no `tests/` directory yet, add `tests/test_<module>.py` first, then run.

Do not add pytest unless the project already uses it. Do not hit the network.
