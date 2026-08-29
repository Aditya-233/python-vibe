import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from harness.act.parse import parse_turn, parse_turn_smart


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

    def test_smart_prefers_patch_in_a_menu_dump(self) -> None:
        draft = (
            "Action: skill\nName: add-feature\n\n"
            "Action: patch\nPath: pkg/mathy.py\nAppend:\n"
            "def multiply(a: int, b: int) -> int:\n    return a * b\n"
        )
        turn = parse_turn_smart(draft)
        self.assertIsNotNone(turn)
        assert turn is not None
        self.assertEqual(turn.action, "patch")
        self.assertIn("def multiply", turn.append)
        q = parse_turn_smart(
            "Action: patch\nPath: x.py\nAppend:\nz\n\nAction: done\nSummary: empty draft\n",
            question=True,
        )
        assert q is not None
        self.assertEqual(q.action, "done")

    def test_edit_append_is_source(self) -> None:
        turn = parse_turn(
            "Action: edit\nPath: pkg/__init__.py\n"
            'Append:\n"""Public exports only."""\n'
        )
        assert turn is not None
        self.assertEqual(turn.action, "edit")
        self.assertIn("Public exports", turn.source or "")

    def test_file_alias_is_path(self) -> None:
        turn = parse_turn("Action: read\nFile: src/harness/http.py")
        self.assertIsNotNone(turn)
        assert turn is not None
        self.assertEqual(turn.action, "read")
        self.assertEqual(turn.path, "src/harness/http.py")

    def test_issue_and_pr_fields(self) -> None:
        issue = parse_turn("Action: issue\nNumber: 50")
        assert issue is not None
        self.assertEqual(issue.action, "issue")
        self.assertEqual(issue.number, "50")
        pr = parse_turn(
            "Action: pr\nTitle: After locate, questions must Action: done\n"
            "Body: Closes #50\n"
        )
        assert pr is not None
        self.assertEqual(pr.action, "pr")
        self.assertIn("locate", pr.title)
        self.assertIn("Closes", pr.body)

    def test_unparsed(self) -> None:
        self.assertIsNone(parse_turn("no issues"))


if __name__ == "__main__":
    unittest.main()
