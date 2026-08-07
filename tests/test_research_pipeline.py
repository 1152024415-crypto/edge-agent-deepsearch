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
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # 项目根, for app 包
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))  # agent/, for research_run/publish_results

import publish_results
import research_run
import research_collection
import build_run_week
from app import server as server_app
from app import storage as storage_app


TODAY = date.today()
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()
TEST_PUBLISH_TOKEN = "test-publish-secret"
_TEST_ARTIFACT_DIRS = []


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
        "tags": ["方向:高效推理", "方向:记忆", "方向:评测基准"],
        "edge_agent_scope": "非端侧Agent",
        "edge_agent_evidence": "",
        "recommendation": "纳入",
        "recommendation_reason": "",
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
    return {
        "run_id": "run-20260625-120000",
        "generated_at": "2026-06-25T12:00:00+08:00",
        "papers": list(papers),
    }


def collection_manifest(artifact_paths, today=TODAY):
    start, end, days = research_collection.collection_window(today)
    attestations = {
        source: research_collection.candidate_artifact_attestation(path, source)
        for source, path in artifact_paths.items()
    }
    return {
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "sources": {
            "arxiv": {
                "status": "complete",
                "candidate_count": 0,
                **attestations["arxiv"],
                "queries_completed": sorted(research_collection.REQUIRED_ARXIV_SWEEPS),
                "pages_fetched": len(research_collection.REQUIRED_ARXIV_SWEEPS),
            },
            "huggingface": {
                "status": "complete",
                "candidate_count": 0,
                **attestations["huggingface"],
                "dates_checked": [day.isoformat() for day in days],
            },
            "github": {
                "status": "complete",
                "candidate_count": 0,
                **attestations["github"],
                "release_projects_checked": sorted(research_collection.REQUIRED_GITHUB_PROJECTS),
                "trending_checked": True,
            },
            "vendors": {
                "status": "complete",
                "candidate_count": 0,
                **attestations["vendors"],
                "vendors_checked": sorted(research_collection.REQUIRED_VENDOR_SOURCES),
                "vendor_checks": {
                    vendor: {"status": "no_match", "sources_succeeded": ["official-index"]}
                    for vendor in research_collection.REQUIRED_VENDOR_SOURCES
                },
            },
        },
    }


def covered_run_payload(*papers):
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
    for source in ("arxiv", "huggingface", "github", "vendors"):
        path = artifact_dir / f"{source}.json"
        path.write_text(
            json.dumps(candidates if source == "huggingface" else [], ensure_ascii=False),
            encoding="utf-8",
        )
        artifact_paths[source] = path
    payload = run_payload(*normalized_papers)
    payload["collection_manifest"] = collection_manifest(artifact_paths)
    return payload


def covered_github_run_payload(paper, candidate):
    tempdir = tempfile.TemporaryDirectory()
    _TEST_ARTIFACT_DIRS.append(tempdir)
    artifact_dir = Path(tempdir.name)
    artifact_paths = {}
    for source in ("arxiv", "huggingface", "github", "vendors"):
        path = artifact_dir / f"{source}.json"
        path.write_text(
            json.dumps([candidate] if source == "github" else [], ensure_ascii=False),
            encoding="utf-8",
        )
        artifact_paths[source] = path
    normalized = dict(paper)
    normalized["candidate_source"] = "github"
    normalized["candidate_ref"] = research_collection.candidate_record_ref(candidate)
    payload = run_payload(normalized)
    payload["collection_manifest"] = collection_manifest(artifact_paths)
    return payload


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
        self.assertEqual(normalized["papers"][0]["tags"], ["方向:高效推理", "方向:记忆", "方向:评测基准"])
        self.assertEqual(normalized["papers"][0]["title_zh"], "")

    def test_rejects_unreviewed_edge_agent_scope(self):
        path = write_json(run_payload(valid_paper(edge_agent_scope="待核实")))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("edge_agent_scope", str(ctx.exception))
        self.assertIn("待核实", str(ctx.exception))

    def test_direct_phone_agent_must_be_recommended(self):
        path = write_json(run_payload(valid_paper(
            edge_agent_scope="手机",
            edge_agent_evidence="论文明确说明规划、记忆和工具调用均在手机本地运行。",
            tags=["方向:端侧agent", "方向:工具调用", "硬件:手机"],
            score_relevance=10,
            score_contribution=4,
            recommendation="纳入",
        )))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("真正端侧 Agent", str(ctx.exception))
        self.assertIn("推荐", str(ctx.exception))

    def test_direct_edge_agent_requires_evidence_tag_and_high_relevance(self):
        cases = [
            {"edge_agent_evidence": ""},
            {"tags": ["方向:高效推理", "硬件:手机"]},
            {"score": 11, "score_relevance": 7, "score_contribution": 4},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                direct_values = {
                    "title_zh": "手机本地助理",
                    "edge_agent_scope": "手机",
                    "edge_agent_evidence": "论文明确说明规划和工具调用在手机本地执行。",
                    "tags": ["方向:端侧agent", "方向:工具调用", "硬件:手机"],
                    "recommendation": "推荐",
                    "recommendation_reason": "关键智能体闭环在手机本地运行，直接符合本周核心方向。",
                }
                direct_values.update(overrides)
                paper = valid_paper(
                    **direct_values,
                )
                path = write_json(run_payload(paper))

                with self.assertRaises(research_run.ValidationError):
                    research_run.load_and_validate(path, today=TODAY)

    def test_non_edge_agent_cannot_use_direct_edge_agent_tag(self):
        path = write_json(run_payload(valid_paper(
            edge_agent_scope="非端侧Agent",
            tags=["方向:端侧agent", "方向:高效推理"],
        )))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("方向:端侧agent", str(ctx.exception))

    def test_preserves_verified_phone_agent_classification(self):
        path = write_json(run_payload(valid_paper(
            title_zh="手机本地助理",
            edge_agent_scope="手机",
            edge_agent_evidence="论文明确说明规划、记忆和工具调用均在手机本地运行。",
            tags=["方向:端侧agent", "方向:工具调用", "硬件:手机"],
            score=18,
            score_relevance=10,
            score_contribution=8,
            recommendation="推荐",
            recommendation_reason="手机本地形成完整智能体闭环，直接符合本周核心方向。",
        )))

        normalized = research_run.load_and_validate(path, today=TODAY)

        self.assertEqual(normalized["papers"][0]["edge_agent_scope"], "手机")
        self.assertIn("手机本地", normalized["papers"][0]["edge_agent_evidence"])

    def test_accepts_arxiv_revision_date_when_updated_metadata_matches(self):
        paper = valid_paper(
            paper_url="https://arxiv.org/abs/2505.09606",
            date=TODAY.isoformat(),
            arxiv_date_basis="updated",
            arxiv_revision_note="本周修订扩大了双语用户实验，并更新主要结果和公开代码说明。",
        )
        path = write_json(run_payload(paper))

        with mock.patch("research_run.fetch_arxiv_dates", return_value=(date(2026, 5, 14), TODAY), create=True), mock.patch(
            "research_run.fetch_arxiv_published_date", return_value=date(2026, 5, 14)
        ):
            normalized = research_run.load_and_validate(path, today=TODAY)

        self.assertEqual(normalized["papers"][0]["arxiv_date_basis"], "updated")

    def test_rejects_arxiv_revision_without_meaningful_change_note(self):
        paper = valid_paper(
            paper_url="https://arxiv.org/abs/2505.09606",
            date=TODAY.isoformat(),
            arxiv_date_basis="updated",
            arxiv_revision_note="",
        )
        path = write_json(run_payload(paper))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("arxiv_revision_note", str(ctx.exception))

    def test_rejects_old_papers_for_current_week(self):
        path = write_json(run_payload(valid_paper(date="2025-06-17")))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("outside window", str(ctx.exception))

    def test_seven_day_window_contains_exactly_seven_calendar_dates(self):
        seven_days_ago = (TODAY - timedelta(days=7)).isoformat()
        path = write_json(run_payload(valid_paper(date=seven_days_ago)))

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

    def test_company_tier_requires_affiliation_evidence_url(self):
        path = write_json(
            run_payload(
                valid_paper(
                    source_tier="公司项目",
                    vendors="OpenAI",
                    affiliation_evidence_url="",
                )
            )
        )

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("affiliation_evidence_url", str(ctx.exception))

    def test_company_tier_rejects_non_scholarly_affiliation_evidence(self):
        path = write_json(
            run_payload(
                valid_paper(
                    source_tier="公司项目",
                    vendors="OpenAI",
                    affiliation_evidence_url="https://example.com/",
                )
            )
        )

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("authoritative affiliation evidence", str(ctx.exception))

    def test_company_tier_accepts_authoritative_affiliation_evidence(self):
        path = write_json(
            run_payload(
                valid_paper(
                    source_tier="公司项目",
                    vendors="OpenAI",
                    affiliation_evidence_url="https://arxiv.org/pdf/2608.00001",
                    score_reason="论文 PDF 作者机构页明确列出 OpenAI。",
                )
            )
        )

        normalized = research_run.load_and_validate(path, today=TODAY)

        self.assertEqual(normalized["papers"][0]["vendors"], "OpenAI")

    def test_server_validation_rejects_run_paper_without_candidate_lineage(self):
        payload = covered_run_payload(valid_paper())
        payload["papers"][0]["candidate_ref"] = "not-in-candidates"

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.validate_payload(
                payload,
                today=TODAY,
                skip_network=True,
                require_collection_manifest=True,
            )

        self.assertIn("candidate_ref", str(ctx.exception))

    def test_server_validation_rejects_reused_candidate_lineage(self):
        payload = covered_run_payload(valid_paper())
        duplicate = dict(payload["papers"][0])
        duplicate["id"] = "second-paper-from-same-candidate"
        payload["papers"].append(duplicate)

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.validate_payload(
                payload,
                today=TODAY,
                skip_network=True,
                require_collection_manifest=True,
            )

        self.assertIn("reused", str(ctx.exception))

    def test_server_validation_rejects_candidate_identity_mismatch(self):
        payload = covered_run_payload(valid_paper())
        payload["papers"][0]["title"] = "Unrelated replacement title"

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.validate_payload(
                payload,
                today=TODAY,
                skip_network=True,
                require_collection_manifest=True,
            )

        self.assertIn("identity", str(ctx.exception))

    def test_server_validation_rejects_candidate_date_mismatch(self):
        payload = covered_run_payload(valid_paper())
        payload["papers"][0]["date"] = TODAY.isoformat()

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.validate_payload(
                payload,
                today=TODAY,
                skip_network=True,
                require_collection_manifest=True,
            )

        self.assertIn("identity", str(ctx.exception))

    def test_company_tier_requires_evidence_for_every_declared_vendor(self):
        path = write_json(
            run_payload(
                valid_paper(
                    source_tier="公司项目",
                    vendors="OpenAI, Huawei",
                    affiliation_evidence_url="https://arxiv.org/pdf/2608.00001",
                    score_reason="论文 PDF 作者机构页明确列出 OpenAI。",
                )
            )
        )

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("Huawei", str(ctx.exception))

    def test_company_tier_does_not_skip_short_vendor_names(self):
        path = write_json(
            run_payload(
                valid_paper(
                    source_tier="公司项目",
                    vendors="JD",
                    affiliation_evidence_url="https://arxiv.org/pdf/2608.00001",
                    score_reason="论文 PDF 作者机构页给出了公司署名。",
                )
            )
        )

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("JD", str(ctx.exception))

    def test_company_tier_rejects_separator_only_vendors(self):
        path = write_json(
            run_payload(
                valid_paper(
                    source_tier="公司项目",
                    vendors=",,",
                    affiliation_evidence_url="https://arxiv.org/pdf/2608.00001",
                    score_reason="论文 PDF 作者机构页给出了公司署名。",
                )
            )
        )

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("vendors", str(ctx.exception))

    def test_oss_tier_requires_github_url(self):
        path = write_json(run_payload(valid_paper(source_tier="开源大项目", paper_url="https://example.com/repo")))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("github.com", str(ctx.exception))

    def test_server_rejects_non_whitelisted_github_candidate(self):
        candidate = {
            "repo": "unknown-user/tiny-edge-demo",
            "tag": "v1.0.0",
            "title": "Tiny Edge Demo",
            "summary": "An on-device AI demo.",
            "release_url": "https://github.com/unknown-user/tiny-edge-demo/releases/tag/v1.0.0",
            "date": YESTERDAY,
        }
        payload = covered_github_run_payload(
            valid_paper(
                title=candidate["title"],
                paper_url=candidate["release_url"],
                date=candidate["date"],
                source_tier="学校顶会",
            ),
            candidate,
        )

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.validate_payload(
                payload,
                today=TODAY,
                skip_network=True,
                require_collection_manifest=True,
            )

        self.assertIn("GitHub", str(ctx.exception))

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

    def test_rejects_pipeline_status_in_reader_facing_score_reason(self):
        path = write_json(run_payload(valid_paper(
            score_reason="自动初评为端侧技术栈候选；主 Agent 根据原文待复核。",
        )))

        with self.assertRaises(research_run.ValidationError) as ctx:
            research_run.load_and_validate(path, today=TODAY)

        self.assertIn("score_reason", str(ctx.exception))
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
    def test_company_detection_uses_affiliation_evidence_not_model_mentions(self):
        converted = build_run_week.convert_arxiv({
            "id": "2608.00078",
            "title": "Qwen Quantization for Mobile Inference",
            "abstract": "We deploy Qwen with an NVIDIA-compatible runtime.",
            "authors": "Alice Example; Bob Example",
            "date": YESTERDAY,
        })

        self.assertIsNotNone(converted)
        self.assertEqual(converted["source_tier"], "学校预印本")
        self.assertEqual(converted["vendors"], "")

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
                "repo": "pytorch/executorch",
                "tag": "v1.0.0",
                "title": common_title,
                "summary": "On-device agent inference release.",
                "release_url": "https://github.com/pytorch/executorch/releases/tag/v1.0.0",
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
                self.assertEqual(paper["edge_agent_scope"], "待核实")
                self.assertEqual(paper["edge_agent_evidence"], "")
                self.assertNotIn("方向:端侧agent", paper["tags"])

    def test_github_repo_url_is_not_used_as_company_affiliation_evidence(self):
        converted = build_run_week.convert_github({
            "repo": "pytorch/executorch",
            "tag": "v1.0.0",
            "title": "Edge AI Runtime Release",
            "summary": "An on-device AI inference runtime.",
            "release_url": "https://github.com/pytorch/executorch/releases/tag/v1.0.0",
            "date": YESTERDAY,
            "tier": "公司项目",
            "vendor": "Meta",
        })

        self.assertIsNotNone(converted)
        self.assertEqual(converted["source_tier"], "开源大项目")
        self.assertEqual(converted["affiliation_evidence_url"], "")

    def test_unknown_github_repo_is_not_assembled_into_weekly_run(self):
        converted = build_run_week.convert_github({
            "repo": "unknown-user/tiny-edge-demo",
            "tag": "v1.0.0",
            "title": "Tiny Edge Demo",
            "summary": "An on-device AI inference demo.",
            "release_url": "https://github.com/unknown-user/tiny-edge-demo/releases/tag/v1.0.0",
            "date": YESTERDAY,
            "tier": "学校顶会",
        })

        self.assertIsNone(converted)


class StorageMigrationTests(unittest.TestCase):
    def test_storage_schema_adds_edge_agent_classification_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "papers.sqlite"

            storage_app.init_db(db_path)

            with closing(sqlite3.connect(db_path)) as conn:
                columns = {row[1] for row in conn.execute("PRAGMA table_info(papers)")}
            self.assertIn("edge_agent_scope", columns)
            self.assertIn("edge_agent_evidence", columns)
            self.assertIn("arxiv_date_basis", columns)
            self.assertIn("arxiv_revision_note", columns)

    def test_list_prioritizes_phone_pc_and_other_edge_agents_before_other_recommendations(self):
        reason = "设备端形成了可核验的智能体闭环，直接符合本周核心方向。"
        papers = [
            valid_paper(
                id="official-non-edge", title="Official Infrastructure", title_zh="官方智能体基础设施",
                paper_url="https://www.qualcomm.com/example", source_tier="官方动态",
                recommendation="推荐", recommendation_reason="官方发布有实际工程价值，值得本周关注。",
            ),
            valid_paper(
                id="other-edge", title="Robot Agent", title_zh="机器人本地智能体",
                edge_agent_scope="其他端侧", edge_agent_evidence="感知、规划和行动闭环运行在机器人本地计算单元。",
                tags=["方向:端侧agent", "应用:机器人", "硬件:Jetson"],
                score=16, score_relevance=9, score_contribution=7,
                recommendation="推荐", recommendation_reason=reason,
            ),
            valid_paper(
                id="pc-edge", title="PC Agent", title_zh="电脑本地智能体",
                edge_agent_scope="PC", edge_agent_evidence="规划、记忆和工具执行均在个人电脑本地完成。",
                tags=["方向:端侧agent", "方向:工具调用", "硬件:CPU"],
                score=16, score_relevance=9, score_contribution=7,
                recommendation="推荐", recommendation_reason=reason,
            ),
            valid_paper(
                id="phone-edge", title="Phone Agent", title_zh="手机本地智能体",
                edge_agent_scope="手机", edge_agent_evidence="规划、记忆和工具执行均在手机本地完成。",
                tags=["方向:端侧agent", "方向:工具调用", "硬件:手机"],
                score=16, score_relevance=9, score_contribution=7,
                recommendation="推荐", recommendation_reason=reason,
            ),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "papers.sqlite"
            storage_app.init_db(db_path)
            storage_app.upsert_run(
                db_path,
                research_run.validate_payload(covered_run_payload(*papers), today=TODAY, skip_network=True),
            )

            listed = storage_app.list_papers(db_path)

        self.assertEqual(
            [paper["id"] for paper in listed],
            ["phone-edge", "pc-edge", "other-edge", "official-non-edge"],
        )
        self.assertEqual(listed[0]["edge_agent_scope"], "手机")
        self.assertIn("手机本地", listed[0]["edge_agent_evidence"])

    def test_storage_rejects_run_without_collection_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "papers.sqlite"
            storage_app.init_db(db_path)

            with self.assertRaises(research_run.ValidationError) as ctx:
                storage_app.upsert_run(db_path, run_payload(valid_paper()))

        self.assertIn("collection_manifest", str(ctx.exception))

    def test_legacy_database_adds_recommendation_reason_without_losing_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "legacy.sqlite"
            storage_app.init_db(db_path)
            storage_app.upsert_run(
                db_path,
                research_run.validate_payload(covered_run_payload(valid_paper()), today=TODAY, skip_network=True),
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
                research_run.validate_payload(covered_run_payload(valid_paper()), today=TODAY, skip_network=True),
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
    def test_ghpages_deploy_builds_all_navigation_pages_before_gate(self):
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

        scripts = [Path(str(cmd[1])).name for cmd in calls if len(cmd) > 1 and str(cmd[0]) == sys.executable]
        self.assertIn("build.py", scripts)
        self.assertIn("build_notes.py", scripts)
        self.assertIn("build_snn.py", scripts)
        self.assertIn("build_waic.py", scripts)
        self.assertLess(scripts.index("build_waic.py"), scripts.index("gate_all.py"))

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
    def test_publish_payload_requires_collection_manifest(self):
        with self.assertRaises(research_run.ValidationError) as ctx:
            publish_results.publish_payload("http://example.test", run_payload(valid_paper()))

        self.assertIn("collection_manifest", str(ctx.exception))

    def test_publish_payload_rechecks_candidate_artifact_hashes(self):
        payload = covered_run_payload(valid_paper())
        payload["collection_manifest"]["sources"]["github"]["artifact_sha256"] = "0" * 64

        with self.assertRaises(research_collection.CollectionCoverageError) as ctx:
            publish_results.publish_payload("http://example.test", payload)

        self.assertIn("sha256", str(ctx.exception).lower())

    def test_posts_validated_payload_to_research_runs_endpoint(self):
        payload = covered_run_payload(valid_paper())
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
            result = publish_results.publish_payload(
                "http://example.test", payload, token=TEST_PUBLISH_TOKEN
            )

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

    def test_server_rejects_anonymous_research_run_post(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            httpd = server_app.create_server(
                ("127.0.0.1", 0), Path(tmpdir) / "papers.sqlite", publish_token=TEST_PUBLISH_TOKEN
            )
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{httpd.server_port}"
                payload = research_run.validate_payload(
                    covered_run_payload(valid_paper()), today=TODAY
                )
                with self.assertRaises(HTTPError) as ctx:
                    publish_results.publish_payload(base_url, payload, token="wrong-token")
            finally:
                httpd.shutdown()
                thread.join(timeout=5)
                httpd.server_close()

        self.assertEqual(ctx.exception.code, 401)

    def test_server_accepts_run_and_returns_latest_papers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            httpd = server_app.create_server(
                ("127.0.0.1", 0), Path(tmpdir) / "papers.sqlite", publish_token=TEST_PUBLISH_TOKEN
            )
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{httpd.server_port}"
                reason = "端侧收益明确，并在真实设备上报告了延迟改善，值得优先阅读。"
                title_zh = "端侧智能体规划框架"
                payload = research_run.validate_payload(covered_run_payload(valid_paper(
                    score=14,
                    title_zh=title_zh,
                    recommendation="推荐",
                    recommendation_reason=reason,
                )), today=TODAY)

                publish_result = publish_results.publish_payload(
                    base_url, payload, token=TEST_PUBLISH_TOKEN
                )
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
        self.assertEqual(papers_result["papers"][0]["tags"], ["方向:高效推理", "方向:记忆", "方向:评测基准"])
        self.assertEqual(papers_result["papers"][0]["edge_agent_scope"], "非端侧Agent")
        self.assertEqual(papers_result["papers"][0]["arxiv_date_basis"], "submitted")
        self.assertEqual(papers_result["papers"][0]["arxiv_revision_note"], "")
        self.assertEqual(papers_result["papers"][0]["title_zh"], title_zh)
        self.assertEqual(papers_result["papers"][0]["recommendation_reason"], reason)

    def test_server_lists_only_latest_research_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            httpd = server_app.create_server(
                ("127.0.0.1", 0), Path(tmpdir) / "papers.sqlite", publish_token=TEST_PUBLISH_TOKEN
            )
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{httpd.server_port}"
                old_payload = research_run.validate_payload(
                    {
                        **covered_run_payload(valid_paper(id="old-paper", title="Old Paper", score=10)),
                        "run_id": "run-20260625-old",
                    },
                    today=TODAY,
                )
                new_payload = research_run.validate_payload(
                    {
                        **covered_run_payload(valid_paper(id="new-paper", title="New Paper", score=16)),
                        "run_id": "run-20260625-new",
                    },
                    today=TODAY,
                )

                publish_results.publish_payload(base_url, old_payload, token=TEST_PUBLISH_TOKEN)
                publish_results.publish_payload(base_url, new_payload, token=TEST_PUBLISH_TOKEN)
                with request.urlopen(f"{base_url}/api/papers", timeout=5) as resp:
                    papers_result = json.loads(resp.read().decode("utf-8"))
            finally:
                httpd.shutdown()
                thread.join(timeout=5)
                httpd.server_close()

        self.assertEqual([paper["id"] for paper in papers_result["papers"]], ["new-paper"])

    def test_server_sorts_official_tier_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            httpd = server_app.create_server(
                ("127.0.0.1", 0), Path(tmpdir) / "papers.sqlite", publish_token=TEST_PUBLISH_TOKEN
            )
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{httpd.server_port}"
                payload = research_run.validate_payload(
                    covered_run_payload(
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

                publish_results.publish_payload(base_url, payload, token=TEST_PUBLISH_TOKEN)
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
