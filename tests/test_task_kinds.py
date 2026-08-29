"""Which kind of work a task asks for.

Every layer reads the task through these functions, so a wrong answer here
sends the wrong skill and the wrong first action.
"""

import unittest

from harness.skillkit.catalog import list_skills, pick_skills
from harness.task import (
    looks_like_add_feature,
    looks_like_question,
    looks_like_review_code,
    looks_unclear,
    names_something_concrete,
)


class ConcreteTest(unittest.TestCase):
    def test_a_call_is_concrete(self) -> None:
        self.assertTrue(names_something_concrete("add multiply(a, b)"))

    def test_a_file_path_is_concrete(self) -> None:
        self.assertTrue(names_something_concrete("review src/app.py"))

    def test_a_snake_case_name_is_concrete(self) -> None:
        self.assertTrue(names_something_concrete("rename calc to total_price"))

    def test_plain_english_is_not_concrete(self) -> None:
        self.assertFalse(names_something_concrete("clean this up"))


class UnclearTest(unittest.TestCase):
    def test_a_vague_short_task_is_unclear(self) -> None:
        for task in ("clean this up", "make it better", "fix the thing"):
            self.assertTrue(looks_unclear(task), task)

    def test_a_task_naming_a_symbol_is_clear(self) -> None:
        self.assertFalse(looks_unclear("add multiply(a, b) and a test"))

    def test_a_question_is_never_unclear(self) -> None:
        self.assertFalse(looks_unclear("what does it do?"))

    def test_a_long_task_is_not_treated_as_unclear(self) -> None:
        self.assertFalse(
            looks_unclear("go through the tree and tidy the naming everywhere please")
        )


class ReviewTest(unittest.TestCase):
    def test_review_is_review(self) -> None:
        self.assertTrue(looks_like_review_code("review src/app.py for bugs"))

    def test_adding_is_not_review(self) -> None:
        self.assertFalse(looks_like_review_code("add multiply(a, b)"))

    def test_a_question_is_still_a_question(self) -> None:
        self.assertTrue(looks_like_question("what does compute_total return?"))
        self.assertFalse(looks_like_add_feature("what does compute_total return?"))


class SkillChoiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = list_skills()

    def _names(self, task: str) -> list[str]:
        return [item.name for item in pick_skills(task, self.catalog)]

    def test_vague_task_offers_the_asking_skill(self) -> None:
        self.assertIn("ask-when-unclear", self._names("clean this up"))

    def test_review_task_offers_the_review_skill(self) -> None:
        self.assertIn("review-code", self._names("review src/app.py for bugs"))

    def test_add_task_still_offers_add_and_tests(self) -> None:
        names = self._names("add multiply(a, b) and a unit test")
        self.assertIn("add-feature", names)
        self.assertIn("write-tests", names)

    def test_a_clear_task_is_not_offered_the_asking_skill(self) -> None:
        self.assertNotIn(
            "ask-when-unclear", self._names("add multiply(a, b) and a test")
        )


if __name__ == "__main__":
    unittest.main()
