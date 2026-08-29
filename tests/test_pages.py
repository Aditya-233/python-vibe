import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

_BANNED_PRODUCTS = re.compile(r"\b(Cursor|ChatGPT|Claude|Grok)\b")


class PagesInvestigationsTest(unittest.TestCase):
    def test_site_files_exist(self) -> None:
        required = (
            "_config.yml",
            "_layouts/default.html",
            "_includes/site.css",
            "_includes/nav.html",
            "index.md",
            "start.md",
            "api.md",
            "architecture.md",
            "local-editor.md",
            "research-vibe-review.md",
            "investigations/index.md",
            "investigations/everyday-laptop.md",
            "investigations/everyday-skills.md",
            "investigations/harness-comparison.md",
            "investigations/local-vs-cloud.md",
            "investigations/what-to-improve.md",
        )
        missing = [name for name in required if not (DOCS / name).is_file()]
        self.assertEqual(missing, [])

    def test_seo_and_llm_discovery_files_exist(self) -> None:
        required = (
            "robots.md",
            "sitemap.md",
            "llms.md",
            "llms-full.md",
            "_includes/head-seo.html",
            "_includes/schema.html",
        )
        missing = [name for name in required if not (DOCS / name).is_file()]
        self.assertEqual(missing, [])
        llms = (DOCS / "llms.md").read_text(encoding="utf-8")
        self.assertIn("# python-vibe", llms)
        self.assertIn("permalink: /llms.txt", llms)
        self.assertIn("> ", llms)
        full = (DOCS / "llms-full.md").read_text(encoding="utf-8")
        self.assertIn("permalink: /llms-full.txt", full)
        self.assertIn("Do not call the project everyday-ready", full)
        robots = (DOCS / "robots.md").read_text(encoding="utf-8")
        self.assertIn("Allow: /", robots)
        self.assertIn("Sitemap:", robots)
        sitemap = (DOCS / "sitemap.md").read_text(encoding="utf-8")
        self.assertIn("urlset", sitemap)
        self.assertIn("/llms.txt", sitemap)
        layout = (DOCS / "_layouts" / "default.html").read_text(encoding="utf-8")
        self.assertIn("head-seo.html", layout)
        seo = (DOCS / "_includes" / "head-seo.html").read_text(encoding="utf-8")
        self.assertIn('rel="canonical"', seo)
        self.assertIn('rel="describedby"', seo)
        self.assertIn('type="text/markdown"', seo)
        self.assertIn("application/ld+json", (DOCS / "_includes" / "schema.html").read_text(encoding="utf-8"))
        self.assertIn("SoftwareSourceCode", (DOCS / "_includes" / "schema.html").read_text(encoding="utf-8"))
        self.assertIn("robots: noindex", (DOCS / "404.md").read_text(encoding="utf-8"))

    def test_layout_inlines_css_and_is_keyboard_usable(self) -> None:
        layout = (DOCS / "_layouts" / "default.html").read_text(encoding="utf-8")
        css = (DOCS / "_includes" / "site.css").read_text(encoding="utf-8")
        self.assertIn("{% include site.css %}", layout)
        self.assertNotIn('rel="stylesheet"', layout)
        self.assertIn('href="#main"', layout)
        self.assertIn('id="main"', layout)
        self.assertIn("aria-current", (DOCS / "_includes" / "nav.html").read_text(encoding="utf-8"))
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("prefers-color-scheme: dark", css)
        self.assertIn("color-scheme: light dark", css)
        self.assertLess(len(css.encode("utf-8")), 9000)

    def test_no_personal_devbox_paths_in_pages(self) -> None:
        hits: list[str] = []
        for path in DOCS.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".html", ".css", ".yml"}:
                continue
            text = path.read_text(encoding="utf-8")
            if "/Users/" in text or "DevBox/" in text:
                hits.append(str(path.relative_to(ROOT)))
        self.assertEqual(hits, [])

    def test_public_copy_does_not_name_other_editors(self) -> None:
        hits: list[str] = []
        for path in DOCS.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".html", ".css"}:
                continue
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if _BANNED_PRODUCTS.search(line):
                    hits.append(f"{path.relative_to(ROOT)}:{i}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
