#!/usr/bin/env python3
import json
import sys
import tempfile
import threading
import unittest
from datetime import date
from pathlib import Path
from unittest import mock
from urllib import request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # 项目根, for app 包
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))  # agent/, for research_run/publish_results

import publish_results
import research_run
from app import server as server_app


TODAY = date(2026, 6, 25)


def _score_dims(score):
    """Return a legal 5-dim breakdown summing to ``score`` (relevance/vendor/contribution/quality/recency)."""
    rec = min(5, max(0, score))
    rem = score - rec
    rel = min(35, rem)
    rem -= rel
    ven = min(25, rem)
    rem -= ven
    con = min(20, rem)
    rem -= con
    qua = min(15, rem)
    return rel, ven, con, qua, rec


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
    rel, ven, con, qua, rec = _score_dims(paper["score"])
    paper.setdefault("score_relevance", rel)
    paper.setdefault("score_vendor", ven)
    paper.setdefault("score_contribution", con)
    paper.setdefault("score_quality", qua)
    paper.setdefault("score_recency", rec)
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
        self.assertEqual(normalized["papers"][0]["paper_url"], "https://arxiv.org/abs/2606.12345")
        self.assertEqual(normalized["papers"][0]["category"], "应用")
        self.assertEqual(normalized["papers"][0]["keywords"], ["GUI智能体", "端侧部署", "评测基准"])

    def test_rejects_old_papers_for_current_week(self):
        path = write_json(run_payload(valid_paper(date="2025-06-17")))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("outside window", str(ctx.exception))

    def test_rejects_non_paper_sources(self):
        path = write_json(run_payload(valid_paper(source_type="厂商博客")))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("source_type", str(ctx.exception))

    def test_rejects_invalid_category(self):
        path = write_json(run_payload(valid_paper(category="产品")))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("category", str(ctx.exception))

    def test_rejects_empty_keywords(self):
        path = write_json(run_payload(valid_paper(keywords=[])))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("keywords", str(ctx.exception))

    def test_accepts_official_major_vendor_blog(self):
        path = write_json(
            run_payload(
                valid_paper(
                    source_type="官方技术博客",
                    paper_url="https://openai.com/research/example",
                    is_major_vendor_official=True,
                    vendors="OpenAI",
                    score=99,
                    score_reason="Official major vendor source with direct edge-agent relevance.",
                )
            )
        )

        normalized = research_run.load_and_validate(path, today=TODAY)

        self.assertTrue(normalized["papers"][0]["is_major_vendor_official"])
        self.assertEqual(normalized["papers"][0]["source_type"], "官方技术博客")

    def test_rejects_unofficial_vendor_blog(self):
        path = write_json(
            run_payload(
                valid_paper(
                    source_type="官方技术博客",
                    paper_url="https://example.com/openai-analysis",
                    is_major_vendor_official=True,
                    vendors="OpenAI",
                )
            )
        )

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("official vendor URL", str(ctx.exception))


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
                payload = research_run.validate_payload(run_payload(valid_paper(score=88)), today=TODAY)

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
        self.assertEqual(papers_result["papers"][0]["score"], 88)
        self.assertEqual(papers_result["papers"][0]["category"], "应用")
        self.assertEqual(papers_result["papers"][0]["keywords"], ["GUI智能体", "端侧部署", "评测基准"])

    def test_server_lists_only_latest_research_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            httpd = server_app.create_server(("127.0.0.1", 0), Path(tmpdir) / "papers.sqlite")
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{httpd.server_port}"
                old_payload = research_run.validate_payload(
                    {
                        **run_payload(valid_paper(id="old-paper", title="Old Paper", score=70)),
                        "run_id": "run-20260625-old",
                    },
                    today=TODAY,
                )
                new_payload = research_run.validate_payload(
                    {
                        **run_payload(valid_paper(id="new-paper", title="New Paper", score=90)),
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

    def test_server_sorts_official_major_vendor_items_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            httpd = server_app.create_server(("127.0.0.1", 0), Path(tmpdir) / "papers.sqlite")
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{httpd.server_port}"
                payload = research_run.validate_payload(
                    run_payload(
                        valid_paper(id="academic-high-score", score=99),
                        valid_paper(
                            id="official-vendor-lower-score",
                            title="Official Vendor Update",
                            source_type="官方技术博客",
                            paper_url="https://openai.com/research/example",
                            is_major_vendor_official=True,
                            vendors="OpenAI",
                            score=80,
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
        self.assertTrue(papers_result["papers"][0]["is_major_vendor_official"])


if __name__ == "__main__":
    unittest.main()
