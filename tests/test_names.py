"""Compiler-style undefined-name oracle. No model."""

import tempfile
import unittest
from pathlib import Path

from harness.act.tools import edit_py, patch_py
from harness.scan.names import new_undefined, undefined_names
from harness.skillkit.style import (
    refuse_done_oracle,
    refuse_rename_incomplete,
    refuse_test_in_impl,
    refuse_undefined_draft,
)


ORDERS = '''TAX_RATE = 0.2

def compute_total(prices: list[int]) -> int:
    return sum(prices)

def total_with_tax(prices: list[int]) -> float:
    subtotal = compute_total(prices)
    return subtotl + (subtotl * TAX_RATE)
'''

FIXED = ORDERS.replace("subtotl", "subtotal")


class UndefinedNamesTest(unittest.TestCase):
    def test_planted_typo_is_found(self) -> None:
        self.assertIn("subtotl", undefined_names(ORDERS))

    def test_fixed_file_is_clean(self) -> None:
        self.assertEqual(undefined_names(FIXED), [])

    def test_adding_a_function_does_not_count_the_old_typo(self) -> None:
        draft = FIXED.replace(
            "return subtotal + (subtotal * TAX_RATE)\n",
            "return subtotal + (subtotal * TAX_RATE)\n\n"
            "def total_lines(prices: list[int]) -> int:\n    return len(prices)\n",
        )
        # original still has the typo; draft is clean — not "new" undefined
        self.assertEqual(new_undefined(ORDERS, draft), [])

    def test_a_new_typo_is_new_undefined(self) -> None:
        draft = FIXED + (
            "\ndef total_lines(prices: list[int]) -> int:\n    return lenght\n"
        )
        self.assertIn("lenght", new_undefined(FIXED, draft))


class StyleOracleTest(unittest.TestCase):
    def test_test_in_impl_is_refused(self) -> None:
        draft = ORDERS + "\ndef test_apply_discount_reduces_the_total(self) -> None:\n    pass\n"
        self.assertIn("tests/", refuse_test_in_impl("src/orders.py", draft))
        self.assertEqual(
            refuse_test_in_impl("tests/test_orders.py", draft),
            "",
        )

    def test_bugfix_cannot_leave_the_typo(self) -> None:
        self.assertIn(
            "subtotl",
            refuse_undefined_draft(
                "find a real NameError in src/orders.py and fix it",
                "src/orders.py",
                ORDERS,
                ORDERS + "\n# note\n",
            ),
        )
        self.assertEqual(
            refuse_undefined_draft(
                "find a real NameError in src/orders.py and fix it",
                "src/orders.py",
                ORDERS,
                FIXED,
            ),
            "",
        )

    def test_rename_must_change_the_def(self) -> None:
        body = "def calc(left: int, right: int) -> int:\n    return left * right\n"
        self.assertIn(
            "still defines calc",
            refuse_rename_incomplete("rename calc to multiply", "src/util.py", body),
        )
        self.assertEqual(
            refuse_rename_incomplete(
                "rename calc to multiply",
                "src/util.py",
                body.replace("calc", "multiply"),
            ),
            "",
        )

    def test_done_oracle_sees_the_named_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src"
            src.mkdir()
            (src / "orders.py").write_text(ORDERS, encoding="utf-8")
            self.assertIn(
                "subtotl",
                refuse_done_oracle(
                    "find a real NameError in src/orders.py and fix it",
                    root,
                    "src/orders.py",
                ),
            )
            (src / "orders.py").write_text(FIXED, encoding="utf-8")
            self.assertEqual(
                refuse_done_oracle(
                    "find a real NameError in src/orders.py and fix it",
                    root,
                    "src/orders.py",
                ),
                "",
            )

    def test_write_tests_done_requires_the_named_function(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "src" / "orders.py").write_text(FIXED, encoding="utf-8")
            (root / "tests" / "test_orders.py").write_text(
                "def test_compute_total_sums_the_prices(self) -> None:\n    pass\n",
                encoding="utf-8",
            )
            task = "write tests for apply_discount in src/orders.py"
            self.assertIn(
                "apply_discount",
                refuse_done_oracle(task, root, "src/orders.py"),
            )
            (root / "tests" / "test_orders.py").write_text(
                "def test_apply_discount_reduces_the_total(self) -> None:\n"
                "    got = apply_discount(10, 0.2)\n",
                encoding="utf-8",
            )
            self.assertEqual(refuse_done_oracle(task, root, "src/orders.py"), "")

    def test_patch_refuses_a_test_in_the_impl_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "src" / "orders.py"
            path.parent.mkdir()
            path.write_text(FIXED, encoding="utf-8")
            blocked = patch_py(
                root,
                "src/orders.py",
                "",
                "",
                append="    def test_apply_discount_reduces_the_total(self) -> None:\n        pass\n",
                task="write tests for apply_discount in src/orders.py",
            )
        self.assertIn("tests/", blocked)


if __name__ == "__main__":
    unittest.main()
