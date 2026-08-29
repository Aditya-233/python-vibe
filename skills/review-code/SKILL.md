---
name: review-code
description: Reports defects in one file without changing it. Use when the task is review, check, or find bugs. Do not use when the task asks for a fix.
---

Read the file, then report. Reviews do not edit.

Action: read
Path: {{module}}

Then, for each problem, one line naming the symbol and what goes wrong:

Action: done
Summary: compute_total returns 0 for an empty list, so callers cannot tell
an empty input from a zero total.

Quote the code. Do not repeat this instruction back as the answer. If the
file has no defect, say so.
