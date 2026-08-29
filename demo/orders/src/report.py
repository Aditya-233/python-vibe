"""Order report."""

from src.render import render_line


def build_report(rows: list[int]) -> str:
    return "\n".join(render_line(row) for row in rows)
