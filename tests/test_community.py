#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.community import CommunityValidationError, load_community, validate_community


TODAY = date(2026, 8, 13)
COMMUNITY_SOURCES = (
    "X",
    "Bluesky",
    "Reddit",
    "Hacker News",
    "Mastodon",
    "GitHub Discussions",
    "Hugging Face",
    "YouTube / Bilibili",
    "厂商论坛",
)


def valid_payload():
    return {
        "window": {"start": "2026-08-07", "end": "2026-08-13"},
        "coverage": [
            {
                "source": source,
                "status": "limited" if source == "X" else ("found" if source == "Reddit" else "no_match"),
                "note": "已完成公开来源检索并记录结果",
            }
            for source in COMMUNITY_SOURCES
        ],
        "items": [
            {
                "id": "reddit-nemotron-spark",
                "source": "Reddit",
                "author": "r/LocalLLM",
                "url": "https://www.reddit.com/r/LocalLLM/comments/example/",
                "published_at": "2026-08-11T12:00:00Z",
                "title_zh": "Nemotron 3.5 单机实测",
                "summary_zh": "社区在单台 DGX Spark 上验证模型的推理速度与工具调用表现。",
                "why_it_matters": "它补充了官方发布没有给出的本地 Agent 实际运行反馈。",
                "device_scope": "PC",
                "topic": "Agent",
                "verification": "已回链原始材料",
                "evidence_url": "https://blogs.nvidia.com/blog/example/",
            }
        ],
    }


class CommunityValidationTests(unittest.TestCase):
    def test_accepts_and_sorts_valid_items_by_device_then_time(self):
        payload = valid_payload()
        second = dict(payload["items"][0])
        second.update({"id": "mobile", "device_scope": "手机", "published_at": "2026-08-10T10:00:00Z"})
        payload["items"].append(second)

        result = validate_community(payload, today=TODAY)

        self.assertEqual([item["id"] for item in result["items"]], ["mobile", "reddit-nemotron-spark"])
        self.assertEqual({record["source"] for record in result["coverage"]}, set(COMMUNITY_SOURCES))

    def test_rejects_unknown_source_device_and_verification(self):
        for field, value in [
            ("source", "博客"),
            ("device_scope", "云端"),
            ("verification", "可信"),
        ]:
            with self.subTest(field=field):
                payload = valid_payload()
                payload["items"][0][field] = value
                with self.assertRaises(CommunityValidationError):
                    validate_community(payload, today=TODAY)

    def test_rejects_missing_chinese_editorial_fields(self):
        for field in ["title_zh", "summary_zh", "why_it_matters"]:
            with self.subTest(field=field):
                payload = valid_payload()
                payload["items"][0][field] = "English only"
                with self.assertRaises(CommunityValidationError):
                    validate_community(payload, today=TODAY)

    def test_rejects_non_http_url_and_out_of_window_date(self):
        payload = valid_payload()
        payload["items"][0]["url"] = "javascript:alert(1)"
        with self.assertRaises(CommunityValidationError):
            validate_community(payload, today=TODAY)

        payload = valid_payload()
        payload["items"][0]["published_at"] = "2026-08-06T23:59:59Z"
        with self.assertRaises(CommunityValidationError):
            validate_community(payload, today=TODAY)

    def test_limited_coverage_requires_an_explanation(self):
        payload = valid_payload()
        payload["coverage"][0]["note"] = ""

        with self.assertRaises(CommunityValidationError):
            validate_community(payload, today=TODAY)

    def test_load_missing_file_returns_explicit_empty_coverage(self):
        result = load_community(Path("missing-community.json"), today=TODAY)

        self.assertEqual(result["items"], [])
        self.assertEqual(result["coverage"][0]["status"], "unavailable")

    def test_load_reads_and_validates_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "community.json"
            path.write_text(json.dumps(valid_payload(), ensure_ascii=False), encoding="utf-8")

            result = load_community(path, today=TODAY)

        self.assertEqual(result["items"][0]["id"], "reddit-nemotron-spark")


if __name__ == "__main__":
    unittest.main()
