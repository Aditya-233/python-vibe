#!/usr/bin/env python3
"""Everyday explore / edit / run for small repos; harness for large ones.

Everyday brain is llama3.1:8b (or qwen2.5-coder:7b / 14b). The 0.5B LoRA
is a sidecar — pass --tiny only for smoke.

  ollama pull llama3.1:8b
  PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/app \\
    "find a real NameError and fix it"

  # large repo: stay inside one tree
  PYTHONPATH=src python3.13 scripts/agent.py --project /path/to/app \\
    --scope src/harness "what does apply_source refuse?"

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
from harness.agent_parse import parse_turn_smart  # noqa: E402
from harness.agent_tools import (  # noqa: E402
    edit_py,
    glob_py,
    grep_py,
    map_py,
    patch_py,
    read_py,
    run_python,
)
from harness.engine import make_generate  # noqa: E402
from harness.project_brief import (  # noqa: E402
    classify_project,
    looks_like_question,
    render_brief,
    start_hint,
)
from harness.smart import locate_py, prelude, refuse_early_done  # noqa: E402
from harness.python_vibe import PythonVibeGuard  # noqa: E402
from harness.skills import (  # noqa: E402
    get_skill,
    list_skills,
    pick_skills,
    render_catalog,
    render_skill,
    skill_from_action,
)
from harness.trace_record import append_turn  # noqa: E402

_ACTIONS = "glob|grep|read|edit|patch|run|map|plan|skill|locate|done"


def _remember(generate_once, prompt: str, draft: str) -> None:
    history = getattr(generate_once, "history", None)
    if history is None:
        return
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": draft})


def _tool(project: Path, turn, last_path: str, scope: str) -> tuple[str, str]:
    path = turn.path or last_path
    used_scope = turn.scope or scope
    loaded = skill_from_action(turn.action, turn.name, turn.path, project)
    if loaded is not None:
        return render_skill(loaded), last_path
    if turn.action == "skill":
        return (
            f"skill needs Name: (add-feature, write-tests, stay-scoped). "
            f"{render_catalog(list_skills(project))}",
            last_path,
        )
    if turn.action == "locate":
        query = turn.query or turn.name
        return locate_py(project, query, used_scope)
    if turn.action == "map":
        return map_py(project, used_scope), last_path
    if turn.action == "plan":
        return (
            f"plan noted:\n{turn.summary or '(empty plan)'}\n"
            "Take the first explore action now.",
            last_path,
        )
    if turn.action == "glob":
        return glob_py(project, turn.pattern or "**/*.py", scope=used_scope), last_path
    if turn.action == "grep":
        return grep_py(project, turn.query, scope=used_scope), last_path
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
        return patch_py(project, path, turn.find, turn.replace, turn.append), path
    if turn.action == "run":
        return run_python(project, turn.argv), last_path
    if turn.action == "done":
        return turn.summary or "done", last_path
    return (
        f"unknown Action {turn.action}. Use {_ACTIONS}.",
        last_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", nargs="?", default="")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument(
        "--scope",
        default="",
        help="large-repo harness: only map/grep/glob under this subdirectory",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="print small/large brief and exit (no model)",
    )
    parser.add_argument(
        "--skill",
        action="append",
        default=[],
        metavar="NAME",
        help="preload a SKILL.md (repeatable). Kit: add-feature, write-tests, stay-scoped",
    )
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
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument(
        "--record",
        type=Path,
        help="append redacted turns (default: data/agent-loop/extra.jsonl if set)",
    )
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    if not project.is_dir():
        sys.exit(f"not a directory: {project}")
    try:
        brief = classify_project(project, args.scope)
    except ValueError as exc:
        sys.exit(str(exc))
    catalog = list_skills(project)
    if args.brief:
        print(render_brief(brief, scope=args.scope))
        print()
        print(render_catalog(catalog))
        return
    if not args.task:
        sys.exit("task required (or pass --brief)")
    if args.tiny:
        args.model = TINY_OLLAMA
        args.engine = "ollama"
    if is_tiny_model(args.model) or args.engine == "mlx":
        print(
            "warning: 0.5B sidecar — expect missed Action: lines. "
            f"Everyday default is {DEFAULT_EVERYDAY_OLLAMA}.",
            file=sys.stderr,
        )

    label, generate_once = make_generate(
        args.engine, args.max_tokens, model=args.model, system=AGENT_SYSTEM
    )
    print(
        f"engine {label}  project {project}  mode {brief.kind}",
        file=sys.stderr,
    )
    last_path = ""
    located_path = ""
    pre_text, located_path = prelude(project, args.task, args.scope)
    if pre_text:
        last_path = located_path
        print(pre_text[:2000], file=sys.stderr)
    preloaded = []
    for name in args.skill:
        loaded = get_skill(name, project)
        if loaded is None:
            sys.exit(f"unknown skill: {name}")
        preloaded.append(loaded)
    if not preloaded:
        preloaded = pick_skills(args.task, catalog)
        if brief.kind == "large":
            extra = get_skill("stay-scoped", project)
            if extra and extra.name not in {item.name for item in preloaded}:
                preloaded.append(extra)
    skill_block = ""
    if preloaded:
        skill_block = "\n\n".join(render_skill(item) for item in preloaded) + "\n\n"
    prompt = (
        f"{render_brief(brief, scope=args.scope)}\n\n"
        f"{render_catalog(catalog)}\n\n"
        f"{skill_block}"
        + (f"{pre_text}\n\n" if pre_text else "")
        + f"Project root: {project}\n"
        + (f"Scope: {args.scope}\n" if args.scope else "")
        + f"Task: {args.task}\n"
        + start_hint(brief, args.task)
    )
    for step in range(1, args.steps + 1):
        draft = generate_once(prompt)
        _remember(generate_once, prompt, draft)
        print(f"\n--- step {step} ---\n{draft}\n", flush=True)
        turn = parse_turn_smart(draft, question=looks_like_question(args.task))
        if args.record:
            append_turn(
                args.record.expanduser(),
                {"user": prompt, "assistant": draft, "action": (turn.action if turn else "")},
            )
        if turn is None:
            prompt = f"Could not parse. One Action: {_ACTIONS}"
            continue
        if turn.action == "done":
            blocked = refuse_early_done(args.task, last_path, located_path)
            if blocked:
                prompt = blocked
                print(blocked[:500], file=sys.stderr)
                continue
            print(turn.summary or "done")
            return
        try:
            result, last_path = _tool(project, turn, last_path, args.scope)
        except (ValueError, OSError) as exc:
            result = str(exc)
        print(result[:2000], file=sys.stderr)
        prompt = f"Tool result:\n{result}\n\nNext Action:"
    sys.exit(f"stopped after {args.steps} steps")


if __name__ == "__main__":
    main()
