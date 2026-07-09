#!/usr/bin/env python3
"""Unit tests for app.weeks (week archive / manifest / parse logic)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import weeks


class ParseWeekMetaTest(unittest.TestCase):
    def test_parses_range_from_overview(self):
        ov = "本周端侧 AI 技术动态(06-26~07-03)：edge AI 板卡/整机..."
        m = weeks.parse_week_meta(ov, "2026-07-09")
        self.assertEqual(m["label"], "2026-06-26")
        self.assertEqual(m["title"], "06-26~07-03")
        self.assertEqual(m["range"]["start"], "2026-06-26")
        self.assertEqual(m["range"]["end"], "2026-07-03")

    def test_uses_fallback_year(self):
        # 2025 年的 overview 也用 fallback 年份
        ov = "本周动态(12-26~01-02)：..."
        m = weeks.parse_week_meta(ov, "2026-01-05")
        self.assertEqual(m["label"], "2026-12-26")
        self.assertEqual(m["range"]["end"], "2026-01-02")

    def test_no_range_falls_back_to_date(self):
        ov = "本周动态：无日期范围"
        m = weeks.parse_week_meta(ov, "2026-07-09")
        self.assertEqual(m["label"], "2026-07-09")
        self.assertEqual(m["title"], "2026-07-09")
        self.assertEqual(m["range"]["start"], "2026-07-09")
        self.assertEqual(m["range"]["end"], "2026-07-09")


if __name__ == "__main__":
    unittest.main()
