#!/usr/bin/env python3
import json
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path
from unittest import mock
from urllib import request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # 项目根, for app 包
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))  # agent/, for research_run/publish_results

import publish_results
import research_run
import build_run_week
from app import server as server_app
from app import storage as storage_app


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
        "title_zh": "",
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
        "recommendation": "纳入",
        "recommendation_reason": "",
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
        self.assertEqual(normalized["papers"][0]["title_zh"], "")

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

    def test_rejects_english_only_reader_summary(self):
        path = write_json(run_payload(valid_paper(abstract="An English-only abstract about edge AI.")))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("abstract", str(ctx.exception))
        self.assertIn("中文", str(ctx.exception))

    def test_recommended_paper_requires_chinese_recommendation_reason(self):
        path = write_json(run_payload(valid_paper(
            title_zh="端侧智能体规划框架",
            recommendation="推荐",
            recommendation_reason="",
        )))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("recommendation_reason", str(ctx.exception))

    def test_rejects_internal_placeholder_in_recommendation_reason(self):
        path = write_json(run_payload(valid_paper(
            title_zh="端侧智能体规划框架",
            recommendation="推荐",
            recommendation_reason="auto-converted；中文精修待后续补",
        )))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("recommendation_reason", str(ctx.exception))
        self.assertIn("内部占位", str(ctx.exception))

    def test_preserves_valid_chinese_recommendation_reason(self):
        reason = "直接解决端侧智能体的延迟与内存瓶颈，且给出了真实设备上的量化结果。"
        path = write_json(run_payload(valid_paper(
            title_zh="端侧智能体规划框架",
            recommendation="推荐",
            recommendation_reason=reason,
        )))

        normalized = research_run.load_and_validate(path, today=TODAY)

        self.assertEqual(normalized["papers"][0]["recommendation_reason"], reason)

    def test_recommended_paper_requires_short_chinese_title(self):
        path = write_json(run_payload(valid_paper(
            recommendation="推荐",
            recommendation_reason="端侧收益明确，而且给出了真实设备上的验证结果。",
            title_zh="",
        )))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("title_zh", str(ctx.exception))

    def test_rejects_abstract_used_as_chinese_title(self):
        abstract = "这项工作让端侧智能体在手机本地完成规划与执行。"
        path = write_json(run_payload(valid_paper(
            abstract=abstract,
            title_zh=abstract,
            recommendation="推荐",
            recommendation_reason="端侧收益明确，而且给出了真实设备上的验证结果。",
        )))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("title_zh", str(ctx.exception))

    def test_preserves_valid_short_chinese_title(self):
        title_zh = "端侧智能体规划框架"
        path = write_json(run_payload(valid_paper(
            title_zh=title_zh,
            recommendation="推荐",
            recommendation_reason="端侧收益明确，而且给出了真实设备上的验证结果。",
        )))

        normalized = research_run.load_and_validate(path, today=TODAY)

        self.assertEqual(normalized["papers"][0]["title_zh"], title_zh)


class BuildRunDefaultsTests(unittest.TestCase):
    def test_automatic_converters_never_promote_by_keyword(self):
        common_title = "On-Device Edge Agent with KV Cache Compression"
        converted = [
            build_run_week.convert_arxiv({
                "id": "2608.00001",
                "title": common_title,
                "abstract": "An on-device agent compresses its KV cache for mobile inference.",
                "authors": "Example University",
                "date": YESTERDAY,
            }),
            build_run_week.convert_hf({
                "id": "hf-edge",
                "title": common_title,
                "abstract": "An on-device agent compresses its KV cache for mobile inference.",
                "paper_url": "https://huggingface.co/papers/edge-agent",
                "date": YESTERDAY,
            }, set()),
            build_run_week.convert_github({
                "repo": "example/edge-agent",
                "tag": "v1.0.0",
                "title": common_title,
                "summary": "On-device agent inference release.",
                "release_url": "https://github.com/example/edge-agent/releases/tag/v1.0.0",
                "date": YESTERDAY,
            }),
            build_run_week.convert_vendor({
                "vendor": "Qualcomm",
                "title": common_title,
                "summary": "On-device agent inference update.",
                "url": "https://www.qualcomm.com/example",
                "date": YESTERDAY,
            }),
        ]

        for paper in converted:
            with self.subTest(source=paper["source_tier"]):
                self.assertEqual(paper["recommendation"], "纳入")
                self.assertEqual(paper["recommendation_reason"], "")
                self.assertEqual(paper["title_zh"], "")


class StorageMigrationTests(unittest.TestCase):
    def test_legacy_database_adds_recommendation_reason_without_losing_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "legacy.sqlite"
            storage_app.init_db(db_path)
            storage_app.upsert_run(
                db_path,
                research_run.validate_payload(run_payload(valid_paper()), today=TODAY, skip_network=True),
            )
            with closing(sqlite3.connect(db_path)) as conn:
                conn.execute("ALTER TABLE papers DROP COLUMN recommendation_reason")
                conn.commit()
                columns_before = {row[1] for row in conn.execute("PRAGMA table_info(papers)")}
            self.assertNotIn("recommendation_reason", columns_before)

            storage_app.init_db(db_path)

            migrated = storage_app.get_paper(db_path, "fresh-edge-agent-paper")
            self.assertIsNotNone(migrated)
            self.assertEqual(migrated["title"], "Fresh Edge Agent Paper")
            self.assertEqual(migrated["recommendation_reason"], "")

    def test_legacy_database_adds_title_zh_without_losing_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "legacy.sqlite"
            storage_app.init_db(db_path)
            storage_app.upsert_run(
                db_path,
                research_run.validate_payload(run_payload(valid_paper()), today=TODAY, skip_network=True),
            )
            with closing(sqlite3.connect(db_path)) as conn:
                columns_before = {row[1] for row in conn.execute("PRAGMA table_info(papers)")}
                if "title_zh" in columns_before:
                    conn.execute("ALTER TABLE papers DROP COLUMN title_zh")
                    conn.commit()
                columns_before = {row[1] for row in conn.execute("PRAGMA table_info(papers)")}
            self.assertNotIn("title_zh", columns_before)

            storage_app.init_db(db_path)

            migrated = storage_app.get_paper(db_path, "fresh-edge-agent-paper")
            self.assertIsNotNone(migrated)
            self.assertEqual(migrated["title"], "Fresh Edge Agent Paper")
            self.assertEqual(migrated["title_zh"], "")


class AutoDeployGateTests(unittest.TestCase):
    def test_ghpages_deploy_stops_when_release_gate_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "site").mkdir()
            calls = []

            def fake_run(command, **_kwargs):
                calls.append(command)
                if any(str(part).endswith("gate_all.py") for part in command):
                    return subprocess.CompletedProcess(command, 1, stdout="gate failed", stderr="")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            with mock.patch.object(server_app, "ROOT", root), \
                    mock.patch("app.server.subprocess.run", side_effect=fake_run):
                server_app._deploy_to_ghpages()

        self.assertTrue(any(any(str(part).endswith("gate_all.py") for part in cmd) for cmd in calls))
        self.assertFalse(any(cmd and cmd[0] == "git" for cmd in calls), calls)


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
                reason = "端侧收益明确，并在真实设备上报告了延迟改善，值得优先阅读。"
                title_zh = "端侧智能体规划框架"
                payload = research_run.validate_payload(run_payload(valid_paper(
                    score=14,
                    title_zh=title_zh,
                    recommendation="推荐",
                    recommendation_reason=reason,
                )), today=TODAY)

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
        self.assertEqual(papers_result["papers"][0]["title_zh"], title_zh)
        self.assertEqual(papers_result["papers"][0]["recommendation_reason"], reason)

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
