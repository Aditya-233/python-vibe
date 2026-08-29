"""Decide whether a proposed action is allowed, and what to do next.

The loop consults three functions, in this order:

* `refuse_before` runs before an action is carried out. It returns the
  reason the action is not allowed, or an empty string if it is allowed.
* `refuse_done` runs when the model reports that the task is finished. It
  returns the reason the work is not finished, or an empty string.
* `next_prompt` runs after an action has been carried out. It returns the
  single next instruction to send, or an empty string to leave the choice
  to the model.

Keeping these separate from the loop means a new rule is a new function
rather than another branch inside the loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from harness.act.tools import read_py
from harness.agent.dispatch import SHIP_ACTIONS, WRITE_ACTIONS
from harness.guard.loop_guard import LoopGuard
from harness.locate import (
    refuse_early_done,
    refuse_question_write,
    refuse_redundant_explore,
    refuse_redundant_locate,
    refuse_shallow_done,
)
from harness.skillkit.catalog import get_skill, render_skill
from harness.skillkit.style import refuse_package_done, refuse_smell_wrong_file
from harness.task import (
    looks_like_add_feature,
    looks_like_fix_smell,
    looks_like_merge,
    looks_like_new_package,
    looks_like_question,
    looks_like_ship,
    question_symbol,
    rename_target,
    smell_symbol,
)

MAX_QUESTIONS = 2
# A Summary this close to a line it was given is an echo, not an answer.
ECHO_RATIO = 0.75


@dataclass
class LoopState:
    """Facts the loop has gathered, used to judge the next action.

    Fields:
        task: the user's request.
        project: directory being worked in.
        located_path: file the harness found before the model started.
        located_signature: the definition line found in that file.
        prelude_ran: whether the harness searched before the model started.
        allow_writes: whether file changes are permitted in this run.
        last_path: file the most recent action applied to.
        ran_tests: whether the test suite has passed during this run.
        questions_asked: how many questions the agent has put to the user.
        instructions: skill lines the model was given, used to detect a
            reply that repeats an instruction instead of answering.
        guard: record of read-only actions already performed.
    """

    task: str
    project: Path
    located_path: str = ""
    located_signature: str = ""
    prelude_ran: bool = False
    allow_writes: bool = True
    last_path: str = ""
    ran_tests: bool = False
    questions_asked: int = 0
    instructions: tuple[str, ...] = ()
    guard: LoopGuard = field(default_factory=LoopGuard)


def refuse_before(state: LoopState, turn) -> str:
    """The turn is about to run a tool. Return a refusal, or ""."""
    if not state.allow_writes and turn.action in WRITE_ACTIONS:
        return (
            "This run is read-only. Do not patch, edit, or run. "
            "Action: done Summary: say what you would change and why."
        )
    if turn.action == "ask" and state.questions_asked >= MAX_QUESTIONS:
        return (
            "You have already asked. Choose the most likely reading, say "
            "which you chose, and continue."
        )
    blocked = refuse_question_write(state.task, turn.action)
    if not blocked:
        blocked = refuse_redundant_explore(
            state.task, turn.action, turn.path, state.located_path
        )
    if not blocked:
        blocked = refuse_redundant_locate(state.task, turn.action, state.prelude_ran)
    if not blocked:
        blocked = refuse_smell_wrong_file(
            state.task,
            turn.action,
            turn.path,
            state.located_path,
            _located_body(state),
        )
    if not blocked:
        blocked = state.guard.check(turn)
    if not blocked and turn.action in SHIP_ACTIONS:
        blocked = _refuse_ship(state.task, turn.action)
    return blocked


def _located_body(state: LoopState) -> str:
    if not state.located_path:
        return ""
    try:
        return read_py(state.project, state.located_path)
    except (OSError, ValueError):
        return ""


def _refuse_ship(task: str, action: str) -> str:
    if not looks_like_ship(task):
        return (
            "Ship actions only when the task is about an issue, PR, commit, "
            "or push."
        )
    if action == "merge" and not looks_like_merge(task):
        return "merge only when the task says merge"
    return ""


def refuse_echoed_summary(summary: str, instructions: tuple[str, ...]) -> str:
    """Reject a closing summary that repeats an instruction the model was given.

    A small model will sometimes copy a line out of its skill and present it
    as the answer. For example, given the instruction "quote the -> type
    from the def line (example: tuple[str, int])", it replies with that
    exact sentence. A check that only looks for the return type finds "int"
    inside the example and accepts it, so the text is compared against the
    instructions as well.
    """
    said = _squash(summary)
    if len(said) < 12:
        return ""
    for line in instructions:
        want = _squash(line)
        if len(want) < 12:
            continue
        if said in want or want in said:
            return (
                "That repeats an instruction you were given, it does not "
                "answer. Action: done Summary: say it in your own words and "
                "quote the code you read."
            )
        overlap = len(set(said.split()) & set(want.split()))
        if overlap and overlap / max(1, len(set(said.split()))) >= ECHO_RATIO:
            return (
                "That repeats an instruction you were given, it does not "
                "answer. Action: done Summary: quote the code you read."
            )
    return ""


def _squash(text: str) -> str:
    return " ".join(text.lower().split())


def refuse_done(state: LoopState, turn) -> str:
    """The model says it is finished. Return a refusal, or ""."""
    blocked = refuse_echoed_summary(turn.summary, state.instructions)
    if not blocked:
        blocked = refuse_early_done(state.task, state.last_path, state.located_path)
    if not blocked:
        blocked = refuse_shallow_done(
            state.task, turn.summary, state.located_signature
        )
    if not blocked:
        blocked = refuse_package_done(state.task, state.ran_tests)
    return blocked


def next_prompt(state: LoopState, turn, result: str, target=None) -> str:
    """A tool just ran. Name the one right next step, or "" to stay open."""
    path = (turn.path or state.last_path).lower()
    wrote = result.startswith(("patched", "wrote"))
    if not wrote:
        return ""
    is_test = "test" in path
    if looks_like_add_feature(state.task) and turn.action == "patch" and not is_test:
        loaded = get_skill("write-tests", state.project)
        if loaded is not None:
            return (
                f"{render_skill(loaded, target, state.project)}\n"
                "Next Action must be this write-tests patch. "
                "Do not Append after if __name__.\n"
            )
    if looks_like_new_package(state.task) and turn.action in {"edit", "patch"}:
        noun = question_symbol(state.task) or "service"
        if "__init__" in path:
            return (
                f"Next Action must be edit Path: pkg/{noun}.py with one "
                f"function def {noun}(...). snake_case. Not in __init__.py.\n"
            )
        if not is_test:
            return (
                f"Next Action must be edit Path: tests/test_{noun}.py as a "
                f"unittest.TestCase that imports {noun}. Then Action: run.\n"
            )
        return "Next Action must be run Argv: -m unittest discover -s tests -q\n"
    if looks_like_fix_smell(state.task) and turn.action == "patch" and not is_test:
        old, new = smell_symbol(state.task), rename_target(state.task)
        if old and new:
            return (
                f"Next Action: patch tests to replace {old} with {new}, "
                "then Action: run.\n"
            )
    return ""


def unclear(task: str) -> bool:
    """A task with no verb and no symbol cannot be started from."""
    text = task.strip()
    if looks_like_question(text):
        return False
    return len(text.split()) < 3 and not question_symbol(text)
