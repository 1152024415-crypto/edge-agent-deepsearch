#!/usr/bin/env python3
"""Mirror-mode build tests.

Starts a real display server on an ephemeral port, publishes one validated
paper, runs ``python app/build.py --server <url>`` against it, and asserts the
generated ``site/`` snapshot inlines the papers payload and mirrors the detail
page with a rewritten back link.
"""

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
import research_run
from app import build as build_app
from app import server as server_app
from app import weeks as weeks_mod

TODAY = date.today()
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()


def _score_dims(score):
    """Legal 2-dim breakdown summing to ``score`` (relevance + contribution, each 0-10)."""
    rel = min(10, max(0, score))
    con = max(0, score - rel)
    return rel, con


def valid_paper(**overrides):
    paper = {
        "id": "fresh-edge-agent-paper",
        "title": "Fresh Edge Agent Paper",
        "abstract": "A real paper abstract about edge-side agent execution.",
        "effects": "Reports 23% latency reduction on an on-device benchmark.",
        "mechanism": "Uses a planner-executor loop with compressed local memory.",
        "paper_url": "https://openreview.net/forum?id=fresh-edge-agent-paper",
        "date": YESTERDAY,
        "score": 14,
        "score_reason": "Strong edge-agent relevance with reported benchmark effect.",
        "source_tier": "学校顶会",
        "open_source": False,
        "tags": ["方向:端侧agent", "方向:记忆", "方向:评测基准"],
        "insight_person": "",
        "wiki_url": "",
    }
    paper.update(overrides)
    rel, con = _score_dims(paper["score"])
    paper.setdefault("score_relevance", rel)
    paper.setdefault("score_contribution", con)
    return paper


def run_payload(*papers):
    return {
        "run_id": "run-20260625-120000",
        "generated_at": "2026-06-25T12:00:00+08:00",
        "papers": list(papers),
    }


class MirrorBuildTest(unittest.TestCase):
    def setUp(self):
        # validate_payload checks paper_url liveness; stub it for the test.
        patcher = mock.patch("research_run.is_link_alive", return_value=True)
        self.addCleanup(patcher.stop)
        patcher.start()

        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        db_path = Path(self._tmpdir.name) / "papers.sqlite"

        self.httpd = server_app.create_server(("127.0.0.1", 0), db_path)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_port}"
        self.addCleanup(self._stop_server)

        self.site_dir = ROOT / "site"
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)
        self.addCleanup(self._cleanup_site)

        self.weeks_dir = ROOT / "data" / "weeks"
        if self.weeks_dir.exists():
            shutil.rmtree(self.weeks_dir)
        self.addCleanup(self._cleanup_weeks)

    def _stop_server(self):
        self.httpd.shutdown()
        self.thread.join(timeout=5)
        self.httpd.server_close()

    def _cleanup_site(self):
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)

    def _cleanup_weeks(self):
        if (ROOT / "data" / "weeks").exists():
            shutil.rmtree(ROOT / "data" / "weeks")

    def test_build_mirrors_server_to_static_site(self):
        # Publish one validated paper to the running test server.
        payload = research_run.validate_payload(run_payload(valid_paper()), today=TODAY)
        publish_results.publish_payload(self.base_url, payload)

        # Run build.py against the ephemeral server URL.
        result = subprocess.run(
            [sys.executable, str(ROOT / "app" / "build.py"),
             "--server", self.base_url],
            cwd=ROOT,
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
        self.assertIn("Fresh Edge Agent Paper", index_html)

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
            '<script>const res=await fetch("/api/papers");const data=await res.json();'
            'const wr=await fetch("/api/weekly");const w=await wr.json();</script>'
            '<a href="/paper/abc">x</a><a href="/paper/${escapeAttr(p.id)}">y</a>'
            '</body></html>'
        )
        weeks = [{"label": "2026-06-26", "title": "06-26~07-03", "current": False, "href": "../week/2026-06-26.html"}]
        out = build_app.render_page(html, [{"id": "abc"}], {"overview": ""}, {"items": []},
                                    weeks, week_label="2026-06-26", weeks_base="../", runtime=False)
        self.assertIn("window.__PAPERS__", out)
        self.assertIn("window.__WEEKS__", out)
        self.assertIn('"2026-06-26"', out)  # week_label inlined
        self.assertIn('window.__WEEKS_BASE__="../"', out)
        # fetch rewritten to globals
        self.assertNotIn('fetch("/api/papers")', out)
        # paper links prefixed with ../
        self.assertIn('href="../paper/abc.html"', out)
        self.assertIn('href="../paper/${escapeAttr(p.id)}.html"', out)


class WeekArchiveBuildTest(unittest.TestCase):
    def setUp(self):
        self.site_dir = ROOT / "site"
        self.weeks_dir = ROOT / "data" / "weeks"
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)
        if self.weeks_dir.exists():
            shutil.rmtree(self.weeks_dir)
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)
        if self.weeks_dir.exists():
            shutil.rmtree(self.weeks_dir)

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
            cwd=ROOT, capture_output=True, text=True, timeout=60,
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
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(weeks_mod.read_manifest(), [])


if __name__ == "__main__":
    unittest.main()
