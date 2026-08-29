"""Mechanical fixes the 8B fails to express. Deterministic. No model.

Live 8B (29 Aug 2026): left `subtotal` unbound after a NameError task, and
spent twelve `Find:` turns that never matched `def calc(x: int, ...)`.
Those are compiler jobs. The harness does them, then runs the suite,
before the first generate. A green suite ends the run without a model.
"""

from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path

from harness.act.code import apply_source
from harness.scan.names import undefined_names
from harness.task import (
    looks_like_bugfix,
    looks_like_fix_smell,
    named_project_file,
    rename_pair,
)


def levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    prev = list(range(len(right) + 1))
    for i, char in enumerate(left, 1):
        cur = [i]
        for j, other in enumerate(right, 1):
            cur.append(
                min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (char != other))
            )
        prev = cur
    return prev[-1]


def _is_typo(bad: str, good: str) -> bool:
    if bad == good or good.startswith("__"):
        return False
    gap = abs(len(bad) - len(good))
    if gap > 2:
        return False
    distance = levenshtein(bad, good)
    if distance == 1:
        return True
    return distance == 2 and min(len(bad), len(good)) >= 6


def typo_pairs(source: str) -> list[tuple[str, str]]:
    """Unique undefined-name → nearby bound-name pairs."""
    leftover = undefined_names(source)
    if not leftover:
        return []
    try:
        import ast

        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bound.add(node.id)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bound.add(node.name)
            for arg in (*node.args.args, *node.args.posonlyargs, *node.args.kwonlyargs):
                bound.add(arg.arg)
    pairs: list[tuple[str, str]] = []
    for bad in leftover:
        hits = [good for good in bound if _is_typo(bad, good)]
        if len(hits) == 1:
            pairs.append((bad, hits[0]))
    return pairs


def _rename_name_tokens(source: str, bad: str, good: str) -> str:
    """Replace `bad` where Python reads it as a name, and nowhere else.

    A plain search also rewrites the word inside strings and comments. An
    error message that mentions the misspelling is text the person wrote,
    and the harness has no business changing it.
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return source
    lines = source.splitlines(keepends=True)
    spots = [
        token
        for token in tokens
        if token.type == tokenize.NAME and token.string == bad
    ]
    for token in reversed(spots):
        row = token.start[0] - 1
        line = lines[row]
        lines[row] = line[: token.start[1]] + good + line[token.end[1] :]
    return "".join(lines)


def apply_typo_fixes(source: str) -> str:
    text = source
    for bad, good in typo_pairs(source):
        text = _rename_name_tokens(text, bad, good)
    return text


def apply_function_rename(source: str, old: str, new: str) -> str:
    """Rename one `def old` and `old(` calls. Keep the rest of the signature.

    Matching requires a call shape, so prose that merely mentions the name
    is left alone. Text inside a string that looks like a call is rewritten
    too; for a message naming the function that is usually wanted, and it
    is the same on every supported Python version, which a token-based
    rename would not be.
    """
    if not old or not new or old == new:
        return source
    if not re.search(rf"^def {re.escape(old)}\b", source, re.MULTILINE):
        return source
    if re.search(rf"^def {re.escape(new)}\b", source, re.MULTILINE):
        return source
    text = re.sub(
        rf"^def {re.escape(old)}\b",
        f"def {new}",
        source,
        count=1,
        flags=re.MULTILINE,
    )
    return re.sub(rf"\b{re.escape(old)}\s*\(", f"{new}(", text)


def apply_mechanical(project: Path, task: str, rel: str) -> str:
    """Write a rename or unique typo fix. Return a note, or empty."""
    if not rel:
        rel = named_project_file(task, project)
    if not rel:
        return ""
    path = Path(project) / rel
    if not path.is_file():
        return ""
    try:
        original = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    text = original
    notes: list[str] = []
    if looks_like_fix_smell(task):
        old, new = rename_pair(task)
        if old and new:
            renamed = apply_function_rename(text, old, new)
            if renamed != text:
                text = renamed
                notes.append(f"renamed def {old} → def {new} in {rel}")
    if looks_like_bugfix(task):
        fixed = apply_typo_fixes(text)
        if fixed != text:
            pairs = typo_pairs(original)
            text = fixed
            shown = ", ".join(f"{bad} → {good}" for bad, good in pairs)
            notes.append(f"bound unique NameError typo ({shown}) in {rel}")
    if text == original or not notes:
        return ""
    apply_source(path, text, original=original)
    return (
        "Harness applied a mechanical fix (no model):\n"
        + "\n".join(f"- {item}" for item in notes)
        + "\nNext Action must be run Argv: -m unittest discover -s tests -q. "
        "Do not patch this file again."
    )
