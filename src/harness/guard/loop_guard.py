"""Refuse a repeated explore action. Deterministic. No model.

A small model that does not know what to do next re-runs the last grep.
The loop then burns its whole `--steps` budget on identical tool results.
Only read-only actions are guarded: re-running tests after a patch is
progress, re-grepping the same query is not.
"""

from __future__ import annotations

from dataclasses import dataclass, field

EXPLORE = frozenset({"glob", "grep", "read", "map", "locate", "plan", "skill"})
_NEXT = {
    "grep": "Action: read Path: one file from those hits.",
    "glob": "Action: read Path: one file from that list.",
    "map": "Action: grep Query: a symbol from the task.",
    "locate": "Action: read Path: the file it named, or Action: done.",
    "read": "Action: done with the answer, or Action: patch with a fix.",
    "plan": "Take the first explore action now.",
    "skill": "Copy the Action: block from the skill.",
}


def turn_key(turn) -> tuple[str, ...]:
    return (
        turn.action,
        turn.path.strip(),
        turn.query.strip(),
        turn.pattern.strip(),
        turn.scope.strip(),
        turn.name.strip(),
    )


@dataclass
class LoopGuard:
    """Remembers explore keys already served in this run."""

    seen: set[tuple[str, ...]] = field(default_factory=set)

    def check(self, turn) -> str:
        if turn is None or turn.action not in EXPLORE:
            return ""
        key = turn_key(turn)
        if key in self.seen:
            hint = _NEXT.get(turn.action, "Take a different action.")
            detail = turn.path or turn.query or turn.pattern or turn.name
            return (
                f"already ran that exact {turn.action}"
                + (f" ({detail})" if detail else "")
                + f". The result has not changed. {hint}"
            )
        self.seen.add(key)
        return ""
