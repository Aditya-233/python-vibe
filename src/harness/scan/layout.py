"""Report why a project is difficult to read, and what to change first.

Four problems are detected, listed here in the order they are worth
fixing:

* `cycle`    - two modules import each other, so neither can be read alone.
* `flat`     - one directory holds many modules with no grouping.
* `god`      - one module is much larger than the others around it.
* `no-tests` - the project contains no test files.

Only the first problem is turned into an instruction. A model given four
instructions at once tends to change four things at once; a model given one
instruction changes one thing, which can then be checked.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from harness.scan.project_scan import SKIP_DIR

FLAT_MAX_MODULES = 12
GOD_RATIO = 3
GOD_MIN_BYTES = 6000
MAX_FINDINGS = 4


@dataclass(frozen=True)
class Finding:
    """One structural problem found in a project.

    Fields:
        kind: "cycle", "flat", "god" or "no-tests".
        detail: what was found, naming the files involved.
        move: the change to make, written as an instruction.
    """

    kind: str
    detail: str
    move: str


def _modules(project: Path) -> list[Path]:
    root = project.resolve()
    return [
        path
        for path in sorted(root.rglob("*.py"))
        if not any(part in SKIP_DIR for part in path.parts)
    ]


def _local_imports(path: Path, root: Path) -> set[str]:
    """Imported module stems that are files in this project."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[-1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[-1])
    return names


def find_cycles(project: Path) -> list[tuple[str, str]]:
    root = project.resolve()
    modules = _modules(project)
    by_stem = {path.stem: path for path in modules}
    graph = {
        path.stem: _local_imports(path, root) & set(by_stem) - {path.stem}
        for path in modules
    }
    pairs = {
        tuple(sorted((stem, other)))
        for stem, deps in graph.items()
        for other in deps
        if stem in graph.get(other, set())
    }
    return sorted(pairs)


def find_flat_packages(project: Path) -> list[tuple[str, int]]:
    root = project.resolve()
    counts: dict[str, int] = {}
    for path in _modules(project):
        parent = path.parent
        key = str(parent.relative_to(root)) if parent != root else "."
        counts[key] = counts.get(key, 0) + 1
    return sorted(
        ((name, n) for name, n in counts.items() if n > FLAT_MAX_MODULES),
        key=lambda item: (-item[1], item[0]),
    )


def find_god_modules(project: Path) -> list[tuple[str, int]]:
    root = project.resolve()
    sizes = []
    for path in _modules(project):
        try:
            sizes.append((str(path.relative_to(root)), path.stat().st_size))
        except OSError:
            continue
    if len(sizes) < 3:
        return []
    median = sorted(size for _rel, size in sizes)[len(sizes) // 2]
    return sorted(
        (
            (rel, size)
            for rel, size in sizes
            if size >= GOD_MIN_BYTES and size > median * GOD_RATIO
        ),
        key=lambda item: -item[1],
    )


def has_tests(project: Path) -> bool:
    root = project.resolve()
    return any(
        path.name.startswith("test_")
        for path in root.rglob("test_*.py")
        if not any(part in SKIP_DIR for part in path.parts)
    )


def review_layout(project: Path) -> list[Finding]:
    out: list[Finding] = []
    for left, right in find_cycles(project):
        out.append(
            Finding(
                "cycle",
                f"{left}.py and {right}.py import each other",
                f"Move what they share into a new module both import. "
                f"Action: grep Query: def .*  Path: {left}.py",
            )
        )
    for name, count in find_flat_packages(project):
        out.append(
            Finding(
                "flat",
                f"{name}/ holds {count} modules with no grouping",
                f"Group {name}/ by what each module is for, one folder per "
                "job, and give each folder an __init__.py that says so.",
            )
        )
    for rel, size in find_god_modules(project):
        out.append(
            Finding(
                "god",
                f"{rel} is {size // 1024} KB — far larger than its neighbours",
                f"Action: read Path: {rel} and split the one group of "
                "functions that does not belong with the rest.",
            )
        )
    if not has_tests(project):
        out.append(
            Finding(
                "no-tests",
                "no test_*.py anywhere in this project",
                "Action: patch Path: tests/test_smoke.py with one unittest "
                "for the function you touch next.",
            )
        )
    return out[:MAX_FINDINGS]


def render_layout(project: Path) -> str:
    findings = review_layout(project)
    if not findings:
        return (
            "layout: no cycles, no oversized package, no god module, tests "
            "present. Nothing to restructure — do the task."
        )
    lines = [f"layout: {len(findings)} finding(s), worst first."]
    for finding in findings:
        lines.append(f"  [{finding.kind}] {finding.detail}")
    lines.append("")
    lines.append(f"Next move (do only this one): {findings[0].move}")
    return "\n".join(lines)
