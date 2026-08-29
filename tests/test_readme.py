"""README contributor list is a workflow marker, not a hardcoded table."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
WORKFLOW = ROOT / ".github" / "workflows" / "contributors.yml"
CELEBRATE = ROOT / ".github" / "workflows" / "celebrate-merge.yml"

_START = "<!-- readme: contributors,bots/- -start -->"
_END = "<!-- readme: contributors,bots/- -end -->"


class ReadmeContributorsTest(unittest.TestCase):
    def test_markers_not_hardcoded_table(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn(_START, text)
        self.assertIn(_END, text)
        self.assertEqual(text.count(_START), 1)
        self.assertLess(text.index(_START), text.index(_END))
        self.assertNotIn("contrib.rocks", text)
        self.assertNotIn("| Contributor | Commits |", text)

    def test_workflow_reads_github_api(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("akhilmhdh/contributors-readme-action@", text)
        self.assertIn("github-actions[bot]", text)
        self.assertNotIn("YauhenBichel", text)
        self.assertNotIn("ItzSaurav", text)

    def test_celebrate_merge_uses_giphy_not_hardcoded_gifs(self) -> None:
        text = CELEBRATE.read_text(encoding="utf-8")
        self.assertIn("pull_request_target", text)
        self.assertIn("api.giphy.com", text)
        self.assertIn("rating", text)
        self.assertIn("GIPHY_API_KEY", text)
        self.assertNotIn("media.giphy.com/media/", text)
        self.assertNotIn("YauhenBichel", text)
