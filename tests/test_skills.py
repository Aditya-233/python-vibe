import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from harness.agent_parse import parse_turn
from harness.skills import (
    get_skill,
    list_skills,
    looks_like_add_feature,
    pick_skills,
    render_catalog,
    render_skill,
    skill_from_action,
)

ROOT = Path(__file__).resolve().parents[1]


class SkillsTest(unittest.TestCase):
    def test_kit_lists_add_feature(self) -> None:
        catalog = list_skills(ROOT)
        names = {item.name for item in catalog}
        self.assertEqual(names, {"add-feature", "write-tests", "stay-scoped"})
        loaded = get_skill("add-feature", ROOT)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertIn("When to add", loaded.body)

    def test_pick_on_add_task_not_on_question(self) -> None:
        catalog = list_skills(ROOT)
        self.assertTrue(looks_like_add_feature("add a function multiply and a test"))
        self.assertFalse(looks_like_add_feature("what does add return?"))
        picked = pick_skills("add a function multiply(a, b) and a unit test", catalog)
        self.assertEqual([item.name for item in picked], ["add-feature", "write-tests"])
        self.assertEqual(pick_skills("what does add return?", catalog), [])

    def test_render_and_parse_skill_action(self) -> None:
        catalog = list_skills(ROOT)
        text = render_catalog(catalog)
        self.assertIn("add-feature", text)
        skill = get_skill("write-tests", ROOT)
        assert skill is not None
        self.assertIn("unittest", render_skill(skill))
        turn = parse_turn("Action: skill\nName: add-feature")
        self.assertIsNotNone(turn)
        assert turn is not None
        self.assertEqual(turn.action, "skill")
        self.assertEqual(turn.name, "add-feature")

    def test_action_write_tests_is_a_skill(self) -> None:
        shortcut = skill_from_action("write-tests", project=ROOT)
        self.assertIsNotNone(shortcut)
        assert shortcut is not None
        self.assertEqual(shortcut.name, "write-tests")
        self.assertIsNone(skill_from_action("grep", project=ROOT))
        named = skill_from_action("skill", name="add-feature", project=ROOT)
        self.assertIsNotNone(named)
        assert named is not None
        self.assertEqual(named.name, "add-feature")


if __name__ == "__main__":
    unittest.main()
