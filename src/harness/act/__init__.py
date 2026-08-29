"""Read a proposed action and carry it out on the file system.

Parses one action from the model's reply and provides the operations it can
request: search, read, patch, replace and run. All file writes pass through
the path restriction and backup in `harness.act.code`.
"""
