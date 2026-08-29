import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from harness.ship.git_ship import (
    commit_changes,
    current_branch,
    make_branch,
    merge_pr,
    push_branch,
)
from harness.task import issue_number, looks_like_add_feature, looks_like_ship


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "init.templateDir=", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


class GitShipTest(unittest.TestCase):
    def test_ship_task_kinds(self) -> None:
        self.assertTrue(looks_like_ship("fix #50 and open a PR"))
        self.assertTrue(looks_like_ship("create a pr for the rename"))
        self.assertEqual(issue_number("fix issue #50"), "50")
        self.assertFalse(looks_like_ship("create a package for total_price"))
        self.assertFalse(looks_like_add_feature("create a pr for #50"))
        self.assertFalse(looks_like_ship("what does apply_source refuse?"))

    def test_branch_and_commit_in_temp_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git(root, "init", "-b", "proceed/test")
            _git(root, "config", "user.email", "t@localhost")
            _git(root, "config", "user.name", "t")
            (root / "ok.py").write_text("print(1)\n", encoding="utf-8")
            _git(root, "add", "ok.py")
            _git(root, "commit", "-m", "start")
            out = make_branch(root, "proceed/quote-type")
            self.assertNotIn("bad branch", out)
            self.assertEqual(current_branch(root), "proceed/quote-type")
            self.assertIn("main", make_branch(root, "main"))
            (root / "ok.py").write_text("print(2)\n", encoding="utf-8")
            committed = commit_changes(root, "Explain why the print changed.")
            self.assertIn("quote-type", current_branch(root))
            self.assertTrue(
                "changed" in committed.lower() or "commit" in committed.lower()
            )
            self.assertIn("origin", push_branch(root))

    def test_merge_refused_without_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIn("merge only", merge_pr(Path(tmp), "16", allowed=False))


if __name__ == "__main__":
    unittest.main()
