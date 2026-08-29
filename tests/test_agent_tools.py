import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from harness.agent_tools import edit_py, grep_py, map_py, patch_py, read_py, run_python
from harness.code import resolve_project_file


class AgentToolsTest(unittest.TestCase):
    def test_resolve_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ok.py").write_text("print(1)\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                resolve_project_file(root, "../secret.py")

    def test_read_stays_inside_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ok.py").write_text("print(1)\n", encoding="utf-8")
            self.assertIn("print(1)", read_py(root, "ok.py"))

    def test_edit_keeps_bak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "ok.py"
            original = "\n".join(f"value_{i} = {i}" for i in range(20)) + "\n"
            dest.write_text(original, encoding="utf-8")
            rewrite = "\n".join(f"value_{i} = {i + 1}" for i in range(20)) + "\n"
            edit_py(root, "ok.py", rewrite)
            self.assertIn("value_0 = 1", dest.read_text(encoding="utf-8"))
            self.assertTrue(dest.with_suffix(".py.bak").is_file())

    def test_patch_append_adds_function(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "ok.py"
            dest.write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
            out = patch_py(
                root,
                "ok.py",
                "",
                "",
                append="def multiply(a: int, b: int) -> int:\n    return a * b\n",
            )
            self.assertIn("patched", out)
            text = dest.read_text(encoding="utf-8")
            self.assertIn("def add", text)
            self.assertIn("def multiply", text)

    def test_patch_one_occurrence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "ok.py"
            body = "\n".join(f"value_{i} = {i}" for i in range(20)) + "\nreturn tota\n"
            dest.write_text(body, encoding="utf-8")
            out = patch_py(root, "ok.py", "return tota", "return sum(cleaned)")
            self.assertIn("patched", out)
            self.assertIn("return sum(cleaned)", dest.read_text(encoding="utf-8"))

    def test_patch_rejects_short_find(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "ok.py"
            dest.write_text("\n".join(f"value_{i} = {i}" for i in range(20)) + "\n", encoding="utf-8")
            out = patch_py(root, "ok.py", "tota", "sum(x)")
            self.assertIn("8 characters", out)

    def test_grep_finds_markdown_and_respects_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "a.py").write_text("def apply_source():\n    pass\n", encoding="utf-8")
            (root / "README.md").write_text("apply_source creates parent dirs\n", encoding="utf-8")
            hits = grep_py(root, "apply_source")
            self.assertIn("README.md", hits)
            self.assertIn("src/a.py", hits)
            scoped = grep_py(root, "apply_source", scope="src")
            self.assertIn("src/a.py", scoped)
            self.assertNotIn("README.md", scoped)

    def test_map_lists_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ok.py").write_text("print(1)\n", encoding="utf-8")
            out = map_py(root)
            self.assertIn("ok.py", out)

    def test_run_refuses_dash_c(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = run_python(Path(tmp), ("-c", "print(1)"))
        self.assertIn("refusing", out)


if __name__ == "__main__":
    unittest.main()
