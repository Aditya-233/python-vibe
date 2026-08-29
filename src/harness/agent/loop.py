"""Run one task from start to finish.

    from harness import Agent, AgentOptions

    result = Agent(AgentOptions(project=Path("~/app"))).run("fix the NameError")

This class is responsible for the order of steps and nothing else. It asks
`harness.agent.prompt` what to send to the model, `harness.agent.policy`
whether a proposed action is allowed, and `harness.agent.dispatch` to carry
an allowed action out.
"""

from __future__ import annotations

from dataclasses import dataclass

from harness.act.parse import parse_turn_smart
from harness.agent.dispatch import ACTIONS, run_action
from harness.agent.options import AgentOptions, AgentResult, Step
from harness.agent.policy import LoopState, next_prompt, refuse_before, refuse_done
from harness.agent.prompt import Preamble, build_preamble
from harness.model.engine import make_generate
from harness.observe.trace_record import append_turn
from harness.scan.design import render_design_review
from harness.task import (
    looks_like_design_loop,
    looks_like_question,
    looks_like_ship,
    looks_unclear,
)


@dataclass(frozen=True)
class Question:
    """A question the agent needs answered before it can continue.

    Fields:
        text: the question.
        options: answers the agent considers likely. May be empty.
    """

    text: str
    options: tuple[str, ...] = ()

    def render(self) -> str:
        if not self.options:
            return self.text
        listed = "\n".join(f"  {i}. {opt}" for i, opt in enumerate(self.options, 1))
        return f"{self.text}\n{listed}"


def _question_from(turn) -> Question:
    text = (turn.query or turn.summary or "").strip() or "What should I do?"
    raw = turn.append or turn.replace or ""
    options = tuple(
        line.strip(" -*\t")
        for line in raw.splitlines()
        if line.strip(" -*\t")
    )
    return Question(text, options[:4])


class Agent:
    """Runs one task against one project."""

    def __init__(self, options: AgentOptions) -> None:
        self.options = options
        self.project = options.resolved_project()

    def preamble(self, task: str | None = None) -> Preamble:
        options = self.options if task is None else _with_task(self.options, task)
        return build_preamble(options)

    def run(self, task: str | None = None) -> AgentResult:
        options = self.options if task is None else _with_task(self.options, task)
        if not options.task.strip():
            raise ValueError("task required")
        pre = build_preamble(options)
        options.emit("preamble", pre.pre_text or "")

        # A task that names no file and no symbol cannot be started from.
        # The harness asks, rather than relying on the model to notice: a
        # small model reaches for `patch` long before it reaches for `ask`.
        opening = opening_question(options.task, pre)
        if opening is not None:
            answer = self._ask(opening, options)
            if answer is None:
                return AgentResult(
                    ok=False,
                    summary=opening.render(),
                    stopped="question",
                )
            options = _with_task(options, f"{options.task} ({answer})")
            pre = build_preamble(options)
            options.emit("preamble", f"user answered: {answer}")
        label, generate = make_generate(
            options.engine,
            options.max_tokens,
            model=options.model,
            system=pre.system or options.system,
        )
        options.emit("engine", f"{label}  project {self.project}  mode {pre.brief.kind}")
        state = LoopState(
            task=options.task,
            project=self.project,
            located_path=pre.located_path,
            located_signature=pre.located_signature,
            prelude_ran=bool(pre.pre_text),
            allow_writes=options.allow_writes,
            last_path=pre.located_path,
            instructions=_instruction_lines(pre),
            scope=options.scope,
            design_report=(
                render_design_review(self.project, options.scope)
                if looks_like_design_loop(options.task)
                else ""
            ),
        )
        prompt = pre.prompt
        steps: list[Step] = []
        writes: list[str] = []

        for number in range(1, options.steps + 1):
            draft = generate(prompt)
            _remember(generate, prompt, draft)
            options.emit("draft", f"--- step {number} ---\n{draft}")
            turn = parse_turn_smart(
                draft,
                question=looks_like_question(options.task),
                ship=looks_like_ship(options.task),
            )
            if options.record:
                append_turn(
                    options.record.expanduser(),
                    {
                        "user": prompt,
                        "assistant": draft,
                        "action": turn.action if turn else "",
                    },
                )
            if turn is None:
                steps.append(Step(number, "", refused="unparsed", draft=draft))
                prompt = f"Could not parse. One Action: {ACTIONS}"
                continue

            if turn.action == "done":
                blocked = refuse_done(state, turn)
                if blocked:
                    steps.append(Step(number, "done", refused=blocked, draft=draft))
                    options.emit("refused", blocked)
                    prompt = blocked
                    continue
                steps.append(Step(number, "done", result=turn.summary, draft=draft))
                return AgentResult(
                    ok=True,
                    summary=turn.summary or "done",
                    stopped="done",
                    steps=tuple(steps),
                    writes=tuple(writes),
                )

            # Policy first, ask included: the cap on repeated questions
            # lives there, so it has to run before the question is put.
            blocked = refuse_before(state, turn)
            if blocked:
                steps.append(
                    Step(number, turn.action, turn.path, refused=blocked, draft=draft)
                )
                options.emit("refused", blocked)
                prompt = blocked
                continue

            if turn.action == "ask":
                question = _question_from(turn)
                state.questions_asked += 1
                answer = self._ask(question, options)
                if answer is None:
                    steps.append(
                        Step(number, "ask", result=question.render(), draft=draft)
                    )
                    return AgentResult(
                        ok=False,
                        summary=question.render(),
                        stopped="question",
                        steps=tuple(steps),
                        writes=tuple(writes),
                    )
                steps.append(Step(number, "ask", result=answer, draft=draft))
                prompt = f"The user answered: {answer}\n\nNext Action:"
                continue

            try:
                result, state.last_path = run_action(
                    self.project,
                    turn,
                    state.last_path,
                    options.scope,
                    pre.target,
                    task=options.task,
                )
            except (ValueError, OSError) as exc:
                result = str(exc)
            options.emit("result", result)
            if turn.action == "run" and result.startswith("exit 0"):
                state.ran_tests = True
            if result.startswith(("patched", "wrote")):
                writes.append(turn.path or state.last_path)
                state.wrote_something = True
            steps.append(
                Step(number, turn.action, state.last_path, result=result, draft=draft)
            )
            nudge = next_prompt(state, turn, result, pre.target)
            prompt = (
                f"Tool result:\n{result}\n\n{nudge}"
                if nudge
                else f"Tool result:\n{result}\n\nNext Action:"
            )

        return AgentResult(
            ok=False,
            summary=f"stopped after {options.steps} steps",
            stopped="steps",
            steps=tuple(steps),
            writes=tuple(writes),
        )

    def _ask(self, question: Question, options: AgentOptions) -> str | None:
        """None means nobody is there to answer — the caller decides."""
        handler = getattr(options, "on_question", None)
        if handler is None:
            return None
        return handler(question)


def opening_question(task: str, pre) -> Question | None:
    """Return a question to put before the run starts, or None to proceed.

    Only returned when the task names nothing the agent can search for and
    the harness did not find a file on its own.
    """
    if pre.located_path or not looks_unclear(task):
        return None
    options = tuple(
        item for item in (pre.target.module, pre.target.test) if item
    )
    return Question(
        f'"{task.strip()}" does not name a file or a function. '
        "Which file should I work on?",
        options,
    )


def _instruction_lines(pre) -> tuple[str, ...]:
    """The skill lines the model was handed, so an echo can be spotted."""
    lines: list[str] = []
    for skill in pre.skills:
        lines.extend(
            line.strip()
            for line in skill.body.splitlines()
            if len(line.strip()) >= 12 and not line.strip().startswith("Action:")
        )
    return tuple(lines)


def _with_task(options: AgentOptions, task: str) -> AgentOptions:
    from dataclasses import replace

    return replace(options, task=task)


def _remember(generate, prompt: str, draft: str) -> None:
    history = getattr(generate, "history", None)
    if history is None:
        return
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": draft})
