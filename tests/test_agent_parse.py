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

    def test_patch_append(self) -> None:
        turn = parse_turn(
            "Action: patch\nPath: pkg/mathy.py\nAppend:\n"
            "def multiply(a: int, b: int) -> int:\n    return a * b\n"
        )
        self.assertIsNotNone(turn)
        assert turn is not None
        self.assertEqual(turn.action, "patch")
        self.assertIn("def multiply", turn.append)
        self.assertIn("return a * b", turn.append)

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

    def test_map_and_plan(self) -> None:
        mapped = parse_turn("Action: map\nScope: src/harness")
        self.assertIsNotNone(mapped)
        assert mapped is not None
        self.assertEqual(mapped.action, "map")
        self.assertEqual(mapped.scope, "src/harness")
        plan = parse_turn("Action: plan\nSummary: read then patch")
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan.action, "plan")
        self.assertEqual(plan.summary, "read then patch")

    def test_unparsed(self) -> None:
        self.assertIsNone(parse_turn("no issues"))


if __name__ == "__main__":
    unittest.main()
