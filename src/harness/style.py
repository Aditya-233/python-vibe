"""SoC / readable-name guards. Deterministic. No model."""

from __future__ import annotations

import re

_DEF = re.compile(r"^def\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
_CLASS = re.compile(r"^class\s+([A-Za-z_]\w*)", re.MULTILINE)
_OK_PARAM = frozenset({"self", "cls", "i", "j", "k"})
_OPAQUE = frozenset(
    {
        "btn",
        "calc",
        "data",
        "do",
        "fn",
        "foo",
        "bar",
        "baz",
        "func",
        "helper",
        "mgr",
        "misc",
        "obj",
        "proc",
        "stuff",
        "temp",
        "thing",
        "tmp",
        "util",
        "val",
        "var",
    }
)
_SMELL = re.compile(
    r"\b(code smell|smell|rename|readable name|human[- ]readable|clean up|cleanup)\b"
)
_PACKAGE = re.compile(
    r"\b(scaffold|project structure|new package|new project|"
    r"create a package|create a project|create a pkg)\b"
)
_RENAME = re.compile(
    r"\brename\s+([A-Za-z_][A-Za-z0-9_]*)\s+to\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.I,
)


def looks_like_new_package(task: str) -> bool:
    from harness.project_brief import looks_like_question

    if looks_like_question(task):
        return False
    return bool(_PACKAGE.search(task.strip().lower()))


def looks_like_fix_smell(task: str) -> bool:
    from harness.project_brief import looks_like_question

    if looks_like_question(task):
        return False
    return bool(_SMELL.search(task.strip().lower()))


_SMELL_SKIP = frozenset(
    {
        "the",
        "code",
        "smell",
        "rename",
        "readable",
        "human",
        "clean",
        "cleanup",
        "fix",
        "name",
        "names",
        "function",
        "please",
        "this",
        "that",
        "with",
        "from",
    }
)


def smell_symbol(task: str) -> str:
    match = _RENAME.search(task)
    if match:
        return match.group(1)
    names = re.findall(r"\b([a-z_][a-z0-9_]{2,})\b", task.lower())
    hits = [name for name in names if name not in _SMELL_SKIP]
    return hits[-1] if hits else ""


def rename_target(task: str) -> str:
    match = _RENAME.search(task)
    return match.group(2) if match else ""


def _opaque_param(draft: str) -> str:
    for match in re.finditer(r"^def\s+\w+\s*\((.*?)\)", draft, re.MULTILINE | re.DOTALL):
        for part in match.group(1).split(","):
            token = part.strip()
            if not token or token.startswith("*"):
                continue
            name = token.split(":")[0].split("=")[0].strip()
            if name in _OK_PARAM:
                continue
            if len(name) == 1 or name in _OPAQUE:
                return (
                    f"opaque parameter {name}. Use a readable noun "
                    f"(quantity, unit_price), not x or tmp."
                )
    return ""


def refuse_opaque_names(draft: str) -> str:
    if not draft.strip():
        return ""
    for match in _DEF.finditer(draft):
        name = match.group(1)
        if name.startswith("test_") or (name.startswith("__") and name.endswith("__")):
            continue
        if len(name) == 1 or name in _OPAQUE:
            return (
                f"opaque name {name}. Use a readable snake_case verb_noun "
                f"(total_price, not calc or tmp)."
            )
        if name != name.lower() or any(ch.isupper() for ch in name):
            return f"functions are snake_case: {name}"
    param = _opaque_param(draft)
    if param:
        return param
    for match in _CLASS.finditer(draft):
        name = match.group(1)
        if name[0].islower() or "_" in name:
            return f"classes are PascalCase: {name}"
    return ""


def refuse_smell_wrong_file(
    task: str,
    action: str,
    path: str,
    located_path: str,
    located_body: str = "",
) -> str:
    if not looks_like_fix_smell(task) or action != "patch" or not located_path:
        return ""
    rel = path.replace("\\", "/").lower()
    located = located_path.replace("\\", "/").lower()
    if "test" not in rel or "test" in located:
        return ""
    old = smell_symbol(task)
    if old and located_body and not re.search(rf"\bdef\s+{re.escape(old)}\b", located_body):
        return ""
    return (
        f"rename the implementation first. "
        f"Action: patch Path: {located_path} Find: the old def line."
    )


def refuse_layout(rel: str, original: str, draft: str) -> str:
    posix = rel.replace("\\", "/").lstrip("./")
    has_impl = bool(re.search(r"^(async\s+)?(def |class )", draft, re.MULTILINE))
    if posix.endswith("__init__.py") and has_impl:
        return (
            "SoC: __init__.py is exports only. "
            "Action: edit Path: pkg/<noun>.py with the function."
        )
    if (posix.startswith("scripts/") or "/scripts/" in posix) and has_impl:
        if "def main" not in draft:
            return "SoC: library code is not in scripts/. Use pkg/<noun>.py"
    if has_impl and original:
        count = len(re.findall(r"^def ", original, re.MULTILINE))
        if count >= 4:
            return (
                f"SoC: {posix} already has {count} functions. "
                "Action: edit Path: pkg/<new_concern>.py with only the new function."
            )
    return ""
