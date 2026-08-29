"""Seed explore→edit→run traces. Templates, not 2k Cursor sessions."""

from __future__ import annotations

from finetune.agent_system import AGENT_SYSTEM


def seed_pairs() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    files = (
        "src/app.py",
        "tools/system/work_items/validation.py",
        "lib/stats.py",
        "pkg/util_stats.py",
    )
    for path in files:
        pairs.append(
            (
                f"Project root: /tmp/app\nTask: find where {path.split('/')[-1]} defines main helpers\n"
                "Start with Action: grep or Action: read. Do not Action: done yet.",
                f"Action: grep\nQuery: def ",
            )
        )
        pairs.append(
            (
                f"Tool result:\n{path}:12:def compute_total(rows):\n\nNext Action:",
                f"Action: read\nPath: {path}",
            )
        )
        pairs.append(
            (
                f"Tool result:\n{path} (1200 chars)\ndef compute_total(rows):\n    return tota\n\nNext Action:",
                f"Action: edit\nPath: {path}\n```python\ndef compute_total(rows):\n    return sum(rows)\n```",
            )
        )
        pairs.append(
            (
                "Tool result:\nwrote "
                + path
                + " (backup "
                + path.split("/")[-1]
                + ".bak)\n\nNext Action:",
                "Action: run\nArgv: -m unittest discover -s tests -q",
            )
        )
        pairs.append(
            (
                "Tool result:\nexit 0\n.\n----------------------------------------------------------------------\nRan 1 test in 0.01s\n\nOK\n\nNext Action:",
                "Action: done\nSummary: Fixed NameError in compute_total (tota → sum(rows)) and tests passed.",
            )
        )

    pairs.append(
        (
            "Could not parse. Reply with one Action: glob|grep|read|edit|run|done",
            "Action: grep\nQuery: NameError",
        )
    )
    pairs.append(("Tool result:\n(no hits)\n\nNext Action:", "Action: glob\nPattern: **/*.py"))
    pairs.append(
        (
            "Tool result:\npkg/util_stats.py\ntests/test_util_stats.py\n\nNext Action:",
            "Action: read\nPath: tests/test_util_stats.py",
        )
    )
    pairs.append(
        (
            "Project root: /tmp/app\nTask: do not rewrite the whole repo after seeing __init__.py\n"
            "Start with Action: grep or Action: read. Do not Action: done yet.",
            "Action: grep\nQuery: TODO|FIXME|NameError",
        )
    )
    for query in ("class ", "import json", "def test_", "except Exception", "Path("):
        pairs.append((f"Find uses of {query.strip()}", f"Action: grep\nQuery: {query.strip()}"))
    pairs.append(
        (
            "Tool result:\nsrc/app.py:1:from pathlib import Path\n\nNext Action:",
            "Action: read\nPath: src/app.py",
        )
    )
    pairs.append(
        (
            "Task: run the unit tests after the edit. Do not Action: done yet.",
            "Action: run\nArgv: -m unittest discover -s tests -q",
        )
    )
    pairs.append(
        (
            "Tool result:\nexit 1\nNameError: name 'tota' is not defined\n\nNext Action:",
            "Action: grep\nQuery: tota",
        )
    )
    pairs.append(
        (
            "Tool result:\npkg/util_stats.py:71:return tota\n\nNext Action:",
            "Action: patch\nPath: pkg/util_stats.py\nFind: return tota\nReplace: return sum(cleaned)",
        )
    )
    return pairs


def all_pairs() -> list[tuple[str, str]]:
    return seed_pairs()


def system_prompt() -> str:
    return AGENT_SYSTEM
