"""Platform-engineering path helpers. Small files, every OS."""

import tempfile
import unittest
from pathlib import Path

from harness.act.code import resolve_project_file
from harness.act.tools import edit_py, glob_py
from harness.paths import is_windows, venv_python
from harness.skillkit.catalog import list_skills, pick_skills
from harness.skillkit.style import refuse_platform_draft
from harness.task import everyday_example_path, looks_like_platform

ROOT = Path(__file__).resolve().parents[1]

SAFE = """
import os
from pathlib import Path


def interpreter_in_venv(venv: Path, *, windows: bool | None = None) -> Path:
    on_windows = os.name == "nt" if windows is None else windows
    if on_windows:
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"
"""


class PlatformTaskTest(unittest.TestCase):
    def test_pathlib_and_venv_tasks_are_platform(self) -> None:
        self.assertTrue(looks_like_platform("write a pathlib path helper"))
        self.assertTrue(looks_like_platform("cross-platform venv python path"))
        self.assertFalse(looks_like_platform("what is pathlib?"))
        self.assertFalse(looks_like_platform("implement binary search"))

    def test_skill_and_path_match(self) -> None:
        catalog = list_skills(ROOT)
        task = "write a pathlib helper for windows and posix venv"
        self.assertEqual(
            [item.name for item in pick_skills(task, catalog)],
            ["write-paths", "write-tests"],
        )
        self.assertEqual(everyday_example_path(task), "pkg/paths.py")


class PlatformRefuseTest(unittest.TestCase):
    def test_os_path_join_is_refused(self) -> None:
        blocked = refuse_platform_draft(
            "pkg/paths.py", "import os\np = os.path.join('a', 'b')\n"
        )
        self.assertIn("pathlib", blocked)

    def test_hardcoded_home_is_refused(self) -> None:
        blocked = refuse_platform_draft("pkg/paths.py", 'home = "/Users/jenya"\n')
        self.assertIn("Path.home", blocked)

    def test_hardcoded_tmp_is_refused(self) -> None:
        blocked = refuse_platform_draft("pkg/paths.py", 'p = "/tmp/work"\n')
        self.assertIn("tempfile", blocked)

    def test_posix_only_venv_is_refused(self) -> None:
        blocked = refuse_platform_draft(
            "pkg/paths.py", 'return venv / "bin/python"\n'
        )
        self.assertIn("Scripts", blocked)

    def test_open_without_encoding_is_refused(self) -> None:
        blocked = refuse_platform_draft(
            "pkg/paths.py", "text = open(path).read()\n"
        )
        self.assertIn("encoding", blocked)

    def test_safe_pathlib_is_allowed(self) -> None:
        self.assertEqual(refuse_platform_draft("pkg/paths.py", SAFE), "")

    def test_test_files_may_quote_os_path(self) -> None:
        self.assertEqual(
            refuse_platform_draft(
                "tests/test_paths.py", "os.path.join is refused\n"
            ),
            "",
        )


class PlatformJailTest(unittest.TestCase):
    def test_toml_is_in_the_jail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
            path = resolve_project_file(root, "pyproject.toml")
            self.assertEqual(path.name, "pyproject.toml")

    def test_credentials_json_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "credentials.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError) as caught:
                resolve_project_file(root, "credentials.json")
            self.assertIn("secret", str(caught.exception))

    def test_glob_skips_secret_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
            (root / "credentials.json").write_text("{}", encoding="utf-8")
            listed = glob_py(root, "*")
            self.assertIn("pyproject.toml", listed)
            self.assertNotIn("credentials.json", listed)

    def test_edit_refuses_os_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pkg").mkdir()
            (root / "pkg" / "paths.py").write_text("x = 1\n", encoding="utf-8")
            result = edit_py(
                root,
                "pkg/paths.py",
                "import os\n\ndef join(a, b):\n    return os.path.join(a, b)\n",
                task="write a pathlib path helper",
            )
            self.assertIn("pathlib", result)
            self.assertEqual((root / "pkg" / "paths.py").read_text(encoding="utf-8"), "x = 1\n")


class VenvLayoutTest(unittest.TestCase):
    def test_both_layouts_are_named(self) -> None:
        venv = Path("/opt/venv")
        self.assertEqual(
            venv_python(venv, windows=False).as_posix(),
            "/opt/venv/bin/python",
        )
        self.assertEqual(
            venv_python(venv, windows=True).as_posix(),
            "/opt/venv/Scripts/python.exe",
        )
        self.assertTrue(is_windows(windows=True))
        self.assertFalse(is_windows(windows=False))


if __name__ == "__main__":
    unittest.main()
