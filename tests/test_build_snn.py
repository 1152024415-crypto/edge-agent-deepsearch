#!/usr/bin/env python3
"""build_snn renders site/snn.html + copies site/snn/SNN-insight.md."""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BuildSnnTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.site = Path(self._tmp.name)
        self.src = Path(self._tmp.name) / "SNN-insight.md"

    def _load(self, src_md_text):
        self.src.write_text(src_md_text, encoding="utf-8")
        os.environ["SNN_SRC"] = str(self.src)
        os.environ["SNN_SITE"] = str(self.site)
        spec = importlib.util.spec_from_file_location("build_snn", ROOT / "agent" / "build_snn.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_build_writes_html_and_md(self):
        mod = self._load("# title\n## 1. A\nbody\n")
        self.assertEqual(mod.main(), 0)
        self.assertTrue((self.site / "snn.html").exists())
        self.assertTrue((self.site / "snn" / "SNN-insight.md").exists())
        html = (self.site / "snn.html").read_text(encoding="utf-8")
        self.assertIn("SNN-insight.md", html)
        self.assertIn('id="art"', html)
        md = (self.site / "snn" / "SNN-insight.md").read_text(encoding="utf-8")
        self.assertIn("## 1. A", md)

    def test_build_returns_1_when_src_missing(self):
        os.environ["SNN_SRC"] = str(self.site / "nope.md")
        os.environ["SNN_SITE"] = str(self.site)
        spec = importlib.util.spec_from_file_location("build_snn", ROOT / "agent" / "build_snn.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.main(), 1)


if __name__ == "__main__":
    unittest.main()
