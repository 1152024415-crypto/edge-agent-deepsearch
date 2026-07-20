#!/usr/bin/env python3
"""waic_page template renders the WAIC insight page shell."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.waic_page import WAIC_HTML


class WaicPageTest(unittest.TestCase):
    def test_template_has_key_markers(self):
        self.assertIn("<!doctype html>", WAIC_HTML)
        self.assertIn("marked.min.js", WAIC_HTML)
        self.assertIn("katex", WAIC_HTML.lower())
        self.assertIn("WAIC-insight.md", WAIC_HTML)
        self.assertIn('id="toc"', WAIC_HTML)
        self.assertIn('id="art"', WAIC_HTML)
        self.assertIn("index.html", WAIC_HTML)

    def test_template_has_toc_autobuild_js(self):
        self.assertIn("querySelectorAll('h2')", WAIC_HTML)
        self.assertIn("IntersectionObserver", WAIC_HTML)


if __name__ == "__main__":
    unittest.main()
