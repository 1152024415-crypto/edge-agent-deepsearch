#!/usr/bin/env python3
import json
import sys
import tempfile
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock
from urllib import request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # 项目根, for app 包
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))  # agent/, for research_run/publish_results

import publish_results
import research_run
from app import server as server_app


TODAY = date.today()
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()


def _score_dims(score):
    """Return a legal 2-dim breakdown summing to ``score`` (relevance + contribution, each 0-10)."""
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


def write_json(payload):
    tmp = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
    with tmp:
        json.dump(payload, tmp, ensure_ascii=False)
    return Path(tmp.name)


class ResearchRunValidationTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch("research_run.is_link_alive", return_value=True)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_validates_fresh_paper_run(self):
        path = write_json(run_payload(valid_paper()))

        normalized = research_run.load_and_validate(path, today=TODAY)

        self.assertEqual(normalized["run_id"], "run-20260625-120000")
        self.assertEqual(len(normalized["papers"]), 1)
        self.assertEqual(normalized["papers"][0]["id"], "fresh-edge-agent-paper")
        self.assertEqual(normalized["papers"][0]["paper_url"], "https://openreview.net/forum?id=fresh-edge-agent-paper")
        self.assertEqual(normalized["papers"][0]["source_tier"], "学校顶会")
        self.assertEqual(normalized["papers"][0]["tags"], ["方向:端侧agent", "方向:记忆", "方向:评测基准"])

    def test_rejects_old_papers_for_current_week(self):
        path = write_json(run_payload(valid_paper(date="2025-06-17")))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("outside window", str(ctx.exception))

    def test_rejects_invalid_source_tier(self):
        path = write_json(run_payload(valid_paper(source_tier="厂商博客")))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("source_tier", str(ctx.exception))

    def test_rejects_tag_not_in_taxonomy(self):
        path = write_json(run_payload(valid_paper(tags=["方向:不存在"])))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("not in taxonomy", str(ctx.exception))

    def test_rejects_empty_tags(self):
        path = write_json(run_payload(valid_paper(tags=[])))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("tags", str(ctx.exception))

    def test_accepts_official_tier_blog(self):
        path = write_json(
            run_payload(
                valid_paper(
                    source_tier="官方动态",
                    paper_url="https://openai.com/research/example",
                    vendors="OpenAI",
                    score=12,
                    score_reason="Official major vendor source with direct edge-agent relevance.",
                )
            )
        )

        normalized = research_run.load_and_validate(path, today=TODAY)

        self.assertEqual(normalized["papers"][0]["source_tier"], "官方动态")

    def test_rejects_unofficial_vendor_blog(self):
        path = write_json(
            run_payload(
                valid_paper(
                    source_tier="官方动态",
                    paper_url="https://example.com/openai-analysis",
                    vendors="OpenAI",
                )
            )
        )

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("official vendor domain URL", str(ctx.exception))

    def test_company_tier_requires_vendors(self):
        path = write_json(run_payload(valid_paper(source_tier="公司项目", vendors="")))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("requires non-empty vendors", str(ctx.exception))

    def test_oss_tier_requires_github_url(self):
        path = write_json(run_payload(valid_paper(source_tier="开源大项目", paper_url="https://example.com/repo")))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("github.com", str(ctx.exception))

    def test_accepts_school_preprint_tier(self):
        path = write_json(run_payload(valid_paper(source_tier="学校预印本")))
        normalized = research_run.load_and_validate(path, today=TODAY)
        self.assertEqual(normalized["papers"][0]["source_tier"], "学校预印本")


class DeadLinkValidationTests(unittest.TestCase):
    def test_rejects_dead_paper_url(self):
        dead_url = "https://arxiv.org/abs/this-does-not-exist-404-xxx"
        if research_run.is_link_alive(dead_url):
            self.skipTest("network unavailable or URL did not return 404")
        path = write_json(run_payload(valid_paper(paper_url=dead_url)))
        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)
        msg = str(ctx.exception)
        self.assertTrue("dead" in msg or "404" in msg)


class PublishResultsTests(unittest.TestCase):
    def test_posts_validated_payload_to_research_runs_endpoint(self):
        payload = run_payload(valid_paper())
        seen = {}

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b'{"ok": true, "accepted": 1}'

        def fake_urlopen(req, timeout=0):
            seen["url"] = req.full_url
            seen["method"] = req.get_method()
            seen["content_type"] = req.get_header("Content-type")
            seen["payload"] = json.loads(req.data.decode("utf-8"))
            seen["timeout"] = timeout
            return FakeResponse()

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = publish_results.publish_payload("http://example.test", payload)

        self.assertEqual(result["accepted"], 1)
        self.assertEqual(seen["url"], "http://example.test/api/research-runs")
        self.assertEqual(seen["method"], "POST")
        self.assertEqual(seen["content_type"], "application/json")
        self.assertEqual(seen["payload"]["papers"][0]["id"], "fresh-edge-agent-paper")


class ServerApiTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch("research_run.is_link_alive", return_value=True)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_server_accepts_run_and_returns_latest_papers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            httpd = server_app.create_server(("127.0.0.1", 0), Path(tmpdir) / "papers.sqlite")
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{httpd.server_port}"
                payload = research_run.validate_payload(run_payload(valid_paper(score=14)), today=TODAY)

                publish_result = publish_results.publish_payload(base_url, payload)
                with request.urlopen(f"{base_url}/api/papers", timeout=5) as resp:
                    papers_result = json.loads(resp.read().decode("utf-8"))
            finally:
                httpd.shutdown()
                thread.join(timeout=5)
                httpd.server_close()

        self.assertEqual(publish_result["accepted"], 1)
        self.assertEqual(len(papers_result["papers"]), 1)
        self.assertEqual(papers_result["papers"][0]["id"], "fresh-edge-agent-paper")
        self.assertEqual(papers_result["papers"][0]["score"], 14)
        self.assertEqual(papers_result["papers"][0]["source_tier"], "学校顶会")
        self.assertEqual(papers_result["papers"][0]["tags"], ["方向:端侧agent", "方向:记忆", "方向:评测基准"])

    def test_server_lists_only_latest_research_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            httpd = server_app.create_server(("127.0.0.1", 0), Path(tmpdir) / "papers.sqlite")
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{httpd.server_port}"
                old_payload = research_run.validate_payload(
                    {
                        **run_payload(valid_paper(id="old-paper", title="Old Paper", score=10)),
                        "run_id": "run-20260625-old",
                    },
                    today=TODAY,
                )
                new_payload = research_run.validate_payload(
                    {
                        **run_payload(valid_paper(id="new-paper", title="New Paper", score=16)),
                        "run_id": "run-20260625-new",
                    },
                    today=TODAY,
                )

                publish_results.publish_payload(base_url, old_payload)
                publish_results.publish_payload(base_url, new_payload)
                with request.urlopen(f"{base_url}/api/papers", timeout=5) as resp:
                    papers_result = json.loads(resp.read().decode("utf-8"))
            finally:
                httpd.shutdown()
                thread.join(timeout=5)
                httpd.server_close()

        self.assertEqual([paper["id"] for paper in papers_result["papers"]], ["new-paper"])

    def test_server_sorts_official_tier_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            httpd = server_app.create_server(("127.0.0.1", 0), Path(tmpdir) / "papers.sqlite")
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{httpd.server_port}"
                payload = research_run.validate_payload(
                    run_payload(
                        valid_paper(id="academic-high-score", score=16),
                        valid_paper(
                            id="official-vendor-lower-score",
                            title="Official Vendor Update",
                            source_tier="官方动态",
                            paper_url="https://openai.com/research/example",
                            vendors="OpenAI",
                            score=10,
                            score_reason="Official major vendor source.",
                        ),
                    ),
                    today=TODAY,
                )

                publish_results.publish_payload(base_url, payload)
                with request.urlopen(f"{base_url}/api/papers", timeout=5) as resp:
                    papers_result = json.loads(resp.read().decode("utf-8"))
            finally:
                httpd.shutdown()
                thread.join(timeout=5)
                httpd.server_close()

        self.assertEqual(papers_result["papers"][0]["id"], "official-vendor-lower-score")
        self.assertEqual(papers_result["papers"][0]["source_tier"], "官方动态")


if __name__ == "__main__":
    unittest.main()
