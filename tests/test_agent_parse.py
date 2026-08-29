import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from harness.agent_parse import parse_turn


class AgentParseTest(unittest.TestCase):
    def test_grep(self) -> None:
        turn = parse_turn("Action: grep\nQuery: def main")
        self.assertIsNotNone(turn)
        self.assertEqual(turn.action, "grep")
        self.assertEqual(turn.query, "def main")

    def test_edit_with_fence(self) -> None:
        turn = parse_turn(
            "Action: edit\nPath: src/foo.py\n```python\nprint(1)\n```\n"
        )
        self.assertEqual(turn.action, "edit")
        self.assertEqual(turn.path, "src/foo.py")
        self.assertEqual(turn.source, "print(1)")

    def test_patch(self) -> None:
        turn = parse_turn(
            "Action: patch\nPath: pkg/util_stats.py\nFind: return tota\n"
            "Replace: return sum(cleaned)\n"
        )
        self.assertEqual(turn.action, "patch")
        self.assertEqual(turn.find, "return tota")
        self.assertEqual(turn.replace, "return sum(cleaned)")

    def test_done(self) -> None:
        turn = parse_turn("Action: done\nSummary: nothing to fix")
        self.assertEqual(turn.action, "done")
        self.assertIn("nothing", turn.summary)

    def test_unparsed(self) -> None:
        self.assertIsNone(parse_turn("no issues"))


if __name__ == "__main__":
    unittest.main()
