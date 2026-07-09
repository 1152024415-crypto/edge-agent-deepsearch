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


import tempfile


class ArchiveManifestTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._orig = weeks.WEEKS_DIR
        weeks.WEEKS_DIR = Path(self._tmp.name)
        self.addCleanup(self._restore)

    def _restore(self):
        weeks.WEEKS_DIR = self._orig

    def _meta(self, label, title=None, start=None, end=None):
        return {"label": label, "title": title or label,
                "range": {"start": start or label, "end": end or label}}

    def test_write_then_read_archive(self):
        meta = self._meta("2026-06-26", "06-26~07-03", "2026-06-26", "2026-07-03")
        weeks.write_archive(meta, [{"id": "p1"}], {"overview": "ov"}, {"items": []})
        self.assertEqual(weeks.archive_path("2026-06-26"), Path(self._tmp.name) / "2026-06-26.json")
        a = weeks.read_archive("2026-06-26")
        self.assertEqual(a["label"], "2026-06-26")
        self.assertEqual(a["papers"], [{"id": "p1"}])
        self.assertEqual(a["weekly"], {"overview": "ov"})
        self.assertEqual(a["trending"], {"items": []})

    def test_read_missing_returns_none(self):
        self.assertIsNone(weeks.read_archive("nope"))

    def test_build_manifest_sorts_desc_and_marks_current(self):
        weeks.write_archive(self._meta("2026-06-26", "06-26~07-03", "2026-06-26", "2026-07-03"), [], {}, {})
        weeks.write_archive(self._meta("2026-07-02", "07-02~07-09", "2026-07-02", "2026-07-09"), [], {}, {})
        m = weeks.build_manifest("2026-07-02")
        self.assertEqual(m[0]["label"], "2026-07-02")
        self.assertTrue(m[0]["current"])
        self.assertFalse(m[1]["current"])
        self.assertEqual(m[1]["label"], "2026-06-26")
        # manifest persisted
        self.assertEqual(weeks.read_manifest(), m)

    def test_read_manifest_missing_returns_empty(self):
        weeks.WEEKS_DIR = Path(self._tmp.name) / "nope"  # 不存在的目录
        self.assertEqual(weeks.read_manifest(), [])

    def test_attach_hrefs_static_root(self):
        manifest = [
            {"label": "2026-07-02", "title": "07-02~07-09", "range": {"start": "2026-07-02", "end": "2026-07-09"}, "current": True},
            {"label": "2026-06-26", "title": "06-26~07-03", "range": {"start": "2026-06-26", "end": "2026-07-03"}, "current": False},
        ]
        out = weeks.attach_hrefs(manifest, weeks_base="", runtime=False)
        self.assertEqual(out[0]["href"], "index.html")
        self.assertEqual(out[1]["href"], "week/2026-06-26.html")

    def test_attach_hrefs_static_subdir(self):
        manifest = [{"label": "2026-07-02", "current": True}, {"label": "2026-06-26", "current": False}]
        out = weeks.attach_hrefs(manifest, weeks_base="../", runtime=False)
        self.assertEqual(out[0]["href"], "../index.html")
        self.assertEqual(out[1]["href"], "../week/2026-06-26.html")

    def test_attach_hrefs_runtime(self):
        manifest = [{"label": "2026-07-02", "current": True}, {"label": "2026-06-26", "current": False}]
        out = weeks.attach_hrefs(manifest, weeks_base="", runtime=True)
        self.assertEqual(out[0]["href"], "/")
        self.assertEqual(out[1]["href"], "/week/2026-06-26")


class ExtractPayloadsTest(unittest.TestCase):
    def test_extracts_three_payloads(self):
        html = (
            '<script>window.__PAPERS__ = [{"id":"p1"}];'
            'window.__WEEKLY__ = {"overview":"ov","highlights":[]};'
            'window.__TRENDING__ = {"items":[{"repo":"r"}]};</script>'
        )
        out = weeks.extract_payloads_from_html(html)
        self.assertEqual(out["papers"], [{"id": "p1"}])
        self.assertEqual(out["weekly"]["overview"], "ov")
        self.assertEqual(out["trending"]["items"], [{"repo": "r"}])

    def test_missing_payloads_use_defaults(self):
        out = weeks.extract_payloads_from_html("<html>no scripts</html>")
        self.assertEqual(out["papers"], [])
        self.assertEqual(out["weekly"], {"overview": "", "highlights": []})
        self.assertEqual(out["trending"], {"items": []})

    def test_papers_with_semicolon_bracket_in_string(self):
        # A paper whose title contains "];" must not truncate the PAPERS capture.
        html = (
            '<script>window.__PAPERS__ = [{"id":"p1","title":"a];b"}];'
            'window.__WEEKLY__ = {"overview":"ov","highlights":[]};'
            'window.__TRENDING__ = {"items":[]};</script>'
        )
        out = weeks.extract_payloads_from_html(html)
        self.assertEqual(out["papers"], [{"id": "p1", "title": "a];b"}])
        self.assertEqual(out["weekly"]["overview"], "ov")


if __name__ == "__main__":
    unittest.main()
