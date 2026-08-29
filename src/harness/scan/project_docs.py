"""Read the instructions a project publishes for contributors.

A project states its own conventions in `AGENTS.md`, `CLAUDE.md` or
`CONTRIBUTING.md`: where new code belongs, which test runner is used, what
must not be changed. Those instructions are more accurate for that project
than the general skills shipped with this harness, so they are placed
before them in the prompt.

The text is truncated to a fixed number of characters, because it is meant
as a short preface and not as the main content of the prompt.
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
