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
from datetime import date
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # for app package
sys.path.insert(0, str(ROOT / "agent"))  # for research_run / publish_results

import publish_results
import research_run
from app import server as server_app

TODAY = date(2026, 6, 25)


def _score_dims(score):
    """Legal 6-dim breakdown summing to ``score``."""
    rec = min(5, max(0, score))
    rem = score - rec
    op = min(10, max(0, rem))
    rem -= op
    rel = min(30, rem)
    rem -= rel
    ven = min(25, rem)
    rem -= ven
    con = min(15, rem)
    rem -= con
    qua = min(15, rem)
    return rel, ven, con, qua, rec, op


def valid_paper(**overrides):
    paper = {
        "id": "fresh-edge-agent-paper",
        "title": "Fresh Edge Agent Paper",
        "abstract": "A real paper abstract about edge-side agent execution.",
        "effects": "Reports 23% latency reduction on an on-device benchmark.",
        "mechanism": "Uses a planner-executor loop with compressed local memory.",
        "paper_url": "https://arxiv.org/abs/2606.12345",
        "date": "2026-06-24",
        "score": 92,
        "score_reason": "Strong edge-agent relevance with reported benchmark effect.",
        "source_type": "学术论文",
        "is_major_vendor_official": False,
        "category": "应用",
        "keywords": ["GUI智能体", "端侧部署", "评测基准"],
        "insight_person": "",
        "wiki_url": "",
    }
    paper.update(overrides)
    rel, ven, con, qua, rec, op = _score_dims(paper["score"])
    paper.setdefault("score_relevance", rel)
    paper.setdefault("score_vendor", ven)
    paper.setdefault("score_contribution", con)
    paper.setdefault("score_quality", qua)
    paper.setdefault("score_recency", rec)
    paper.setdefault("score_open", op)
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


if __name__ == "__main__":
    unittest.main()
