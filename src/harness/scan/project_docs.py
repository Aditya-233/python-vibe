"""Read the target project's own agent instructions. Deterministic. No model.

Every mature harness loads the repo's `AGENTS.md` before it acts. This one
walked into other people's repos with only its own kit conventions, so it
had no way to know that *this* project puts tests somewhere else or forbids
a dependency. Budgeted hard: house rules are a preamble, not the context.
"""

from __future__ import annotations

from pathlib import Path

DOC_NAMES = ("AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md")
MAX_DOC_CHARS = 1200


def find_doc(project: Path) -> Path | None:
    root = project.resolve()
    for name in DOC_NAMES:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def render_house_rules(project: Path, *, limit: int = MAX_DOC_CHARS) -> str:
    doc = find_doc(project)
    if doc is None:
        return ""
    try:
        text = doc.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    if not text:
        return ""
    if len(text) > limit:
        text = text[:limit].rstrip() + "\n# … truncated"
    return f"House rules from {doc.name} (follow them over the kit skill):\n{text}"
