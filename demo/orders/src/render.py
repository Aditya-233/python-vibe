"""Line rendering."""

from src.report import build_report


def render_line(value: int) -> str:
    return f"- {value}"


def render_all(rows: list[int]) -> str:
    return build_report(rows)
