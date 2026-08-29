#!/usr/bin/env python3
"""One-turn probe: how this Ollama model uses a skill. No writes.

  PYTHONPATH=src python3.13 scripts/skill_probe.py --project eval/fixtures/add_feature_pkg \\
    --skill add-feature "add a function multiply(a, b) and a unit test"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finetune.agent_system import AGENT_SYSTEM  # noqa: E402
from finetune.everyday import DEFAULT_EVERYDAY_OLLAMA  # noqa: E402
from harness.act.parse import parse_turn_smart  # noqa: E402
from harness.model.engine import make_generate  # noqa: E402
from harness.task import looks_like_question
from harness.scan.project_brief import (  # noqa: E402
    classify_project,
    render_brief,
    start_hint,
)
from harness.skillkit.target import pick_target  # noqa: E402
from harness.skillkit.catalog import get_skill, list_skills, pick_skills, render_catalog, render_skill  # noqa: E402
from harness.locate import prelude  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--scope", default="")
    parser.add_argument("--skill", action="append", default=[])
    parser.add_argument("--model", default=DEFAULT_EVERYDAY_OLLAMA)
    parser.add_argument("--max-tokens", type=int, default=400)
    parser.add_argument("--no-prelude", action="store_true")
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    brief = classify_project(project, args.scope)
    catalog = list_skills(project)
    preloaded = [get_skill(name, project) for name in args.skill]
    preloaded = [item for item in preloaded if item is not None]
    if not preloaded:
        preloaded = pick_skills(args.task, catalog)
    pre_text, _path = ("", "")
    if not args.no_prelude:
        pre_text, _path = prelude(project, args.task, args.scope)
    prompt = (
        f"{render_brief(brief, scope=args.scope)}\n\n"
        f"{render_catalog(catalog)}\n\n"
        + (
            "\n\n".join(
                render_skill(item, pick_target(project, args.task, args.scope, _path), project)
                for item in preloaded
            )
            + "\n\n"
            if preloaded
            else ""
        )
        + (f"{pre_text}\n\n" if pre_text else "")
        + f"Task: {args.task}\n"
        + start_hint(brief, args.task, located=bool(_path))
    )
    _label, generate_once = make_generate(
        "ollama", args.max_tokens, model=args.model, system=AGENT_SYSTEM
    )
    draft = generate_once(prompt)
    turn = parse_turn_smart(draft, question=looks_like_question(args.task))
    row = {
        "model": args.model,
        "task": args.task,
        "skills": [item.name for item in preloaded],
        "prelude": bool(pre_text),
        "action": turn.action if turn else None,
        "path": turn.path if turn else "",
        "query": turn.query if turn else "",
        "append": bool(turn.append) if turn else False,
        "draft_head": (draft or "")[:240],
    }
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
