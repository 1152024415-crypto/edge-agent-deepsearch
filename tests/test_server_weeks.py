#!/usr/bin/env python3
"""Server routes for week archive browsing."""
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agent"))

from app import server as server_app
from app import weeks as weeks_mod


class ServerWeeksTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        db_path = Path(self._tmp.name) / "papers.sqlite"
        # redirect weeks dir into tmp so tests don't touch real data/weeks
        self._orig_wd = weeks_mod.WEEKS_DIR
        weeks_mod.WEEKS_DIR = Path(self._tmp.name) / "weeks"
        self.addCleanup(self._restore)

        self.httpd = server_app.create_server(("127.0.0.1", 0), db_path)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_port}"
        self.addCleanup(self._stop)

    def _restore(self):
        weeks_mod.WEEKS_DIR = self._orig_wd

    def _stop(self):
        self.httpd.shutdown()
        self.thread.join(timeout=5)
        self.httpd.server_close()

    def _get(self, path):
        import urllib.request
        with urllib.request.urlopen(self.base_url + path, timeout=10) as r:
            return r.read().decode("utf-8")

    def _seed(self):
        meta = {"label": "2026-06-26", "title": "06-26~07-03",
                "range": {"start": "2026-06-26", "end": "2026-07-03"}}
        weeks_mod.write_archive(meta, [{"id": "p1"}], {"overview": "ov(06-26~07-03)"}, {"items": []})
        weeks_mod.build_manifest("2026-07-02")  # current is some other week

    def test_api_weeks_returns_manifest(self):
        self._seed()
        body = self._get("/api/weeks")
        m = json.loads(body)["weeks"]
        self.assertEqual(m[0]["label"], "2026-06-26")
        self.assertFalse(m[0]["current"])  # current is 2026-07-02 which has no archive

    def test_week_route_serves_frozen_page(self):
        self._seed()
        html = self._get("/week/2026-06-26")
        self.assertIn("window.__PAPERS__", html)
        self.assertIn('"p1"', html)
        # render_page inlines window.__WEEK_LABEL__=<json> (no spaces around =)
        self.assertIn('window.__WEEK_LABEL__="2026-06-26"', html)
        # frozen: fetches rewritten to globals
        self.assertNotIn('fetch("/api/papers")', html)
        # runtime: paper links stay absolute (/paper/<id>), NOT rewritten to relative
        self.assertIn('href="/paper/', html)
        self.assertNotIn('href="paper/', html)

    def test_week_route_404_for_unknown(self):
        try:
            self._get("/week/nope")
            self.fail("expected 404")
        except Exception as e:
            self.assertIn("404", str(e))

    def test_root_injects_weeks_global(self):
        self._seed()
        html = self._get("/")
        self.assertIn("window.__WEEKS__", html)


if __name__ == "__main__":
    unittest.main()
