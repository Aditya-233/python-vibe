import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class PagesInvestigationsTest(unittest.TestCase):
    def test_site_files_exist(self) -> None:
        required = (
            "local-editor.md",
            "investigations/everyday-laptop.md",
            "research-vibe-review.md",
        )
        missing = [name for name in required if not (DOCS / name).is_file()]
        self.assertEqual(missing, [])

    def test_no_personal_devbox_paths_in_pages(self) -> None:
        hits: list[str] = []
        for path in DOCS.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            if "/Users/yauhenbichel" in text or "DevBox/tracer-cloud" in text:
                hits.append(str(path.relative_to(ROOT)))
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
