import tempfile
import unittest
from pathlib import Path

from harness.skillkit.target import (
    FALLBACK_MODULE,
    Target,
    pick_target,
    retarget,
)
from harness.skillkit.catalog import get_skill, render_skill

MODULE = "def compute_total(rows: list[int]) -> int:\n    return sum(rows)\n"
TEST = (
    "import unittest\n\n\nclass AppTest(unittest.TestCase):\n"
    "    def test_total(self) -> None:\n        self.assertEqual(1, 1)\n"
)


def _project(tmp: str) -> Path:
    project = Path(tmp)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / "src" / "app.py").write_text(MODULE, encoding="utf-8")
    (project / "tests" / "test_app.py").write_text(TEST, encoding="utf-8")
    return project


class PickTargetTest(unittest.TestCase):
    def test_picks_a_real_module_and_test(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = pick_target(_project(tmp), "add multiply")
        self.assertEqual(target.module, "src/app.py")
        self.assertEqual(target.test, "tests/test_app.py")
        self.assertEqual(target.scope, "src")
        self.assertEqual(target.symbol, "multiply")

    def test_located_path_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(tmp)
            (project / "src" / "other.py").write_text(MODULE * 4, encoding="utf-8")
            target = pick_target(project, "add multiply", located_path="src/app.py")
        self.assertEqual(target.module, "src/app.py")

    def test_test_file_is_never_the_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = pick_target(_project(tmp), "add x", located_path="tests/test_app.py")
        self.assertEqual(target.module, "src/app.py")

    def test_empty_project_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = pick_target(Path(tmp), "add x")
        self.assertEqual(target.module, FALLBACK_MODULE)


class RetargetTest(unittest.TestCase):
    def test_fixture_path_is_repointed(self) -> None:
        target = Target("src/app.py", "tests/test_app.py", "src", "multiply")
        with tempfile.TemporaryDirectory() as tmp:
            out = retarget("Action: patch\nPath: pkg/mathy.py\n", target, _project(tmp))
        self.assertIn("Path: src/app.py", out)
        self.assertNotIn("pkg/mathy.py", out)

    def test_a_path_that_exists_here_is_left_alone(self) -> None:
        target = Target("src/app.py", "tests/test_app.py", "src", "multiply")
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(tmp)
            (project / "pkg").mkdir()
            (project / "pkg" / "mathy.py").write_text(MODULE, encoding="utf-8")
            out = retarget("Path: pkg/mathy.py\n", target, project)
        self.assertIn("Path: pkg/mathy.py", out)

    def test_a_missing_test_path_goes_to_the_test_file(self) -> None:
        target = Target("src/app.py", "tests/test_app.py", "src", "multiply")
        with tempfile.TemporaryDirectory() as tmp:
            out = retarget("Path: tests/test_mathy.py\n", target, _project(tmp))
        self.assertIn("Path: tests/test_app.py", out)

    def test_new_package_init_is_left_alone(self) -> None:
        target = Target("src/app.py", "tests/test_app.py", "src", "multiply")
        with tempfile.TemporaryDirectory() as tmp:
            out = retarget("Path: pkg/__init__.py\n", target, _project(tmp))
        self.assertIn("Path: pkg/__init__.py", out)

    def test_placeholders_are_filled(self) -> None:
        target = Target("src/app.py", "tests/test_app.py", "src", "multiply")
        out = retarget("Path: {{module}}\nScope: {{scope}}\nQuery: {{symbol}}\n", target)
        self.assertIn("Path: src/app.py", out)
        self.assertIn("Scope: src", out)
        self.assertIn("Query: multiply", out)

    def test_symbol_token_is_filled(self) -> None:
        target = Target("src/app.py", "tests/test_app.py", "src", "multiply")
        out = retarget("Query: the_symbol_from_the_task\n", target)
        self.assertIn("Query: multiply", out)


class KitSkillTest(unittest.TestCase):
    def test_no_kit_skill_sends_a_fixture_path_into_a_real_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(tmp)
            target = pick_target(project, "add a function multiply(a, b) and a unit test")
            for name in ("add-feature", "write-tests", "fix-smell"):
                skill = get_skill(name)
                self.assertIsNotNone(skill, name)
                rendered = render_skill(skill, target, project)
                for line in rendered.splitlines():
                    if line.startswith(("Path:", "File:")):
                        rel = line.split(":", 1)[1].strip()
                        self.assertTrue(
                            (project / rel).is_file(),
                            f"{name} points at {rel}, which is not in this project",
                        )


if __name__ == "__main__":
    unittest.main()
