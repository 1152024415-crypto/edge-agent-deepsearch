#!/usr/bin/env python3
"""Tests for gate_release — the pre-deploy release gate.

The gate operates on the BUILT site/ + data/ artifacts (not the legacy
frontmatter content dir), so it actually catches the failure modes that
shipped before: 0-paper list (bad __PAPERS__ contract), runtime globals
leaking into static pages, 404 highlight links, paper-duplicate highlights,
and silent 0-官方动态 (vendor blogs never collected).
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app" / "gates"))

import gate_release as gr


def _write(root: Path, rel: str, content: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


class GateReleaseTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def _seed_good(self):
        """A minimally-passing site+data layout."""
        # current week archive (1 paper, 1 官方动态 so the vendor gate passes)
        _write(self.root, "data/weeks/2026-07-02.json", json.dumps({
            "label": "2026-07-02", "title": "07-02~07-09",
            "range": {"start": "2026-07-02", "end": "2026-07-09"},
            "papers": [{"id": "arxiv-x1", "source_tier": "官方动态"}],
            "weekly": {"overview": "(07-02~07-09)", "highlights": []},
            "trending": {"items": []},
        }, ensure_ascii=False))
        _write(self.root, "data/weeks/manifest.json", json.dumps([
            {"label": "2026-07-02", "title": "07-02~07-09",
             "range": {"start": "2026-07-02", "end": "2026-07-09"}, "current": True},
        ], ensure_ascii=False))
        # weekly_summary: ≥5 external-url highlights (editorial, not paper dupes)
        hl = [{"url": f"https://vendor{i}.com/blog", "topic": f"news{i}", "why": "w"} for i in range(5)]
        _write(self.root, "data/weekly_summary.json", json.dumps(
            {"overview": "(07-02~07-09)", "highlights": hl}, ensure_ascii=False))
        # built index: dict __PAPERS__, no server injection
        _write(self.root, "site/index.html",
               '<script>window.__PAPERS__={"papers": [{"id": "arxiv-x1"}]};'
               'window.__WEEKLY__={"overview":"","highlights":[]};'
               'window.__TRENDING__={"items":[]};'
               'window.__WEEKS__=[];window.__WEEK_LABEL__=null;window.__WEEKS_BASE__="";</script>')
        # detail page exists -> no 404
        _write(self.root, "site/paper/arxiv-x1.html", "<html>detail</html>")
        _write(self.root, "site/notes.html", "<html>notes</html>")

    # ---- contract ----
    def test_fail_when_papers_inlined_as_bare_list(self):
        self._seed_good()
        _write(self.root, "site/index.html",
               '<script>window.__PAPERS__=[{"id":"arxiv-x1"}];'  # bare list, not dict
               'window.__WEEKLY__={};window.__TRENDING__={};'
               'window.__WEEKS__=[];window.__WEEK_LABEL__=null;window.__WEEKS_BASE__="";</script>')
        errs = gr.run_all(self.root)
        self.assertTrue(any("__PAPERS__" in e and "dict" in e for e in errs), errs)

    def test_fail_when_server_runtime_injection_present(self):
        self._seed_good()
        _write(self.root, "site/index.html",
               '<script>window.__WEEKS__ = [{"href":"/"}];window.__WEEK_LABEL__ = null;window.__WEEKS_BASE__ = "";</script>'
               '<script>window.__PAPERS__={"papers":[{"id":"arxiv-x1"}]};</script>')
        errs = gr.run_all(self.root)
        self.assertTrue(any("runtime" in e or "server" in e for e in errs), errs)

    # ---- links 200 ----
    def test_fail_when_detail_page_missing(self):
        self._seed_good()
        (self.root / "site" / "paper" / "arxiv-x1.html").unlink()
        errs = gr.run_all(self.root)
        self.assertTrue(any("paper/arxiv-x1" in e for e in errs), errs)

    def test_fail_when_past_week_archive_page_missing(self):
        self._seed_good()
        _write(self.root, "data/weeks/2026-06-26.json", json.dumps({
            "label": "2026-06-26", "papers": [], "weekly": {"overview": "", "highlights": []},
            "trending": {"items": []}}, ensure_ascii=False))
        _write(self.root, "data/weeks/manifest.json", json.dumps([
            {"label": "2026-07-02", "current": True, "range": {"start": "2026-07-02", "end": "2026-07-09"}, "title": "t"},
            {"label": "2026-06-26", "current": False, "range": {"start": "2026-06-26", "end": "2026-07-03"}, "title": "t"},
        ], ensure_ascii=False))
        errs = gr.run_all(self.root)
        self.assertTrue(any("week/2026-06-26" in e for e in errs), errs)

    # ---- highlights editorial ----
    def test_fail_when_highlights_all_paper_duplicates(self):
        self._seed_good()
        # all highlights are paper_id (no external url) -> duplicate of paper list
        hl = [{"url": "", "topic": f"paper{i}", "why": "w", "paper_id": "arxiv-x1"} for i in range(8)]
        _write(self.root, "data/weekly_summary.json", json.dumps(
            {"overview": "(07-02~07-09)", "highlights": hl}, ensure_ascii=False))
        errs = gr.run_all(self.root)
        self.assertTrue(any("editorial" in e or "duplicate" in e or "external" in e for e in errs), errs)

    def test_fail_when_highlights_paper_link_404(self):
        self._seed_good()
        hl = [{"url": "https://ok.com/blog", "topic": "n1", "why": "w"},  # 5 external (pass editorial count)
              {"url": "", "topic": "p1", "why": "w", "paper_id": "arxiv-missing"}]  # 404
        _write(self.root, "data/weekly_summary.json", json.dumps(
            {"overview": "(07-02~07-09)", "highlights": hl}, ensure_ascii=False))
        errs = gr.run_all(self.root)
        self.assertTrue(any("arxiv-missing" in e for e in errs), errs)

    # ---- vendor tier ----
    def test_fail_when_zero_vendor_and_no_evidence(self):
        self._seed_good()
        _write(self.root, "data/weeks/2026-07-02.json", json.dumps({
            "label": "2026-07-02", "papers": [{"id": "x", "source_tier": "学校预印本"}],
            "weekly": {"overview": "", "highlights": []}, "trending": {"items": []}},
            ensure_ascii=False))
        errs = gr.run_all(self.root)
        self.assertTrue(any("官方动态" in e for e in errs), errs)

    def test_pass_when_zero_vendor_but_evidence_file_exists(self):
        self._seed_good()
        _write(self.root, "data/weeks/2026-07-02.json", json.dumps({
            "label": "2026-07-02", "papers": [{"id": "x", "source_tier": "学校预印本"}],
            "weekly": {"overview": "", "highlights": []}, "trending": {"items": []}},
            ensure_ascii=False))
        _write(self.root, "data/weeks/2026-07-02-no-vendor.md",
               "# 0 vendor this week\n- Apple: no in-window edge post\n- Google: Gemma4 QAT was 06-05 (out)")
        errs = gr.run_all(self.root)
        self.assertEqual(errs, [], errs)

    def test_pass_good_layout(self):
        self._seed_good()
        errs = gr.run_all(self.root)
        self.assertEqual(errs, [], errs)


if __name__ == "__main__":
    unittest.main()
