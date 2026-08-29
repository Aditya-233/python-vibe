import tempfile
import unittest
from pathlib import Path

from harness.scan.layout import (
    find_cycles,
    find_flat_packages,
    find_god_modules,
    has_tests,
    render_layout,
    review_layout,
)

HARNESS = Path(__file__).resolve().parents[1] / "src" / "harness"


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class CycleTest(unittest.TestCase):
    def test_two_modules_importing_each_other(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "alpha.py", "from beta import go\n")
            _write(root, "beta.py", "from alpha import back\n")
            self.assertEqual(find_cycles(root), [("alpha", "beta")])

    def test_one_way_import_is_not_a_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "alpha.py", "from beta import go\n")
            _write(root, "beta.py", "x = 1\n")
            self.assertEqual(find_cycles(root), [])

    def test_third_party_import_is_not_a_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "alpha.py", "from unittest import TestCase\n")
            self.assertEqual(find_cycles(root), [])

    def test_unparsable_module_is_not_a_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "alpha.py", "def broken(\n")
            self.assertEqual(find_cycles(root), [])

    def test_the_harness_itself_has_no_cycles(self) -> None:
        self.assertEqual(find_cycles(HARNESS), [])


class FlatAndGodTest(unittest.TestCase):
    def test_flat_package_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(15):
                _write(root, f"pkg/m{i}.py", "x = 1\n")
            flat = find_flat_packages(root)
        self.assertEqual(flat, [("pkg", 15)])

    def test_grouped_package_is_not_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for group in ("a", "b", "c"):
                for i in range(5):
                    _write(root, f"pkg/{group}/m{i}.py", "x = 1\n")
            self.assertEqual(find_flat_packages(root), [])

    def test_god_module_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(6):
                _write(root, f"m{i}.py", "x = 1\n")
            _write(root, "huge.py", "# pad\n" * 3000)
            god = find_god_modules(root)
        self.assertEqual([rel for rel, _size in god], ["huge.py"])

    def test_even_sizes_have_no_god_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(6):
                _write(root, f"m{i}.py", "# pad\n" * 2000)
            self.assertEqual(find_god_modules(root), [])


class ReviewTest(unittest.TestCase):
    def test_missing_tests_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "app.py", "x = 1\n")
            self.assertFalse(has_tests(root))
            self.assertIn("no-tests", [f.kind for f in review_layout(root)])

    def test_tests_present_clears_that_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "app.py", "x = 1\n")
            _write(root, "tests/test_app.py", "x = 1\n")
            self.assertTrue(has_tests(root))
            self.assertNotIn("no-tests", [f.kind for f in review_layout(root)])

    def test_cycle_outranks_everything_else(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "alpha.py", "from beta import go\n")
            _write(root, "beta.py", "from alpha import back\n")
            self.assertEqual(review_layout(root)[0].kind, "cycle")

    def test_clean_project_says_do_the_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "app.py", "x = 1\n")
            _write(root, "tests/test_app.py", "x = 1\n")
            self.assertIn("do the task", render_layout(root))

    def test_render_names_exactly_one_move(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "alpha.py", "from beta import go\n")
            _write(root, "beta.py", "from alpha import back\n")
            text = render_layout(root)
        self.assertEqual(text.count("Next move"), 1)


if __name__ == "__main__":
    unittest.main()
