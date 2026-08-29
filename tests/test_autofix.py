"""Mechanical rename and NameError typo fixes. No model."""

import tempfile
import unittest
from pathlib import Path

from harness.act.autofix import (
    apply_function_rename,
    apply_mechanical,
    apply_typo_fixes,
    levenshtein,
    typo_pairs,
)
from harness.agent.prompt import build_preamble
from harness.agent.options import AgentOptions

ORDERS = '''TAX_RATE = 0.2

def compute_total(prices: list[int]) -> int:
    return sum(prices)

def total_with_tax(prices: list[int]) -> float:
    subtotal = compute_total(prices)
    return subtotl + (subtotl * TAX_RATE)
'''

UTIL = """def calc(x: int, y: int) -> int:
    return x * y
"""


class TypoFixTest(unittest.TestCase):
    def test_subtotl_is_one_edit_from_subtotal(self) -> None:
        self.assertEqual(levenshtein("subtotl", "subtotal"), 1)
        self.assertEqual(typo_pairs(ORDERS), [("subtotl", "subtotal")])

    def test_the_typo_is_rewritten(self) -> None:
        fixed = apply_typo_fixes(ORDERS)
        self.assertNotIn("subtotl", fixed)
        self.assertIn("return subtotal + (subtotal * TAX_RATE)", fixed)
        self.assertIn("subtotal = compute_total", fixed)

    def test_two_equally_close_names_are_left_alone(self) -> None:
        source = (
            "def pick(prices: list[int]) -> int:\n"
            "    foo_bar = 1\n"
            "    foo_baz = 2\n"
            "    return foo_bat\n"
        )
        self.assertEqual(apply_typo_fixes(source), source)


class RenameFixTest(unittest.TestCase):
    def test_the_def_line_keeps_its_types(self) -> None:
        out = apply_function_rename(UTIL, "calc", "multiply")
        self.assertIn("def multiply(x: int, y: int) -> int:", out)
        self.assertNotIn("def calc", out)

    def test_calls_in_the_same_file_are_renamed(self) -> None:
        source = UTIL + "\n\ndef twice() -> int:\n    return calc(2, 2)\n"
        out = apply_function_rename(source, "calc", "multiply")
        self.assertIn("return multiply(2, 2)", out)


class MechanicalPreludeTest(unittest.TestCase):
    def test_bugfix_is_applied_before_the_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "src" / "orders.py").write_text(ORDERS, encoding="utf-8")
            (root / "tests" / "test_orders.py").write_text("x = 1\n", encoding="utf-8")
            note = apply_mechanical(
                root,
                "find a real NameError in src/orders.py and fix it",
                "src/orders.py",
            )
            body = (root / "src" / "orders.py").read_text(encoding="utf-8")
        self.assertIn("subtotl → subtotal", note)
        self.assertNotIn("subtotl", body)
        self.assertIn("subtotal = compute_total", body)

    def test_rename_is_applied_before_the_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "util.py").write_text(UTIL, encoding="utf-8")
            note = apply_mechanical(
                root,
                "rename calc to multiply in src/util.py",
                "src/util.py",
            )
            body = (root / "src" / "util.py").read_text(encoding="utf-8")
        self.assertIn("def calc → def multiply", note)
        self.assertIn("def multiply(x: int, y: int) -> int:", body)

    def test_preamble_records_the_autofix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "orders.py").write_text(ORDERS, encoding="utf-8")
            pre = build_preamble(
                AgentOptions(
                    project=root,
                    task="find a real NameError in src/orders.py and fix it",
                )
            )
        self.assertIn("mechanical fix", pre.autofix)
        self.assertIn("subtotl", pre.autofix)


if __name__ == "__main__":
    unittest.main()


class OnlyCodeIsRewrittenTest(unittest.TestCase):
    """A mechanical fix must not edit words the person wrote.

    The typo fix runs during a bug fix, where an error message may well
    mention the misspelling on purpose. Rewriting it would change the
    program's output without being asked.
    """

    SOURCE = (
        "def total(prices: list[int]) -> int:\n"
        "    subtotal = sum(prices)\n"
        "    if not prices:\n"
        '        raise ValueError("subtotl must be set")  # note: subtotl\n'
        "    return subtotl\n"
    )

    def test_the_code_is_fixed(self) -> None:
        got = apply_typo_fixes(self.SOURCE)
        self.assertIn("return subtotal", got)

    def test_a_string_keeps_the_word(self) -> None:
        got = apply_typo_fixes(self.SOURCE)
        self.assertIn('"subtotl must be set"', got)

    def test_a_comment_keeps_the_word(self) -> None:
        got = apply_typo_fixes(self.SOURCE)
        self.assertIn("# note: subtotl", got)

    def test_the_result_is_still_valid_python(self) -> None:
        import ast

        ast.parse(apply_typo_fixes(self.SOURCE))

    def test_unparsable_source_is_returned_unchanged(self) -> None:
        broken = "def f(\n"
        self.assertEqual(apply_typo_fixes(broken), broken)


class RenameScopeTest(unittest.TestCase):
    """The rename needs a call shape, so prose is left alone."""

    SOURCE = (
        "def calc(x: int, y: int) -> int:\n"
        '    """Return calc of x and y."""\n'
        "    return x * y\n"
    )

    def test_the_definition_is_renamed(self) -> None:
        got = apply_function_rename(self.SOURCE, "calc", "multiply")
        self.assertIn("def multiply(x: int, y: int) -> int:", got)

    def test_prose_mentioning_the_name_is_left_alone(self) -> None:
        got = apply_function_rename(self.SOURCE, "calc", "multiply")
        self.assertIn("Return calc of x and y.", got)

    def test_nothing_happens_when_the_new_name_already_exists(self) -> None:
        source = self.SOURCE + "\n\ndef multiply(a, b):\n    return a * b\n"
        self.assertEqual(apply_function_rename(source, "calc", "multiply"), source)

    def test_nothing_happens_when_the_old_name_is_absent(self) -> None:
        self.assertEqual(apply_function_rename(self.SOURCE, "nope", "x"), self.SOURCE)
