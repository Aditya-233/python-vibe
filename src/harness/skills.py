"""Load SKILL.md files. Deterministic. No model.

Looks in the project `skills/` folder and the python-vibe kit
(`<repo>/skills`). Same name: project wins.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_FRONT = re.compile(r"^---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
_NAME = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
_DESC = re.compile(r"^description:\s*(.+)$", re.MULTILINE)
_ADD_START = re.compile(
    r"^(please\s+)?(add|implement|introduce|create)\b|new feature"
)
MAX_SKILL_CHARS = 2500


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    body: str
    path: Path


def kit_skills_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "skills"


def _parse_skill(path: Path) -> Skill | None:
    text = path.read_text(encoding="utf-8")
    match = _FRONT.match(text)
    if not match:
        return None
    meta, body = match.group(1), match.group(2).strip()
    name = _NAME.search(meta)
    desc = _DESC.search(meta)
    raw_name = name.group(1).strip() if name else path.parent.name
    if not raw_name or not desc:
        return None
    return Skill(
        name=raw_name,
        description=desc.group(1).strip(),
        body=body,
        path=path,
    )


def _scan_dir(root: Path) -> dict[str, Skill]:
    found: dict[str, Skill] = {}
    if not root.is_dir():
        return found
    for skill_md in sorted(root.glob("*/SKILL.md")):
        parsed = _parse_skill(skill_md)
        if parsed:
            found[parsed.name] = parsed
    return found


def list_skills(project: Path | None = None, extra: Path | None = None) -> list[Skill]:
    merged: dict[str, Skill] = {}
    merged.update(_scan_dir(kit_skills_dir()))
    if extra:
        merged.update(_scan_dir(extra))
    if project:
        merged.update(_scan_dir(project.resolve() / "skills"))
    return sorted(merged.values(), key=lambda item: item.name)


def get_skill(name: str, project: Path | None = None) -> Skill | None:
    key = name.strip().lower()
    for skill in list_skills(project):
        if skill.name.lower() == key:
            return skill
    return None


def looks_like_add_feature(task: str) -> bool:
    text = task.strip().lower()
    from harness.project_brief import looks_like_question

    if looks_like_question(text):
        return False
    return bool(_ADD_START.search(text))


def pick_skills(task: str, catalog: list[Skill]) -> list[Skill]:
    picked: list[Skill] = []
    if looks_like_add_feature(task):
        picked.extend(s for s in catalog if s.name == "add-feature")
        picked.extend(s for s in catalog if s.name == "write-tests")
    lowered = task.strip().lower()
    if "test" in lowered and not any(s.name == "write-tests" for s in picked):
        picked.extend(s for s in catalog if s.name == "write-tests")
    return picked


def render_catalog(catalog: list[Skill]) -> str:
    if not catalog:
        return "Skills: (none)"
    lines = ["Skills (Action: skill + Name: …, or --skill):"]
    for skill in catalog:
        lines.append(f"  {skill.name} — {skill.description}")
    return "\n".join(lines)


def render_skill(skill: Skill) -> str:
    body = skill.body
    if len(body) > MAX_SKILL_CHARS:
        body = body[:MAX_SKILL_CHARS] + "\n# … skill truncated\n"
    return f"# skill {skill.name}\n{skill.description}\n\n{body}"
