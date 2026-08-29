"""Jailed git and gh. Deterministic. No model. No force. No main."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

PROTECTED = frozenset({"main", "master"})
_BRANCH = re.compile(r"^[A-Za-z0-9._][A-Za-z0-9._/-]{0,79}$")
SECRET_NAMES = frozenset(
    {".env", ".env.local", "credentials.json", ".pypirc", "secrets.json"}
)
_TIMEOUT = 45


def _run(
    project: Path,
    argv: list[str],
    *,
    env: dict[str, str] | None = None,
) -> tuple[int, str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    merged.setdefault("GIT_AUTHOR_NAME", "python-vibe")
    merged.setdefault("GIT_AUTHOR_EMAIL", "python-vibe@localhost")
    merged.setdefault("GIT_COMMITTER_NAME", merged["GIT_AUTHOR_NAME"])
    merged.setdefault("GIT_COMMITTER_EMAIL", merged["GIT_AUTHOR_EMAIL"])
    try:
        proc = subprocess.run(
            argv,
            cwd=project,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
            check=False,
            env=merged,
        )
    except FileNotFoundError:
        return 127, f"{argv[0]} is not on PATH"
    except subprocess.TimeoutExpired:
        return 124, "timed out"
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, out[-4000:]


def git_root(project: Path) -> Path | None:
    code, out = _run(project, ["git", "rev-parse", "--show-toplevel"])
    if code != 0:
        return None
    try:
        return Path(out.splitlines()[0]).resolve()
    except (IndexError, OSError):
        return None


def _in_project(project: Path) -> str:
    root = git_root(project)
    if root is None:
        return "not a git repository"
    if root != project.resolve():
        return f"git root is {root}, not {project} — refuse"
    return ""


def current_branch(project: Path) -> str:
    code, out = _run(project, ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return out.splitlines()[0] if code == 0 and out else ""


def read_issue(project: Path, number: str) -> str:
    if not number.isdigit():
        return "issue needs Number: (digits)"
    code, out = _run(
        project,
        ["gh", "issue", "view", number, "--json", "number,title,body,state,labels"],
    )
    if code != 0:
        return out or f"gh issue view {number} failed"
    return out[:3500]


def make_branch(project: Path, name: str) -> str:
    blocked = _in_project(project)
    if blocked:
        return blocked
    name = name.strip().lstrip("/")
    if not _BRANCH.match(name) or name in PROTECTED or name.startswith("-"):
        return (
            "bad branch name. Use proceed/short-slug "
            "(letters, digits, . _ / -). Not main or master."
        )
    code, out = _run(project, ["git", "checkout", "-B", name])
    return out or f"now on {name}" if code == 0 else out


def commit_changes(project: Path, summary: str) -> str:
    blocked = _in_project(project)
    if blocked:
        return blocked
    message = " ".join(summary.strip().split())
    if len(message) < 8:
        return "commit needs Summary: of at least 8 characters (why, not what)"
    _run(project, ["git", "add", "-A"])
    for rel in SECRET_NAMES:
        path = project / rel
        if path.exists() or path.is_symlink():
            _run(project, ["git", "reset", "-q", "--", rel])
    code, staged = _run(project, ["git", "diff", "--cached", "--name-only"])
    names = [line for line in staged.splitlines() if line.strip()] if code == 0 else []
    if any(Path(name).name in SECRET_NAMES for name in names):
        return "refusing to commit secret filenames"
    if not names:
        return "nothing to commit"
    code, out = _run(project, ["git", "commit", "-m", message])
    return out or "committed" if code == 0 else out


def push_branch(project: Path) -> str:
    blocked = _in_project(project)
    if blocked:
        return blocked
    branch = current_branch(project)
    if not branch or branch in PROTECTED:
        return f"refusing to push {branch or 'detached'} (not main/master)"
    code, remotes = _run(project, ["git", "remote"])
    if code != 0 or "origin" not in remotes.split():
        return "no origin remote. Add origin or push yourself."
    code, out = _run(project, ["git", "push", "-u", "origin", "HEAD"])
    return out or "pushed" if code == 0 else out


def create_pr(project: Path, title: str, body: str) -> str:
    blocked = _in_project(project)
    if blocked:
        return blocked
    branch = current_branch(project)
    if branch in PROTECTED:
        return "refusing to open a PR from main/master. Action: branch first."
    title = " ".join(title.strip().split())
    if len(title) < 8:
        return "pr needs Title: of at least 8 characters"
    text = body.strip() or title
    code, out = _run(
        project,
        ["gh", "pr", "create", "--title", title, "--body", text],
    )
    return out or "opened pull request" if code == 0 else out


def merge_pr(project: Path, number: str, *, allowed: bool) -> str:
    if not allowed:
        return "merge only when the task says merge"
    if not number.isdigit():
        return "merge needs Number: (PR digits)"
    blocked = _in_project(project)
    if blocked:
        return blocked
    code, out = _run(project, ["gh", "pr", "merge", number, "--merge"])
    return out or f"merged #{number}" if code == 0 else out
