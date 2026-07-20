#!/usr/bin/env python3
"""build_waic renders site/waic.html + copies site/waic/WAIC-insight.md."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BuildWaicTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.site = Path(self._tmp.name)
        self.src = Path(self._tmp.name) / "WAIC-insight.md"

    def _load(self, src_md_text):
        self.src.write_text(src_md_text, encoding="utf-8")
        os.environ["WAIC_SRC"] = str(self.src)
        os.environ["WAIC_SITE"] = str(self.site)
        spec = importlib.util.spec_from_file_location("build_waic", ROOT / "agent" / "build_waic.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_build_writes_html_and_md(self):
        mod = self._load("# title\n## 1. A\nbody\n")
        self.assertEqual(mod.main(), 0)
        self.assertTrue((self.site / "waic.html").exists())
        self.assertTrue((self.site / "waic" / "WAIC-insight.md").exists())
        html = (self.site / "waic.html").read_text(encoding="utf-8")
        self.assertIn("WAIC-insight.md", html)
        self.assertIn('id="art"', html)

    def test_build_returns_1_when_src_missing(self):
        os.environ["WAIC_SRC"] = str(self.site / "nope.md")
        os.environ["WAIC_SITE"] = str(self.site)
        spec = importlib.util.spec_from_file_location("build_waic", ROOT / "agent" / "build_waic.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.main(), 1)


if __name__ == "__main__":
    unittest.main()
