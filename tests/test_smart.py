import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from harness.locate import (
    def_hit_path,
    locate_py,
    prelude,
    refuse_early_done,
    refuse_question_write,
    refuse_redundant_explore,
    refuse_redundant_locate,
    refuse_shallow_done,
    return_annotation,
    signature_line,
)


class SmartHarnessTest(unittest.TestCase):
    def test_def_hit_prefers_definition(self) -> None:
        grep = (
            "src/a.py:1:from harness.act.code import apply_source\n"
            "src/harness/code.py:84:def apply_source(path, source, *, original):\n"
        )
        self.assertEqual(def_hit_path(grep, "apply_source"), "src/harness/code.py")

    def test_locate_reads_defining_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "pkg"
            src.mkdir()
            (src / "code.py").write_text(
                "def apply_source(path, source, *, original):\n"
                "    if not source.strip():\n"
                "        raise ValueError('empty draft')\n",
                encoding="utf-8",
            )
            (src / "other.py").write_text(
                "from pkg.code import apply_source\n",
                encoding="utf-8",
            )
            text, path = locate_py(root, "apply_source")
            self.assertEqual(path, "pkg/code.py")
            self.assertIn("empty draft", text)
            self.assertIn("# auto-read", text)

    def test_prelude_question_and_add(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "pkg"
            pkg.mkdir()
            (pkg / "mathy.py").write_text(
                "def compute_total(rows) -> int:\n    return sum(rows)\n",
                encoding="utf-8",
            )
            q_text, q_path = prelude(root, "what does compute_total return?")
            self.assertIn("auto-read", q_text)
            self.assertEqual(q_path, "pkg/mathy.py")
            self.assertIn("-> type", q_text)
            add_text, _add_path = prelude(
                root, "add a function multiply(a, b) and a unit test"
            )
            self.assertIn("(no hits)", add_text)

    def test_refuse_early_done(self) -> None:
        self.assertIn("locate", refuse_early_done("what does apply_source refuse?", "", ""))
        self.assertEqual(
            refuse_early_done(
                "what does apply_source refuse?",
                "src/harness/code.py",
                "src/harness/code.py",
            ),
            "",
        )

    def test_refuse_question_write_and_reread(self) -> None:
        self.assertIn(
            "do not edit",
            refuse_question_write("what does complete do?", "patch").lower(),
        )
        self.assertEqual(refuse_question_write("add a function multiply", "patch"), "")
        self.assertIn(
            "auto-read",
            refuse_redundant_explore(
                "what does listen_addr return?",
                "read",
                "src/harness/http.py",
                "src/harness/http.py",
            ),
        )
        self.assertEqual(
            refuse_redundant_explore(
                "what does listen_addr return?",
                "read",
                "src/harness/run.py",
                "src/harness/http.py",
            ),
            "",
        )

    def test_signature_and_shallow_done(self) -> None:
        grep = (
            "src/harness/http.py:18:"
            "def listen_addr(argv: list[str] | None = None) -> tuple[str, int]:"
        )
        sig = signature_line(grep, "listen_addr")
        self.assertIn("def listen_addr(", sig)
        self.assertEqual(return_annotation(sig), "tuple[str, int]")
        self.assertIn(
            "tuple[str, int]",
            refuse_shallow_done(
                "what does listen_addr return?",
                "a tuple containing the host and port",
                sig,
            ),
        )
        self.assertEqual(
            refuse_shallow_done(
                "what does listen_addr return?",
                "returns tuple[str, int] from env or argv",
                sig,
            ),
            "",
        )
        self.assertEqual(
            refuse_shallow_done("add a function multiply", "done", sig),
            "",
        )
        self.assertIn(
            "patch",
            refuse_redundant_locate(
                "add a function multiply(a, b) and a unit test", "locate", True
            ),
        )
        self.assertEqual(
            refuse_redundant_locate(
                "add a function multiply(a, b) and a unit test", "locate", False
            ),
            "",
        )


if __name__ == "__main__":
    unittest.main()
