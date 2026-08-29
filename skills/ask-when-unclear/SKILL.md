---
name: ask-when-unclear
description: Asks the user one short question when the task could mean two different things. Use when the task names no file and no symbol, or when two files would both be reasonable places to change. Do not use when the harness has already found the file.
---

Ask once, then continue. Do not ask twice about the same thing.

Action: ask
Query: which file should this change go in?
Append:
- {{module}}
- {{test}}

Give at most four options and make each one a real choice. If you can tell
which reading is right, do not ask; say which one you chose and continue.
