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
from harness.act.parse import parse_turn_smart  # noqa: E402
from harness.act.tools import (  # noqa: E402
    edit_py,
    glob_py,
    grep_py,
    map_py,
    patch_py,
    read_py,
    run_python,
)
from harness.model.engine import make_generate  # noqa: E402
from harness.guard.loop_guard import LoopGuard  # noqa: E402
from harness.scan.layout import render_layout  # noqa: E402
from harness.scan.project_brief import resolve_scope  # noqa: E402
from harness.scan.project_docs import render_house_rules  # noqa: E402
from harness.task import looks_like_question, question_symbol
from harness.scan.project_brief import (  # noqa: E402
    classify_project,
    render_brief,
    start_hint,
)
from harness.locate import (  # noqa: E402
    locate_py,
    prelude,
    refuse_early_done,
    refuse_question_write,
    refuse_redundant_explore,
    refuse_redundant_locate,
    refuse_shallow_done,
    signature_line,
)
from harness.guard.python_vibe import PythonVibeGuard  # noqa: E402
from harness.skillkit.target import pick_target  # noqa: E402
from harness.task import looks_like_add_feature
from harness.skillkit.catalog import (  # noqa: E402
    get_skill,
    list_skills,
    pick_skills,
    render_catalog,
    render_skill,
    skill_from_action,
)
from harness.task import (  # noqa: E402
    looks_like_fix_smell,
    looks_like_new_package,
    rename_target,
    smell_symbol,
)
from harness.skillkit.style import (  # noqa: E402
    refuse_layout,
    refuse_opaque_names,
    refuse_package_done,
    refuse_smell_wrong_file,
    wrap_bare_unittest,
)
from harness.observe.trace_record import append_turn  # noqa: E402
from harness.ship.git_ship import (  # noqa: E402
    commit_changes,
    create_pr,
    make_branch,
    merge_pr,
    push_branch,
    read_issue,
)
from harness.task import issue_number, looks_like_merge, looks_like_ship  # noqa: E402

_ACTIONS = (
    "glob|grep|read|edit|patch|run|map|plan|skill|locate|layout|done|"
    "issue|branch|commit|push|pr|merge"
)


def _remember(generate_once, prompt: str, draft: str) -> None:
    history = getattr(generate_once, "history", None)
    if history is None:
        return
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": draft})


def _tool(
    project: Path, turn, last_path: str, scope: str, target=None
) -> tuple[str, str]:
    path = turn.path or last_path
    used_scope = turn.scope or scope
    loaded = skill_from_action(turn.action, turn.name, turn.path, project)
    if loaded is not None:
        return render_skill(loaded, target, project), last_path
    if turn.action == "skill":
        return (
            f"skill needs Name: (add-feature, write-tests, stay-scoped, "
            f"new-package, fix-smell). "
            f"{render_catalog(list_skills(project))}",
            last_path,
        )
    if turn.action == "locate":
        query = turn.query or turn.name
        return locate_py(project, query, used_scope)
    if turn.action == "map":
        return map_py(project, used_scope), last_path
    if turn.action == "layout":
        base = resolve_scope(project, used_scope) if used_scope else project
        return render_layout(base), last_path
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
        named = refuse_opaque_names(turn.source)
        if named:
            return named, path
        try:
            original = read_py(project, path)
        except (OSError, ValueError):
            original = ""
        layout = refuse_layout(path, original, turn.source)
        if layout:
            return layout, path
        source = turn.source
        if "test" in path.replace("\\", "/").lower():
            stem = Path(path).stem.removeprefix("test_")
            source = wrap_bare_unittest(source, stem)
        return edit_py(project, path, source), path
    if turn.action == "patch":
        if not path:
            return "patch needs Path: (or read that file first)", last_path
        draft = "\n".join(part for part in (turn.replace, turn.append) if part)
        named = refuse_opaque_names(draft)
        if named:
            return named, path
        try:
            original = read_py(project, path)
        except (OSError, ValueError):
            original = ""
        layout = refuse_layout(path, original, draft)
        if layout:
            return layout, path
        return patch_py(project, path, turn.find, turn.replace, turn.append), path
    if turn.action == "run":
        return run_python(project, turn.argv), last_path
    if turn.action == "issue":
        number = turn.number or turn.query or turn.name
        return read_issue(project, number), last_path
    if turn.action == "branch":
        return make_branch(project, turn.name or turn.path or turn.query), last_path
    if turn.action == "commit":
        return commit_changes(project, turn.summary or turn.title), last_path
    if turn.action == "push":
        return push_branch(project), last_path
    if turn.action == "pr":
        return create_pr(
            project, turn.title or turn.summary, turn.body
        ), last_path
    if turn.action == "merge":
        return merge_pr(
            project,
            turn.number or turn.query or turn.name,
            allowed=True,
        ), last_path
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
        help="preload a SKILL.md (repeatable). Kit: add-feature, write-tests, stay-scoped, new-package, fix-smell",
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
    located_sig = signature_line(pre_text, question_symbol(args.task)) if pre_text else ""
    if pre_text:
        last_path = located_path
        print(pre_text[:2000], file=sys.stderr)
    ticket = issue_number(args.task)
    if ticket:
        issue_text = read_issue(project, ticket)
        block = f"Harness issue #{ticket}\n{issue_text}"
        print(block[:2000], file=sys.stderr)
        pre_text = f"{pre_text}\n\n{block}" if pre_text else block
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
    target = pick_target(project, args.task, args.scope, located_path)
    skill_block = ""
    if preloaded:
        skill_block = (
            "\n\n".join(render_skill(item, target, project) for item in preloaded)
            + "\n\n"
        )
    house = render_house_rules(project)
    prompt = (
        f"{render_brief(brief, scope=args.scope)}\n\n"
        + (f"{house}\n\n" if house else "")
        + f"{render_catalog(catalog)}\n\n"
        f"{skill_block}"
        + (f"{pre_text}\n\n" if pre_text else "")
        + f"Project root: {project}\n"
        + (f"Scope: {args.scope}\n" if args.scope else "")
        + f"Task: {args.task}\n"
        + start_hint(brief, args.task, located=bool(located_path))
    )
    loop_guard = LoopGuard()
    ran_tests = False
    for step in range(1, args.steps + 1):
        draft = generate_once(prompt)
        _remember(generate_once, prompt, draft)
        print(f"\n--- step {step} ---\n{draft}\n", flush=True)
        turn = parse_turn_smart(
            draft,
            question=looks_like_question(args.task),
            ship=looks_like_ship(args.task),
        )
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
            if not blocked:
                blocked = refuse_shallow_done(
                    args.task, turn.summary, located_sig
                )
            if not blocked:
                blocked = refuse_package_done(args.task, ran_tests)
            if blocked:
                prompt = blocked
                print(blocked[:500], file=sys.stderr)
                continue
            print(turn.summary or "done")
            return
        blocked = refuse_question_write(args.task, turn.action)
        if not blocked:
            blocked = refuse_redundant_explore(
                args.task, turn.action, turn.path, located_path
            )
        if not blocked:
            blocked = refuse_redundant_locate(
                args.task, turn.action, bool(pre_text)
            )
        if not blocked:
            located_body = ""
            if located_path:
                try:
                    located_body = read_py(project, located_path)
                except (OSError, ValueError):
                    located_body = ""
            blocked = refuse_smell_wrong_file(
                args.task,
                turn.action,
                turn.path,
                located_path,
                located_body,
            )
        if not blocked:
            blocked = loop_guard.check(turn)
        if not blocked and turn.action in {
            "issue",
            "branch",
            "commit",
            "push",
            "pr",
            "merge",
        }:
            if not looks_like_ship(args.task):
                blocked = (
                    "Ship actions only when the task is about an issue, PR, "
                    "commit, or push."
                )
            elif turn.action == "merge" and not looks_like_merge(args.task):
                blocked = "merge only when the task says merge"
        if blocked:
            prompt = blocked
            print(blocked[:500], file=sys.stderr)
            continue
        try:
            result, last_path = _tool(project, turn, last_path, args.scope, target)
        except (ValueError, OSError) as exc:
            result = str(exc)
        print(result[:2000], file=sys.stderr)
        if turn.action == "run" and result.startswith("exit 0"):
            ran_tests = True
        prompt = f"Tool result:\n{result}\n\nNext Action:"
        if (
            looks_like_add_feature(args.task)
            and turn.action == "patch"
            and "test" not in (turn.path or last_path).lower()
            and result.startswith("patched")
        ):
            loaded = get_skill("write-tests", project)
            if loaded is not None:
                prompt = (
                    f"Tool result:\n{result}\n\n"
                    f"{render_skill(loaded, target, project)}\n"
                    "Next Action must be this write-tests patch. "
                    "Do not Append after if __name__.\n"
                )
        if (
            looks_like_new_package(args.task)
            and turn.action in {"edit", "patch"}
            and result.startswith(("wrote", "patched"))
            and "__init__" in (turn.path or last_path)
        ):
            noun = question_symbol(args.task) or "service"
            prompt = (
                f"Tool result:\n{result}\n\n"
                f"Next Action must be edit Path: pkg/{noun}.py with one "
                f"function def {noun}(...). snake_case. Not in __init__.py.\n"
            )
        if (
            looks_like_new_package(args.task)
            and turn.action in {"edit", "patch"}
            and result.startswith(("wrote", "patched"))
            and "__init__" not in (turn.path or last_path)
            and "test" not in (turn.path or last_path).lower()
        ):
            noun = question_symbol(args.task) or "service"
            prompt = (
                f"Tool result:\n{result}\n\n"
                f"Next Action must be edit Path: tests/test_{noun}.py as a "
                f"unittest.TestCase that imports {noun}. Then Action: run.\n"
            )
        if (
            looks_like_new_package(args.task)
            and turn.action in {"edit", "patch"}
            and result.startswith(("wrote", "patched"))
            and "test" in (turn.path or last_path).lower()
        ):
            prompt = (
                f"Tool result:\n{result}\n\n"
                "Next Action must be run Argv: -m unittest discover -s tests -q\n"
            )
        if (
            looks_like_fix_smell(args.task)
            and turn.action == "patch"
            and "test" not in (turn.path or last_path).lower()
            and result.startswith("patched")
        ):
            old = smell_symbol(args.task)
            new = rename_target(args.task)
            if old and new:
                prompt = (
                    f"Tool result:\n{result}\n\n"
                    f"Next Action: patch tests to replace {old} with {new}, "
                    "then Action: run.\n"
                )
    sys.exit(f"stopped after {args.steps} steps")


if __name__ == "__main__":
    main()
