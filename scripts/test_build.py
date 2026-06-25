#!/usr/bin/env python3
"""Build output smoke tests for the static GitHub Pages view."""
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BuildOutputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], cwd=ROOT, check=True)
        cls.html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")

    def test_required_paper_fields_are_rendered(self):
        for label in ("论文标题", "论文摘要", "论文效果", "工作原理", "论文连接", "洞察人", "wiki连接"):
            with self.subTest(label=label):
                self.assertIn(label, self.html)

    def test_current_posts_are_rendered(self):
        for title in ("AgentCPM-GUI", "Apple Core AI", "Qualcomm"):
            with self.subTest(title=title):
                self.assertIn(title, self.html)


if __name__ == "__main__":
    unittest.main()
