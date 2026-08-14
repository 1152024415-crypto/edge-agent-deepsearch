#!/usr/bin/env python3
"""Mirror-mode build tests.

Starts a real display server on an ephemeral port, publishes one validated
paper, runs ``python app/build.py --server <url>`` against it, and asserts the
generated ``site/`` snapshot inlines the papers payload and mirrors the detail
page with a rewritten back link.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # for app package
sys.path.insert(0, str(ROOT / "agent"))  # for research_run / publish_results

import publish_results
import research_collection
import research_run
from app import build as build_app
from app import server as server_app
from app import weeks as weeks_mod
from app.notes_page import NOTES_HTML

TODAY = date.today()
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()
TEST_PUBLISH_TOKEN = "test-publish-secret"
_TEST_ARTIFACT_DIRS = []


class NotesPageTest(unittest.TestCase):
    def test_markdown_frontmatter_is_hidden_but_copy_keeps_original(self):
        self.assertIn("function stripFrontmatter(md)", NOTES_HTML)
        self.assertIn("LAST_RAW = md", NOTES_HTML)
        self.assertIn("var pm = protectMath(stripFrontmatter(md));", NOTES_HTML)


def _score_dims(score):
    """Legal 2-dim breakdown summing to ``score`` (relevance + contribution, each 0-10)."""
    rel = min(10, max(0, score))
    con = max(0, score - rel)
    return rel, con


def valid_paper(**overrides):
    paper = {
        "id": "fresh-edge-agent-paper",
        "title": "Fresh Edge Agent Paper",
        "title_zh": "端侧智能体规划框架",
        "abstract": "这项工作让端侧智能体在设备本地完成规划与执行，减少对云端服务的依赖。",
        "effects": "在端侧基准上将推理延迟降低了 23%。",
        "mechanism": "通过规划器与执行器循环，并压缩本地记忆来控制资源开销。",
        "paper_url": "https://openreview.net/forum?id=fresh-edge-agent-paper",
        "date": YESTERDAY,
        "score": 14,
        "score_reason": "Strong edge-agent relevance with reported benchmark effect.",
        "source_tier": "学校顶会",
        "open_source": False,
        "tags": ["方向:端侧agent", "方向:记忆", "方向:评测基准"],
        "edge_agent_scope": "手机",
        "edge_agent_evidence": "论文明确说明规划、记忆和执行闭环均在手机本地运行。",
        "recommendation": "推荐",
        "recommendation_reason": "端侧收益明确，并在真实设备上给出了可核验的延迟改善。",
        "insight_person": "",
        "wiki_url": "",
        "candidate_source": "",
        "candidate_ref": "",
    }
    paper.update(overrides)
    rel, con = _score_dims(paper["score"])
    paper.setdefault("score_relevance", rel)
    paper.setdefault("score_contribution", con)
    return paper


def run_payload(*papers):
    start, end, days = research_collection.collection_window(TODAY)
    tempdir = tempfile.TemporaryDirectory()
    _TEST_ARTIFACT_DIRS.append(tempdir)
    artifact_dir = Path(tempdir.name)
    candidates = []
    normalized_papers = []
    for paper in papers:
        candidate = {
            "id": paper["id"],
            "title": paper["title"],
            "paper_url": paper["paper_url"],
            "date": paper["date"],
        }
        candidates.append(candidate)
        normalized = dict(paper)
        normalized["candidate_source"] = "huggingface"
        normalized["candidate_ref"] = research_collection.candidate_record_ref(candidate)
        normalized_papers.append(normalized)
    artifact_paths = {}
    attestations = {}
    for source in ("arxiv", "huggingface", "github", "vendors"):
        path = artifact_dir / f"{source}.json"
        path.write_text(
            json.dumps(candidates if source == "huggingface" else [], ensure_ascii=False),
            encoding="utf-8",
        )
        artifact_paths[source] = path
        attestations[source] = research_collection.candidate_artifact_attestation(path, source)
    return {
        "run_id": "run-20260625-120000",
        "generated_at": "2026-06-25T12:00:00+08:00",
        "collection_manifest": {
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "sources": {
                "arxiv": {
                    "status": "complete", "candidate_count": 0,
                    **attestations["arxiv"],
                    "queries_completed": sorted(research_collection.REQUIRED_ARXIV_SWEEPS),
                    "pages_fetched": len(research_collection.REQUIRED_ARXIV_SWEEPS),
                },
                "huggingface": {
                    "status": "complete", "candidate_count": 0,
                    **attestations["huggingface"],
                    "dates_checked": [day.isoformat() for day in days],
                },
                "github": {
                    "status": "complete", "candidate_count": 0,
                    **attestations["github"],
                    "release_projects_checked": sorted(research_collection.REQUIRED_GITHUB_PROJECTS),
                    "trending_checked": True,
                },
                "vendors": {
                    "status": "complete", "candidate_count": 0,
                    **attestations["vendors"],
                    "vendors_checked": sorted(research_collection.REQUIRED_VENDOR_SOURCES),
                    "vendor_checks": {
                        vendor: {"status": "no_match", "sources_succeeded": ["official-index"]}
                        for vendor in research_collection.REQUIRED_VENDOR_SOURCES
                    },
                },
            },
        },
        "papers": normalized_papers,
    }


def _weeks_tmp_env(self):
    """Redirect weeks_mod.WEEKS_DIR + EDGE_WEEKS_DIR env to a tmp dir, so the
    subprocess ``python app/build.py`` writes archives to tmp instead of the
    real committed ``data/weeks/`` (which a test must never wipe). Also returns
    an env dict to pass to subprocess.run.

    Call in setUp; cleanups are registered automatically.
    """
    tmp = tempfile.TemporaryDirectory()
    self.addCleanup(tmp.cleanup)
    weeks_dir = Path(tmp.name)
    orig = weeks_mod.WEEKS_DIR
    weeks_mod.WEEKS_DIR = weeks_dir
    self.addCleanup(lambda: setattr(weeks_mod, "WEEKS_DIR", orig))
    self.weeks_dir = weeks_dir
    self.weeks_env = {**os.environ, "EDGE_WEEKS_DIR": str(weeks_dir)}


class MirrorBuildTest(unittest.TestCase):
    def setUp(self):
        # validate_payload checks paper_url liveness; stub it for the test.
        patcher = mock.patch("research_run.is_link_alive", return_value=True)
        self.addCleanup(patcher.stop)
        patcher.start()

        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        db_path = Path(self._tmpdir.name) / "papers.sqlite"

        self.httpd = server_app.create_server(
            ("127.0.0.1", 0), db_path, publish_token=TEST_PUBLISH_TOKEN
        )
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_port}"
        self.addCleanup(self._stop_server)

        self.site_dir = ROOT / "site"
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)
        self.addCleanup(self._cleanup_site)

        # Redirect the week archive to a tmp dir (subprocess build.py picks up
        # EDGE_WEEKS_DIR via env). Never wipe the real data/weeks/ archive.
        _weeks_tmp_env(self)

    def _stop_server(self):
        self.httpd.shutdown()
        self.thread.join(timeout=5)
        self.httpd.server_close()

    def _cleanup_site(self):
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)

    def test_build_mirrors_server_to_static_site(self):
        # Publish one validated paper to the running test server.
        payload = research_run.validate_payload(run_payload(valid_paper()), today=TODAY)
        publish_results.publish_payload(self.base_url, payload, token=TEST_PUBLISH_TOKEN)

        # Run build.py against the ephemeral server URL.
        result = subprocess.run(
            [sys.executable, str(ROOT / "app" / "build.py"),
             "--server", self.base_url],
            cwd=ROOT,
            env=self.weeks_env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"build.py failed:\nstdout={result.stdout}\nstderr={result.stderr}",
        )

        # index.html: exists, inlines papers payload, contains paper title.
        index_path = self.site_dir / "index.html"
        self.assertTrue(index_path.exists(), "site/index.html was not generated")
        index_html = index_path.read_text(encoding="utf-8")
        self.assertIn("window.__PAPERS__", index_html)
        self.assertIn("let data=window.__PAPERS__||null;", index_html)
        self.assertIn("Fresh Edge Agent Paper", index_html)
        self.assertTrue(
            (self.site_dir / ".nojekyll").is_file(),
            "static builds must disable Jekyll so Markdown notes remain .md files",
        )

        # Detail page: exists, contains the paper title, back link rewritten.
        detail_path = self.site_dir / "paper" / "fresh-edge-agent-paper.html"
        self.assertTrue(detail_path.exists(), "site/paper/<id>.html was not generated")
        detail_html = detail_path.read_text(encoding="utf-8")
        self.assertIn("Fresh Edge Agent Paper", detail_html)
        self.assertIn('href="../index.html"', detail_html)


class RenderPageTest(unittest.TestCase):
    def test_render_page_inlines_weeks_and_label_and_prefixes_paper_links(self):
        html = (
            '<html><head></head><body>'
            '<script>let data=window.__PAPERS__||null;'
            'if(!data){const res=await fetch("/api/papers");'
            'if(!res.ok)throw new Error("HTTP "+res.status);data=await res.json();}'
            'let w=window.__WEEKLY__||null;'
            'if(!w){const wr=await fetch("/api/weekly");w=await wr.json();}</script>'
            '<a href="/paper/abc">x</a><a href="/paper/${escapeAttr(p.id)}">y</a>'
            '</body></html>'
        )
        weeks = [{"label": "2026-06-26", "title": "06-26~07-03", "current": False, "href": "../week/2026-06-26.html"}]
        out = build_app.render_page(
            html, [{"id": "abc"}], {"overview": ""}, {"items": []},
            weeks, week_label="2026-06-26", weeks_base="../", runtime=False,
            community={"items": [{"id": "signal-1"}]})
        self.assertIn("window.__PAPERS__", out)
        # __PAPERS__ must be a {"papers":[...]} dict (matches /api/papers contract;
        # page.py reads `data.papers`). A bare list here would render "0 signals".
        self.assertIn('window.__PAPERS__={"papers":', out)
        self.assertIn("window.__WEEKS__", out)
        self.assertIn('window.__COMMUNITY__={"items": [{"id": "signal-1"}]}', out)
        self.assertIn('"2026-06-26"', out)  # week_label inlined
        self.assertIn('window.__WEEKS_BASE__="../"', out)
        # The inline payload is preferred; the API fetch remains as the live-server fallback.
        self.assertIn('let data=window.__PAPERS__||null;', out)
        self.assertIn('fetch("/api/papers")', out)
        # paper links prefixed with ../
        self.assertIn('href="../paper/abc.html"', out)
        self.assertIn('href="../paper/${escapeAttr(p.id)}.html"', out)

    def test_render_page_rewrites_notes_html_link_for_static_subdir(self):
        html = '<a href="notes.html">调研笔记</a>'
        out = build_app.render_page(html, [], {"overview": ""}, {"items": []}, [],
                                    week_label=None, weeks_base="../", runtime=False)
        self.assertIn('href="../notes.html"', out)
        self.assertNotIn('href="notes.html"', out)
        # runtime keeps notes.html as-is (no rewrite)
        out_rt = build_app.render_page(html, [], {"overview": ""}, {"items": []}, [],
                                       week_label=None, weeks_base="../", runtime=True)
        self.assertIn('href="notes.html"', out_rt)

    def test_render_page_rewrites_weekly_highlight_paper_links(self):
        # weekly highlights link to papers via href="/paper/${paper_id}"; on a
        # static gh-pages subpath the absolute /paper/... would 404 (resolves to
        # domain root). render_page must prefix it with weeks_base + .html like
        # the row template, so highlights resolve to the static detail page.
        html = '<a class="weekly-topic" href="/paper/${escapeAttr(h.paper_id)}">t</a>'
        out = build_app.render_page(html, [], {"overview": ""}, {"items": []}, [],
                                    week_label=None, weeks_base="../", runtime=False)
        self.assertIn('href="../paper/${escapeAttr(h.paper_id)}.html"', out)
        self.assertNotIn('href="/paper/${escapeAttr(h.paper_id)}"', out)
        # runtime keeps the absolute form (server serves /paper/<id>)
        out_rt = build_app.render_page(html, [], {"overview": ""}, {"items": []}, [],
                                       week_label=None, weeks_base="../", runtime=True)
        self.assertIn('href="/paper/${escapeAttr(h.paper_id)}"', out_rt)

    def test_render_page_strips_runtime_server_globals(self):
        # server.py injects a runtime globals block (WEEKS with "/" hrefs,
        # WEEK_LABEL=null, WEEKS_BASE="") into /. build.py fetches / as a
        # template; render_page MUST strip that block so its own static values
        # win (else the server's runtime hrefs break switching on gh-pages).
        html = (
            '<html><body>'
            '<script>window.__WEEKS__ = [{"label":"2026-07-02","current":true,"href":"/"},'
            '{"label":"2026-06-26","current":false,"href":"/week/2026-06-26"}];'
            'window.__WEEK_LABEL__ = null;window.__WEEKS_BASE__ = "";</script>'
            '<script>let ALL=[];</script></body></html>'
        )
        weeks = [{"label": "2026-06-26", "current": False, "href": "../week/2026-06-26.html"}]
        out = build_app.render_page(html, [], {"overview": ""}, {"items": []}, weeks,
                                    week_label="2026-06-26", weeks_base="../", runtime=False)
        # the server's runtime block is gone (no "/" href, no '= null' label)
        self.assertNotIn('window.__WEEK_LABEL__ = null', out)
        self.assertNotIn('"href":"/"', out)
        # render_page's own static values are the only assignment
        self.assertIn('window.__WEEK_LABEL__="2026-06-26"', out)
        self.assertIn('window.__WEEKS_BASE__="../"', out)


class PageSwitcherTest(unittest.TestCase):
    def test_index_html_has_switcher_select_and_js(self):
        from app.page import INDEX_HTML
        self.assertIn('id="week-switch"', INDEX_HTML)
        self.assertIn("renderWeekSwitch", INDEX_HTML)
        # reads the inlined globals
        self.assertIn("window.__WEEKS__", INDEX_HTML)
        self.assertIn("window.__WEEK_LABEL__", INDEX_HTML)

    def test_header_range_uses_editorial_week_window_not_last_paper_date(self):
        from app.page import INDEX_HTML

        self.assertIn("const weekMeta=mine", INDEX_HTML)
        self.assertIn("weekMeta.range.start", INDEX_HTML)
        self.assertIn("weekMeta.range.end", INDEX_HTML)


class WeekArchiveBuildTest(unittest.TestCase):
    def setUp(self):
        self.site_dir = ROOT / "site"
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)
        self.addCleanup(self._cleanup)
        _weeks_tmp_env(self)

    def _cleanup(self):
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)

    def _seed_index(self, overview):
        """Stand in for an existing built index.html with inlined payloads."""
        html = (
            '<html><head></head><body>'
            f'<script>window.__PAPERS__ = [{{"id":"p1","title":"T","date":"2026-06-28"}}];'
            f'window.__WEEKLY__ = {{"overview":"{overview}","highlights":[]}};'
            f'window.__TRENDING__ = {{"items":[]}};</script>'
            '</body></html>'
        )
        self.site_dir.mkdir(parents=True, exist_ok=True)
        (self.site_dir / "index.html").write_text(html, encoding="utf-8")

    def test_backfill_creates_archive_from_existing_index(self):
        self._seed_index("本周端侧动态(06-26~07-03)：...")
        result = subprocess.run(
            [sys.executable, str(ROOT / "app" / "build.py"), "--backfill"],
            cwd=ROOT, env=self.weeks_env, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=f"{result.stdout}\n{result.stderr}")
        a = weeks_mod.read_archive("2026-06-26")
        self.assertIsNotNone(a)
        self.assertEqual(a["papers"], [{"id": "p1", "title": "T", "date": "2026-06-28"}])
        self.assertEqual(a["weekly"]["overview"], "本周端侧动态(06-26~07-03)：...")

    def test_backfill_missing_index_is_noop(self):
        # no site/index.html -> backfill prints warning, returns 0, no archive
        result = subprocess.run(
            [sys.executable, str(ROOT / "app" / "build.py"), "--backfill"],
            cwd=ROOT, env=self.weeks_env, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(weeks_mod.read_manifest(), [])


class TwoWeekFlowTest(unittest.TestCase):
    """Backfill last week from an existing index, then build a new week against
    a live server, and assert both weeks render + switcher present."""

    def setUp(self):
        self.site_dir = ROOT / "site"
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)
        self.addCleanup(self._cleanup)
        _weeks_tmp_env(self)
        # validate_payload checks paper_url liveness; stub it for the test.
        patcher = mock.patch("research_run.is_link_alive", return_value=True)
        self.addCleanup(patcher.stop)
        patcher.start()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        db_path = Path(self._tmp.name) / "papers.sqlite"
        self.httpd = server_app.create_server(
            ("127.0.0.1", 0), db_path, publish_token=TEST_PUBLISH_TOKEN
        )
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_port}"
        self.addCleanup(self._stop)

    def _cleanup(self):
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)

    def _stop(self):
        self.httpd.shutdown()
        self.thread.join(timeout=5)
        self.httpd.server_close()

    def test_backfill_then_build_renders_both_weeks(self):
        # 1) seed an "old" built index with last week's inlined payload
        old_html = ('<html><body>'
                    '<script>window.__PAPERS__ = [{"id":"old","title":"Old","date":"2026-06-28"}];'
                    'window.__WEEKLY__ = {"overview":"本周动态(06-26~07-03)：...","highlights":[]};'
                    'window.__TRENDING__ = {"items":[]};</script></body></html>')
        self.site_dir.mkdir(parents=True, exist_ok=True)
        (self.site_dir / "index.html").write_text(old_html, encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "app" / "build.py"), "--backfill"],
                           cwd=ROOT, env=self.weeks_env, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, msg=f"{r.stdout}\n{r.stderr}")

        # 2) publish a "new week" paper to the live server and build
        payload = research_run.validate_payload(
            run_payload(valid_paper(id="new-week-paper", title="New Week Paper",
                                   date=TODAY.isoformat())),
            today=TODAY)
        # put a current-week overview in weekly_summary.json so parse picks 07-02.
        # data/weekly_summary.json is a real data file — back it up + restore.
        wp = ROOT / "data" / "weekly_summary.json"
        wp.parent.mkdir(parents=True, exist_ok=True)
        backup = wp.read_text(encoding="utf-8") if wp.exists() else None
        wp.write_text(json.dumps(
            {"overview": "本周动态(07-02~07-09)：...", "highlights": []},
            ensure_ascii=False), encoding="utf-8")
        if backup is not None:
            self.addCleanup(lambda: wp.write_text(backup, encoding="utf-8"))
        else:
            self.addCleanup(lambda: wp.unlink(missing_ok=True))
        publish_results.publish_payload(self.base_url, payload, token=TEST_PUBLISH_TOKEN)

        r = subprocess.run([sys.executable, str(ROOT / "app" / "build.py"),
                            "--server", self.base_url],
                           cwd=ROOT, env=self.weeks_env, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, msg=f"{r.stdout}\n{r.stderr}")

        # 3) current index = new week, has switcher
        idx = (self.site_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn("New Week Paper", idx)
        self.assertIn("window.__WEEKS__", idx)
        self.assertIn("window.__WEEK_LABEL__", idx)
        # render_page inlines with NO spaces (window.__WEEK_LABEL__=null)
        self.assertIn("window.__WEEK_LABEL__=null", idx)

        # 4) past week page rendered
        past = self.site_dir / "week" / "2026-06-26.html"
        self.assertTrue(past.exists(), "past week page not rendered")
        past_html = past.read_text(encoding="utf-8")
        self.assertIn("Old", past_html)
        self.assertIn("window.__WEEK_LABEL__", past_html)
        self.assertIn('"2026-06-26"', past_html)
        # switcher hrefs in subdir use ../ prefix
        self.assertIn("../index.html", past_html)
        self.assertIn("../week/2026-06-26.html", past_html)


if __name__ == "__main__":
    unittest.main()
