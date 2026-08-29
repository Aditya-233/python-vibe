import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from harness.style import (
    looks_like_fix_smell,
    looks_like_new_package,
    refuse_layout,
    refuse_opaque_names,
    refuse_smell_wrong_file,
    rename_target,
    smell_symbol,
)


class StyleHarnessTest(unittest.TestCase):
    def test_task_kinds(self) -> None:
        self.assertTrue(looks_like_new_package("create a package for total_price"))
        self.assertTrue(looks_like_fix_smell("rename calc to total_price"))
        self.assertTrue(looks_like_fix_smell("fix the code smell in calc"))
        self.assertFalse(looks_like_new_package("add a function multiply"))
        self.assertEqual(smell_symbol("rename calc to total_price"), "calc")
        self.assertEqual(smell_symbol("fix the code smell in calc"), "calc")
        self.assertIn(
            "implementation first",
            refuse_smell_wrong_file(
                "rename calc to total_price",
                "patch",
                "tests/test_mathy.py",
                "pkg/mathy.py",
                "def calc(x, y):\n    return x * y\n",
            ),
        )
        self.assertEqual(
            refuse_smell_wrong_file(
                "rename calc to total_price",
                "patch",
                "tests/test_mathy.py",
                "pkg/mathy.py",
                "def total_price(quantity, unit_price):\n    return quantity * unit_price\n",
            ),
            "",
        )
        self.assertEqual(rename_target("rename calc to total_price"), "total_price")

    def test_opaque_and_case(self) -> None:
        self.assertIn("opaque", refuse_opaque_names("def calc(x, y):\n    return x\n"))
        self.assertIn("opaque", refuse_opaque_names("def tmp():\n    return 1\n"))
        self.assertIn(
            "parameter",
            refuse_opaque_names(
                "def total_price(x: int, y: int) -> int:\n    return x * y\n"
            ),
        )
        self.assertIn("snake_case", refuse_opaque_names("def TotalPrice():\n    return 1\n"))
        self.assertIn("PascalCase", refuse_opaque_names("class pricing:\n    pass\n"))
        self.assertEqual(
            refuse_opaque_names(
                "def total_price(quantity: int, unit_price: int) -> int:\n"
                "    return quantity * unit_price\n"
            ),
            "",
        )
        self.assertEqual(refuse_opaque_names("def add(left, right):\n    return left\n"), "")

    def test_layout_soc(self) -> None:
        self.assertIn(
            "__init__",
            refuse_layout(
                "pkg/__init__.py",
                "",
                "def total_price(q, p):\n    return q * p\n",
            ),
        )
        self.assertIn(
            "scripts",
            refuse_layout("scripts/chat.py", "", "def helper():\n    return 1\n"),
        )
        many = "".join(f"def fn_{i}():\n    return {i}\n\n" for i in range(4))
        self.assertIn(
            "already has 4",
            refuse_layout("pkg/mathy.py", many, "def extra():\n    return 1\n"),
        )
        self.assertEqual(
            refuse_layout(
                "pkg/__init__.py",
                "",
                '"""Public exports only."""\n',
            ),
            "",
        )


if __name__ == "__main__":
    unittest.main()
