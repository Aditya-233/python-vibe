"""Layer: intent becomes a change. Deterministic, no model.

Parses one `Action:` turn and runs it against the tree: glob, grep, read,
patch, edit, run. Every write goes through the jail in `act.code`.
Depends on `harness.scan`.
"""
