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
            "papers": [{
                "id": "arxiv-x1", "source_tier": "官方动态",
                "recommendation": "推荐",
                "title_zh": "端侧智能体推理框架",
                "abstract": "这项工作让端侧智能体在手机上更快完成推理，并减少运行内存。",
                "recommendation_reason": "端侧收益明确，而且给出了真实设备上的验证结果。",
                "edge_agent_scope": "非端侧Agent", "edge_agent_evidence": "",
                "tags": ["方向:高效推理"], "score_relevance": 7,
            }],
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
               '<main><section id="recommendations"></section><section id="weekly"></section>'
               '<section id="all-research"><div id="source-map"></div></section>'
               '<section id="discovery"></section></main>'
               '<script>window.__PAPERS__={"papers": [{"id": "arxiv-x1", "recommendation": "推荐", '
               '"title_zh": "端侧智能体推理框架", '
               '"abstract": "这项工作让端侧智能体在手机上更快完成推理，并减少运行内存。", '
               '"recommendation_reason": "端侧收益明确，而且给出了真实设备上的验证结果。", '
               '"edge_agent_scope":"非端侧Agent","edge_agent_evidence":"",'
               '"tags":["方向:高效推理"],"score_relevance":7}]};'
               'window.__WEEKLY__={"overview":"","highlights":[]};'
               'window.__TRENDING__={"items":[]};'
               'window.__WEEKS__=[];window.__WEEK_LABEL__=null;window.__WEEKS_BASE__="";</script>'
               '<script>let data=window.__PAPERS__||null;</script>')
        # detail page exists -> no 404
        _write(self.root, "site/paper/arxiv-x1.html", "<html>detail</html>")
        _write(self.root, "site/notes.html", "<html>notes</html>")
        _write(self.root, "site/snn.html", "<html>snn</html>")
        _write(self.root, "site/waic.html", "<html>waic</html>")
        # fresh trending file (mtime now) so check_trending_freshness passes
        _write(self.root, "data/github_trending_top20.json", "[]")
        import os
        os.utime(self.root / "data" / "github_trending_top20.json", None)  # touch -> now

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

    # ---- editorial layout ----
    def test_fail_when_discovery_section_is_missing(self):
        self._seed_good()
        index = self.root / "site" / "index.html"
        html = index.read_text(encoding="utf-8").replace(
            '<section id="discovery"></section>', ""
        )
        index.write_text(html, encoding="utf-8")

        errs = gr.run_all(self.root)

        self.assertTrue(any("discovery" in e or "发现线索" in e for e in errs), errs)

    def test_fail_when_complete_library_excludes_recommendations(self):
        self._seed_good()
        index = self.root / "site" / "index.html"
        html = index.read_text(encoding="utf-8").replace(
            "</script>", "visible().filter(p=>!isRecommended(p));</script>"
        )
        index.write_text(html, encoding="utf-8")

        errs = gr.run_all(self.root)

        self.assertTrue(any("完整" in e and "推荐" in e for e in errs), errs)

    def test_fail_when_static_page_does_not_prefer_inlined_papers(self):
        self._seed_good()
        index = self.root / "site" / "index.html"
        html = index.read_text(encoding="utf-8").replace(
            "let data=window.__PAPERS__||null;", ""
        )
        index.write_text(html, encoding="utf-8")

        errs = gr.run_all(self.root)

        self.assertTrue(any("inlined" in e.lower() or "静态" in e for e in errs), errs)

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

    # ---- recommendation readability ----
    def test_fail_when_edge_agent_scope_is_unreviewed(self):
        self._seed_good()
        _write(self.root, "site/index.html",
               '<script>window.__PAPERS__={"papers":[{"id":"arxiv-x1","recommendation":"推荐",'
               '"title_zh":"手机本地助理","abstract":"这项工作让手机在本地完成规划和工具调用。",'
               '"recommendation_reason":"关键智能体闭环在手机本地运行，值得优先关注。",'
               '"edge_agent_scope":"待核实","edge_agent_evidence":"",'
               '"tags":["方向:高效推理"],"score_relevance":9}]};'
               'window.__WEEKLY__={};window.__TRENDING__={};'
               'window.__WEEKS__=[];window.__WEEK_LABEL__=null;window.__WEEKS_BASE__="";</script>')

        errs = gr.run_all(self.root)

        self.assertTrue(any("edge_agent_scope" in e and "待核实" in e for e in errs), errs)

    def test_fail_when_arxiv_update_has_no_substantive_revision_note(self):
        self._seed_good()
        _write(self.root, "site/index.html",
               '<script>window.__PAPERS__={"papers":[{"id":"arxiv-x1","recommendation":"推荐",'
               '"title_zh":"端侧智能体推理框架","abstract":"这项工作让手机在本地完成推理。",'
               '"recommendation_reason":"端侧收益明确，而且给出了真实设备验证。",'
               '"edge_agent_scope":"非端侧Agent","edge_agent_evidence":"",'
               '"arxiv_date_basis":"updated","arxiv_revision_note":"",'
               '"tags":["方向:高效推理"],"score_relevance":7}]};'
               'window.__WEEKLY__={};window.__TRENDING__={};'
               'window.__WEEKS__=[];window.__WEEK_LABEL__=null;window.__WEEKS_BASE__="";</script>')

        errs = gr.run_all(self.root)

        self.assertTrue(any("arxiv_revision_note" in e for e in errs), errs)

    def test_fail_when_verified_phone_agent_is_not_recommended(self):
        self._seed_good()
        _write(self.root, "site/index.html",
               '<script>window.__PAPERS__={"papers":[{"id":"phone-agent","recommendation":"纳入",'
               '"title_zh":"","abstract":"这项工作让手机在本地完成规划和工具调用。",'
               '"recommendation_reason":"","edge_agent_scope":"手机",'
               '"edge_agent_evidence":"规划和工具调用均在手机本地运行。",'
               '"tags":["方向:端侧agent","硬件:手机"],"score_relevance":9}]};'
               'window.__WEEKLY__={};window.__TRENDING__={};'
               'window.__WEEKS__=[];window.__WEEK_LABEL__=null;window.__WEEKS_BASE__="";</script>')
        _write(self.root, "site/paper/phone-agent.html", "<html>detail</html>")

        errs = gr.run_all(self.root)

        self.assertTrue(any("真正端侧 Agent" in e and "推荐" in e for e in errs), errs)

    def test_fail_when_edge_agent_scope_and_tag_disagree(self):
        self._seed_good()
        _write(self.root, "site/index.html",
               '<script>window.__PAPERS__={"papers":[{"id":"ordinary-edge-model","recommendation":"推荐",'
               '"title_zh":"普通端侧模型","abstract":"这项工作只优化手机模型推理，没有智能体闭环。",'
               '"recommendation_reason":"具有端侧工程参考价值，因此作为普通项目推荐。",'
               '"edge_agent_scope":"非端侧Agent","edge_agent_evidence":"",'
               '"tags":["方向:端侧agent","硬件:手机"],"score_relevance":7}]};'
               'window.__WEEKLY__={};window.__TRENDING__={};'
               'window.__WEEKS__=[];window.__WEEK_LABEL__=null;window.__WEEKS_BASE__="";</script>')
        _write(self.root, "site/paper/ordinary-edge-model.html", "<html>detail</html>")

        errs = gr.run_all(self.root)

        self.assertTrue(any("方向:端侧agent" in e for e in errs), errs)

    def test_fail_when_current_build_has_no_recommendations(self):
        self._seed_good()
        _write(self.root, "site/index.html",
               '<script>window.__PAPERS__={"papers":[{"id":"arxiv-x1","recommendation":"纳入",'
               '"abstract":"这是一条中文摘要。","recommendation_reason":""}]};'
               'window.__WEEKLY__={};window.__TRENDING__={};'
               'window.__WEEKS__=[];window.__WEEK_LABEL__=null;window.__WEEKS_BASE__="";</script>')

        errs = gr.run_all(self.root)

        self.assertTrue(any("推荐" in e and "至少" in e for e in errs), errs)

    def test_fail_when_recommendation_summary_is_english_only(self):
        self._seed_good()
        _write(self.root, "site/index.html",
               '<script>window.__PAPERS__={"papers":[{"id":"arxiv-x1","recommendation":"推荐",'
               '"title_zh":"端侧智能体推理框架",'
               '"abstract":"English-only edge AI summary.",'
               '"recommendation_reason":"端侧收益明确，而且给出了真实设备上的验证结果。"}]};'
               'window.__WEEKLY__={};window.__TRENDING__={};'
               'window.__WEEKS__=[];window.__WEEK_LABEL__=null;window.__WEEKS_BASE__="";</script>')

        errs = gr.run_all(self.root)

        self.assertTrue(any("abstract" in e and "中文" in e for e in errs), errs)

    def test_fail_when_recommendation_reason_is_missing(self):
        self._seed_good()
        _write(self.root, "site/index.html",
               '<script>window.__PAPERS__={"papers":[{"id":"arxiv-x1","recommendation":"推荐",'
               '"title_zh":"端侧智能体推理框架",'
               '"abstract":"这项工作让端侧智能体在手机上更快完成推理。",'
               '"recommendation_reason":""}]};'
               'window.__WEEKLY__={};window.__TRENDING__={};'
               'window.__WEEKS__=[];window.__WEEK_LABEL__=null;window.__WEEKS_BASE__="";</script>')

        errs = gr.run_all(self.root)

        self.assertTrue(any("recommendation_reason" in e for e in errs), errs)

    def test_fail_when_recommendation_title_zh_is_missing(self):
        self._seed_good()
        _write(self.root, "site/index.html",
               '<script>window.__PAPERS__={"papers":[{"id":"arxiv-x1","recommendation":"推荐",'
               '"title_zh":"",'
               '"abstract":"这项工作让端侧智能体在手机上更快完成推理。",'
               '"recommendation_reason":"端侧收益明确，而且给出了真实设备上的验证结果。"}]};'
               'window.__WEEKLY__={};window.__TRENDING__={};'
               'window.__WEEKS__=[];window.__WEEK_LABEL__=null;window.__WEEKS_BASE__="";</script>')

        errs = gr.run_all(self.root)

        self.assertTrue(any("title_zh" in e for e in errs), errs)

    def test_fail_when_title_zh_repeats_abstract(self):
        self._seed_good()
        abstract = "这是一条可以直接阅读的中文项目介绍。"
        _write(self.root, "site/index.html",
               '<script>window.__PAPERS__={"papers":[{"id":"arxiv-x1","recommendation":"推荐",'
               f'"title_zh":"{abstract}","abstract":"{abstract}",'
               '"recommendation_reason":"端侧收益明确，而且给出了真实设备上的验证结果。"}]};'
               'window.__WEEKLY__={};window.__TRENDING__={};'
               'window.__WEEKS__=[];window.__WEEK_LABEL__=null;window.__WEEKS_BASE__="";</script>')

        errs = gr.run_all(self.root)

        self.assertTrue(any("title_zh" in e and "介绍" in e for e in errs), errs)

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

    # ---- snn page ----
    def test_fail_when_snn_page_missing(self):
        self._seed_good()
        (self.root / "site" / "snn.html").unlink()
        errs = gr.run_all(self.root)
        self.assertTrue(any("snn.html" in e and "missing" in e for e in errs), errs)

    # ---- waic page ----
    def test_fail_when_waic_page_missing(self):
        self._seed_good()
        (self.root / "site" / "waic.html").unlink()
        errs = gr.run_all(self.root)
        self.assertTrue(any("waic.html" in e and "missing" in e for e in errs), errs)

    def test_pass_good_layout(self):
        self._seed_good()
        errs = gr.run_all(self.root)
        self.assertEqual(errs, [], errs)

    # ---- trending freshness ----
    def test_fail_when_trending_file_missing(self):
        self._seed_good()
        (self.root / "data" / "github_trending_top20.json").unlink()
        errs = gr.run_all(self.root)
        self.assertTrue(any("github_trending_top20" in e and "missing" in e for e in errs), errs)

    def test_fail_when_trending_file_stale(self):
        self._seed_good()
        import os, time
        p = self.root / "data" / "github_trending_top20.json"
        # set mtime 10 days ago -> > 7d threshold
        old = time.time() - 10 * 86400
        os.utime(p, (old, old))
        errs = gr.run_all(self.root)
        self.assertTrue(any("stale" in e or "old" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
