---
name: new-package
description: Scaffolds pkg/ + tests/ with exports-only __init__. Use when the task is create a package or project structure. Do not use for one function on an existing module.
---

Action: edit
Path: pkg/__init__.py
```python
"""Public exports only. Implementation lives in sibling modules."""
```
