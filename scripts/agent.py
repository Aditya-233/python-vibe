#!/usr/bin/env python3
"""Cursor-like loop: glob / grep / read / edit / run / done.

Everyday brain is llama3.1:8b (or qwen2.5-coder:7b / 14b). The 0.5B LoRA
is a sidecar — pass --tiny only for smoke.

  ollama pull llama3.1:8b
  PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/app \\
    "find a real NameError and fix it"

Writes stay under --project and go through PythonVibeGuard + .bak.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finetune.agent_system import AGENT_SYSTEM  # noqa: E402
from finetune.everyday import DEFAULT_EVERYDAY_OLLAMA, TINY_OLLAMA, is_tiny_model  # noqa: E402
from harness.agent_parse import parse_turn  # noqa: E402
from harness.agent_tools import (  # noqa: E402
    edit_py,
    glob_py,
    grep_py,
    patch_py,
    read_py,
    run_python,
)
from harness.engine import make_generate  # noqa: E402
from harness.python_vibe import PythonVibeGuard  # noqa: E402
from harness.trace_record import append_turn  # noqa: E402


def _remember(generate_once, prompt: str, draft: str) -> None:
    history = getattr(generate_once, "history", None)
    if history is None:
        return
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": draft})


def _tool(project: Path, turn, last_path: str) -> tuple[str, str]:
    path = turn.path or last_path
    if turn.action == "glob":
        return glob_py(project, turn.pattern or "**/*.py"), last_path
    if turn.action == "grep":
        return grep_py(project, turn.query), last_path
    if turn.action == "read":
        if not path:
            return "read needs Path:", last_path
        return read_py(project, path), path
    if turn.action == "edit":
        if not path:
            return "edit needs Path:", last_path
        if not turn.source:
            return "edit needs a ```python block", path
        blocked = PythonVibeGuard().check(turn.source)
        if blocked.verdict != "pass":
            return f"harness blocked: {[f.rule_id for f in blocked.findings]}", path
        return edit_py(project, path, turn.source), path
    if turn.action == "patch":
        if not path:
            return "patch needs Path: (or read that file first)", last_path
        return patch_py(project, path, turn.find, turn.replace), path
    if turn.action == "run":
        return run_python(project, turn.argv), last_path
    if turn.action == "done":
        return turn.summary or "done", last_path
    return (
        f"unknown Action {turn.action}. Use glob, grep, read, edit, patch, run, done.",
        last_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--engine", default="ollama")
    parser.add_argument(
        "--tiny",
        action="store_true",
        help="use qwen2.5-coder:0.5b (smoke only; poor tool calls)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_EVERYDAY_OLLAMA,
        help="Ollama model. Default is the everyday 8B, not the 0.5B LoRA.",
    )
    parser.add_argument("--max-tokens", type=int, default=700)
    parser.add_argument("--steps", type=int, default=16)
    parser.add_argument(
        "--record",
        type=Path,
        help="append redacted turns (default: data/agent-loop/extra.jsonl if set)",
    )
    args = parser.parse_args()
    if args.tiny:
        args.model = TINY_OLLAMA
        args.engine = "ollama"
    if is_tiny_model(args.model) or args.engine == "mlx":
        print(
            "warning: 0.5B sidecar — expect missed Action: lines. "
            f"Everyday default is {DEFAULT_EVERYDAY_OLLAMA}.",
            file=sys.stderr,
        )
    project = args.project.expanduser().resolve()
    if not project.is_dir():
        sys.exit(f"not a directory: {project}")

    label, generate_once = make_generate(
        args.engine, args.max_tokens, model=args.model, system=AGENT_SYSTEM
    )
    print(f"engine {label}  project {project}", file=sys.stderr)
    last_path = ""
    prompt = (
        f"Project root: {project}\n"
        f"Task: {args.task}\n"
        "Start with Action: grep or Action: read. Do not Action: done yet."
    )
    for step in range(1, args.steps + 1):
        draft = generate_once(prompt)
        _remember(generate_once, prompt, draft)
        print(f"\n--- step {step} ---\n{draft}\n", flush=True)
        turn = parse_turn(draft)
        if args.record:
            append_turn(
                args.record.expanduser(),
                {"user": prompt, "assistant": draft, "action": (turn.action if turn else "")},
            )
        if turn is None:
            prompt = (
                "Could not parse. One Action: glob|grep|read|edit|patch|run|done"
            )
            continue
        if turn.action == "done":
            print(turn.summary or "done")
            return
        try:
            result, last_path = _tool(project, turn, last_path)
        except (ValueError, OSError) as exc:
            result = str(exc)
        print(result[:2000], file=sys.stderr)
        prompt = f"Tool result:\n{result}\n\nNext Action:"
    sys.exit(f"stopped after {args.steps} steps")


if __name__ == "__main__":
    main()
