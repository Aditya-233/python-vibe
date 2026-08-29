"""Point a kit skill at *this* project. Deterministic. No model.

A skill for an 8B is one copy-paste `Action:` block, so the paths inside it
have to be real. A kit skill that ships a fixture path (`pkg/mathy.py`) gets
copied verbatim, and the harness then creates that file in a stranger's
repo. So before the model sees a skill, every `Path:`/`Scope:` in it that
does not exist in the target project is rewritten to one that does.

Two mechanisms, both deterministic:

* `{{module}}` `{{test}}` `{{scope}}` `{{symbol}}` placeholders are filled.
* A `Path:` that is not a real file here is repointed — to the project's
  test file if it looks like a test, otherwise to its main module.

A skill whose paths already exist (the eval fixtures) is left alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from harness.task import question_symbol
from harness.scan.project_brief import iter_text_files

_PLACEHOLDER = re.compile(r"\{\{(module|test|scope|symbol)\}\}")
_PATH_LINE = re.compile(r"^(Path|File):\s*(\S+)\s*$", re.MULTILINE)
_SCOPE_LINE = re.compile(r"^Scope:\s*(\S+)\s*$", re.MULTILINE)
_SYMBOL_TOKEN = "the_symbol_from_the_task"
# Scaffolding a package legitimately names a file that does not exist yet.
_KEEP_NAMES = frozenset({"__init__.py"})
FALLBACK_MODULE = "path/to/module.py"
FALLBACK_TEST = "tests/test_module.py"


@dataclass(frozen=True)
class Target:
    module: str
    test: str
    scope: str
    symbol: str


def _is_test(rel: str) -> bool:
    parts = rel.replace("\\", "/").split("/")
    return "tests" in parts or parts[-1].startswith("test_")


def _rels(project: Path, suffix: str = ".py") -> list[tuple[str, int]]:
    root = project.resolve()
    return [
        (str(path.relative_to(root)), size)
        for path, size in iter_text_files(project)
        if path.suffix == suffix
    ]


def pick_module(project: Path, located_path: str = "") -> str:
    """The file a new function most likely belongs in."""
    if located_path:
        rel = located_path.replace("\\", "/").lstrip("./")
        if rel.endswith(".py") and not _is_test(rel):
            return rel
    usable = [
        (rel, size)
        for rel, size in _rels(project)
        if not _is_test(rel) and Path(rel).name != "__init__.py"
    ]
    if not usable:
        return FALLBACK_MODULE
    usable.sort(key=lambda item: (-item[1], item[0]))
    return usable[0][0]


def pick_test(project: Path, module: str) -> str:
    """The matching test file, else any test file, else the name to create."""
    stem = Path(module).stem
    tests = sorted(rel for rel, _size in _rels(project) if _is_test(rel))
    if not tests:
        return f"tests/test_{stem}.py" if stem else FALLBACK_TEST
    for rel in tests:
        if Path(rel).stem == f"test_{stem}":
            return rel
    return tests[0]


def pick_scope(scope: str, module: str) -> str:
    if scope:
        return scope
    parts = module.split("/")
    return parts[0] if len(parts) > 1 else "."


def pick_target(
    project: Path, task: str = "", scope: str = "", located_path: str = ""
) -> Target:
    module = pick_module(project, located_path)
    return Target(
        module=module,
        test=pick_test(project, module),
        scope=pick_scope(scope, module),
        symbol=question_symbol(task) or _SYMBOL_TOKEN,
    )


def retarget(body: str, target: Target, project: Path | None = None) -> str:
    """Fill placeholders, then repoint any path this project does not have."""
    values = {
        "module": target.module,
        "test": target.test,
        "scope": target.scope,
        "symbol": target.symbol,
    }
    text = _PLACEHOLDER.sub(lambda m: values[m.group(1)], body)
    if target.symbol != _SYMBOL_TOKEN:
        text = text.replace(_SYMBOL_TOKEN, target.symbol)
    if project is None:
        return text
    root = project.resolve()

    def _path(match: re.Match[str]) -> str:
        key, rel = match.group(1), match.group(2)
        if (root / rel).is_file() or Path(rel).name in _KEEP_NAMES:
            return match.group(0)
        return f"{key}: {target.test if _is_test(rel) else target.module}"

    def _scope(match: re.Match[str]) -> str:
        rel = match.group(1)
        if (root / rel).is_dir():
            return match.group(0)
        return f"Scope: {target.scope}"

    text = _PATH_LINE.sub(_path, text)
    return _SCOPE_LINE.sub(_scope, text)
