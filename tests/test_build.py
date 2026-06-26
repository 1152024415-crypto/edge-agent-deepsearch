#!/usr/bin/env python3
"""Build output smoke tests for the static fallback site."""

import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BuildOutputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env = {**os.environ, "EDGE_AGENT_TODAY": "2026-06-25"}
        subprocess.run([sys.executable, str(ROOT / "app" / "build.py")], cwd=ROOT, env=env, check=True)
        cls.html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")

    def test_required_paper_fields_are_rendered(self):
        for label in ("论文标题", "论文摘要", "论文效果", "工作原理", "论文连接", "洞察人", "wiki连接"):
            with self.subTest(label=label):
                self.assertIn(label, self.html)

    def test_high_density_table_controls_are_rendered(self):
        for marker in (
            'class="paper-table"',
            'data-sort="score"',
            'data-sort="date"',
            "localStorage",
            "/api/insights",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.html)

    def test_stale_or_non_paper_samples_are_not_rendered(self):
        self.assertIn("暂无可展示论文", self.html)
        for title in ("AgentCPM-GUI", "Apple Core AI", "Qualcomm"):
            with self.subTest(title=title):
                self.assertNotIn(title, self.html)


if __name__ == "__main__":
    unittest.main()
