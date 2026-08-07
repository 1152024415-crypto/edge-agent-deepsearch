#!/usr/bin/env python3
from __future__ import annotations

import importlib
import inspect
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))

import arxiv_curl_sweep
import build_run_from_arxiv
import build_run_week
import collect_vendors
import publish_results
import research_run
import validate_research_run


class ResearchWindowTests(unittest.TestCase):
    def _module(self):
        spec = importlib.util.find_spec("research_collection")
        self.assertIsNotNone(spec, "research_collection module must centralize the weekly window")
        return importlib.import_module("research_collection")

    def test_window_contains_exactly_seven_calendar_dates(self):
        module = self._module()

        start, end, days = module.collection_window(date(2026, 8, 5))

        self.assertEqual(start.isoformat(), "2026-07-30")
        self.assertEqual(end.isoformat(), "2026-08-05")
        self.assertEqual([d.isoformat() for d in days], [
            "2026-07-30", "2026-07-31", "2026-08-01", "2026-08-02",
            "2026-08-03", "2026-08-04", "2026-08-05",
        ])


class ArxivPaginationTests(unittest.TestCase):
    def test_atom_parser_preserves_published_and_updated_dates(self):
        xml = """<feed xmlns="http://www.w3.org/2005/Atom">
          <entry><id>http://arxiv.org/abs/2505.09606v3</id><title>Orchard</title>
          <published>2026-05-14T00:00:00Z</published><updated>2026-07-30T00:00:00Z</updated>
          <summary>Agent training infrastructure.</summary><author><name>Microsoft Research</name></author></entry>
        </feed>"""

        parsed = arxiv_curl_sweep.parse(xml)

        self.assertEqual(parsed[0]["published_date"], "2026-05-14")
        self.assertEqual(parsed[0]["updated_date"], "2026-07-30")

    def test_api_can_sort_by_last_updated_date(self):
        url = arxiv_curl_sweep.build_api_url(
            "cat:cs.AI", start=0, page_size=100, sort_by="lastUpdatedDate"
        )

        self.assertIn("sortBy=lastUpdatedDate", url)

    def test_update_only_mode_selects_the_revision_sweep(self):
        specs = arxiv_curl_sweep.query_specs(only_updates=True)

        self.assertEqual([spec[0] for spec in specs], ["recent-updates"])
        self.assertEqual(specs[0][2:], ("lastUpdatedDate", "updated"))

    def test_script_propagates_incomplete_coverage_exit_code(self):
        source = Path(arxiv_curl_sweep.__file__).read_text(encoding="utf-8")

        self.assertIn("raise SystemExit(main())", source)

    def test_curl_transport_error_returns_empty_body(self):
        with mock.patch.object(arxiv_curl_sweep.subprocess, "run", side_effect=OSError("offline")), mock.patch.object(
            arxiv_curl_sweep.time, "sleep"
        ):
            body = arxiv_curl_sweep.curl_url("https://example.invalid/arxiv")

        self.assertEqual(body, "")

    def test_malformed_arxiv_response_is_not_treated_as_an_empty_page(self):
        with mock.patch.object(arxiv_curl_sweep, "curl_url", return_value="<broken"):
            with self.assertRaises(RuntimeError):
                arxiv_curl_sweep.fetch_query_page("cat:cs.AI", 0, 100)

    def test_full_first_page_fetches_the_second_page(self):
        self.assertTrue(hasattr(arxiv_curl_sweep, "collect_query_pages"))
        calls = []

        def fetch_page(query, start, page_size):
            calls.append((query, start, page_size))
            if start == 0:
                return [
                    {"id": f"2608.{i:05d}", "date": "2026-08-05", "title": "Edge AI", "abstract": "edge inference"}
                    for i in range(100)
                ]
            return [
                {"id": "2608.99999", "date": "2026-08-04", "title": "Mobile AI", "abstract": "mobile inference"}
            ]

        papers = arxiv_curl_sweep.collect_query_pages(
            "cat:cs.AI",
            fetch_page=fetch_page,
            window_start=date(2026, 7, 30),
            window_end=date(2026, 8, 5),
            page_size=100,
        )

        self.assertEqual([call[1] for call in calls], [0, 100])
        self.assertEqual(len(papers), 101)

    def test_api_url_contains_pagination_parameters(self):
        self.assertTrue(hasattr(arxiv_curl_sweep, "build_api_url"))

        url = arxiv_curl_sweep.build_api_url("cat:cs.AI", start=200, page_size=100)

        self.assertIn("start=200", url)
        self.assertIn("max_results=100", url)

    def test_reaching_page_limit_before_window_end_is_incomplete(self):
        self.assertTrue(hasattr(arxiv_curl_sweep, "PaginationLimitError"))

        def fetch_page(query, start, page_size):
            return [
                {
                    "id": f"2608.{start + index:05d}",
                    "date": "2026-08-05",
                    "title": "Edge AI",
                    "abstract": "edge inference",
                }
                for index in range(page_size)
            ]

        with self.assertRaises(arxiv_curl_sweep.PaginationLimitError):
            arxiv_curl_sweep.collect_query_pages(
                "cat:cs.AI",
                fetch_page=fetch_page,
                window_start=date(2026, 7, 30),
                window_end=date(2026, 8, 5),
                page_size=2,
                max_pages=2,
            )


class BroadCollectionBoundaryTests(unittest.TestCase):
    def test_updated_arxiv_candidate_keeps_revision_date_basis(self):
        paper = build_run_week.convert_arxiv({
            "id": "2505.09606",
            "title": "Orchard: An Open-Source Agentic Modeling Framework",
            "abstract": "A framework for scalable agentic modeling with tools and environments.",
            "authors": "Microsoft Research",
            "date": "2026-07-30",
            "date_basis": "updated",
        })

        self.assertIsNotNone(paper)
        self.assertEqual(paper["arxiv_date_basis"], "updated")

    def test_generated_score_reason_is_reader_facing_not_pipeline_status(self):
        paper = build_run_week.convert_arxiv({
            "id": "2608.00123",
            "title": "On-device LLM Inference on an Edge NPU",
            "abstract": "We reduce latency for local inference on resource-constrained devices.",
            "authors": "Alice Example",
            "date": "2026-08-04",
        })

        self.assertIsNotNone(paper)
        self.assertIn("明确涉及端侧", paper["score_reason"])
        self.assertNotRegex(paper["score_reason"], r"自动初评|主\s*Agent|待复核")

    def test_generic_language_collisions_do_not_count_as_edge_ai_evidence(self):
        cases = [
            "GENESIS explains individual graph edge decisions with an LLM.",
            "A foundation-model game theory embeds agents in social systems.",
            "Socially grounded AI is deployed across diverse cultural contexts.",
            "ToolLIFT learns generalizable tool planning for database agents.",
            "An Equivariant Music Transformer distills a mathematical observation.",
            "Onboarding language models for students.",
            "An LLM computes messages at the edge of each graph.",
            "Energy-Based Language Models for structured prediction.",
            "大语言模型提升复杂数学推理能力。",
            "人工智能部署到不同文化环境。",
            "人工智能加速科学发现。",
            "Headphone Transformers for audio synthesis.",
            "Telephone Language Models for call routing.",
            "AI Accelerates Scientific Discovery.",
            "LLM Agents with Monte Carlo Tree Search Pruning.",
            "Mobile Networks with Cloud LLMs.",
            "Mobile Users Query Remote LLMs.",
        ]

        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(
                    build_run_week.classify_research_relevance(text),
                    "irrelevant",
                )

    def test_explicit_edge_ai_terms_are_kept_even_without_singular_ai_words(self):
        cases = [
            "On-device autonomous agents for personal assistance",
            "TinyML on MCUs",
            "Edge LLMs for offline interaction",
            "ExecuTorch release for Android devices",
            "Mobile autonomous agents for offline personal assistance",
            "Embedded LLMs for local control",
            "Embedded neural networks for sensor analytics",
            "Device-side AI for private assistants",
            "Local LLM inference without cloud access",
            "Computer Vision on Edge Devices",
            "Object Detection on Embedded Devices",
            "Speech Recognition on Microcontrollers",
            "Keyword Spotting on MCUs",
            "YOLO Acceleration on FPGA",
            "Vision AI pipeline on an IQ-9075 EVK with Hexagon HTP",
        ]

        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(
                    build_run_week.classify_research_relevance(text),
                    "direct",
                )

    def test_keeps_adjacent_inference_work_but_rejects_unrelated_work(self):
        self.assertTrue(hasattr(build_run_week, "classify_research_relevance"))

        adjacent = build_run_week.classify_research_relevance(
            "High-Throughput LLM Serving with KV Cache Quantization"
        )
        unrelated = build_run_week.classify_research_relevance(
            "Hyperparameter Optimization for MRI Tumor Segmentation"
        )
        agent_memory = build_run_week.classify_research_relevance(
            "Compressed Long-Term Memory for Tool-Using LLM Agents"
        )
        direct_ai = build_run_week.classify_research_relevance(
            "Building Vision AI Pipelines on an Edge NPU"
        )
        saturated_gui = build_run_week.classify_research_relevance(
            "Mobile GUI Agent for Screen Clicking and UI Automation"
        )
        unrelated_edge_model = build_run_week.classify_research_relevance(
            "Energy Model for Low-Latency Edge Routing in Mobile Networks"
        )
        snn_accelerator = build_run_week.classify_research_relevance(
            "FPGA Accelerator for SNNs"
        )
        token_compression = build_run_week.classify_research_relevance(
            "Token Compression for Efficient Omni-modal Large Language Models. "
            "Long visual and audio sequences demand token compression for efficient deployment."
        )
        wearable_memory = build_run_week.classify_research_relevance(
            "A wearable assistant with long-term memory from streaming video"
        )

        self.assertEqual(adjacent, "adjacent")
        self.assertEqual(agent_memory, "adjacent")
        self.assertEqual(direct_ai, "direct")
        self.assertEqual(saturated_gui, "irrelevant")
        self.assertEqual(unrelated_edge_model, "irrelevant")
        self.assertEqual(snn_accelerator, "direct")
        self.assertEqual(token_compression, "adjacent")
        self.assertEqual(wearable_memory, "direct")
        self.assertEqual(unrelated, "irrelevant")

    def test_model_name_in_abstract_does_not_create_company_affiliation(self):
        paper = build_run_week.convert_arxiv({
            "id": "2608.00077",
            "title": "Efficient Qwen Inference on Resource-Constrained Hardware",
            "abstract": "We quantize Qwen and compare it with NVIDIA runtimes for efficient inference.",
            "authors": "Alice Example; Bob Example",
            "date": "2026-08-04",
        })

        self.assertIsNotNone(paper)
        self.assertEqual(paper["source_tier"], "学校预印本")
        self.assertEqual(paper["vendors"], "")

    def test_unrelated_official_post_is_not_given_high_relevance(self):
        paper = build_run_week.convert_vendor({
            "vendor": "NVIDIA",
            "title": "NVIDIA Announces Quarterly Financial Results",
            "summary": "Revenue and shareholder information for the quarter.",
            "url": "https://www.nvidia.com/example",
            "date": "2026-08-04",
        })

        self.assertIsNone(paper)

    def test_chinese_vendor_summary_can_supply_edge_relevance_evidence(self):
        paper = build_run_week.convert_vendor({
            "vendor": "Qualcomm",
            "title": "工业生成式人工智能演示",
            "summary": "在边缘设备上离线运行语言模型、检索和语音识别，并由本地加速器执行。",
            "url": "https://www.qualcomm.com/example",
            "date": "2026-08-04",
        })

        self.assertIsNotNone(paper)
        self.assertEqual(paper["score_relevance"], 9)

    def test_legacy_fixed_date_builder_refuses_to_create_a_run(self):
        with mock.patch.object(build_run_from_arxiv, "convert_arxiv", return_value=[]), mock.patch.object(
            Path, "write_text"
        ) as write_text:
            code = build_run_from_arxiv.main()

        self.assertNotEqual(code, 0)
        write_text.assert_not_called()


class GitHubReleaseCollectionTests(unittest.TestCase):
    def _module(self):
        spec = importlib.util.find_spec("collect_github_releases")
        self.assertIsNotNone(spec, "a weekly collector must cover releases and major code drops")
        return importlib.import_module("collect_github_releases")

    def test_major_code_drop_requires_substantive_change(self):
        module = self._module()

        self.assertTrue(module.is_major_code_drop({"files": [object()] * 80, "stats": {"additions": 16304}}))
        self.assertFalse(module.is_major_code_drop({"files": [object()] * 2, "stats": {"additions": 12}}))

    def test_microsoft_orchard_is_in_the_audited_project_set(self):
        module = importlib.import_module("research_collection")

        self.assertIn("microsoft/Orchard", module.REQUIRED_GITHUB_PROJECTS)

    def test_major_commit_scan_stops_after_first_match_and_caps_detail_requests(self):
        module = self._module()
        commits = [
            {"sha": f"sha-{index}", "commit": {"message": "code", "author": {"date": "2026-07-30T12:00:00Z"}}}
            for index in range(100)
        ]
        calls = []

        def detail_fetch(sha):
            calls.append(sha)
            if len(calls) == 2:
                return {"files": [object()] * 80, "stats": {"additions": 16304}}
            return {"files": [object()], "stats": {"additions": 1}}

        matches = module.find_major_code_drops(commits, detail_fetch, max_inspected=12, max_matches=1)

        self.assertEqual([item[0]["sha"] for item in matches], ["sha-1"])
        self.assertEqual(len(calls), 2)


class CollectionManifestTests(unittest.TestCase):
    def _module(self):
        spec = importlib.util.find_spec("research_collection")
        self.assertIsNotNone(spec, "research_collection module must validate source coverage")
        return importlib.import_module("research_collection")

    def _valid_manifest(self, module):
        _, _, days = module.collection_window(date(2026, 8, 5))
        return {
            "window_start": "2026-07-30",
            "window_end": "2026-08-05",
            "sources": {
                "arxiv": {
                    "status": "complete",
                    "candidate_count": 0,
                    "artifact_path": "C:/evidence/arxiv.json",
                    "artifact_sha256": "a" * 64,
                    "candidate_refs": [],
                    "candidate_identity_refs": [],
                    "candidate_lineage": {},
                    "queries_completed": sorted(module.REQUIRED_ARXIV_SWEEPS),
                    "pages_fetched": len(module.REQUIRED_ARXIV_SWEEPS),
                },
                "huggingface": {
                    "status": "complete",
                    "candidate_count": 0,
                    "artifact_path": "C:/evidence/huggingface.json",
                    "artifact_sha256": "b" * 64,
                    "candidate_refs": [],
                    "candidate_identity_refs": [],
                    "candidate_lineage": {},
                    "dates_checked": [d.isoformat() for d in days],
                },
                "github": {
                    "status": "complete",
                    "candidate_count": 0,
                    "artifact_path": "C:/evidence/github.json",
                    "artifact_sha256": "c" * 64,
                    "candidate_refs": [],
                    "candidate_identity_refs": [],
                    "candidate_lineage": {},
                    "release_projects_checked": sorted(module.REQUIRED_GITHUB_PROJECTS),
                    "trending_checked": True,
                },
                "vendors": {
                    "status": "complete",
                    "candidate_count": 0,
                    "artifact_path": "C:/evidence/vendors.json",
                    "artifact_sha256": "d" * 64,
                    "candidate_refs": [],
                    "candidate_identity_refs": [],
                    "candidate_lineage": {},
                    "vendors_checked": sorted(module.REQUIRED_VENDOR_SOURCES),
                    "vendor_checks": {
                        vendor: {
                            "status": "no_match",
                            "sources_succeeded": ["official-index"],
                        }
                        for vendor in module.REQUIRED_VENDOR_SOURCES
                    },
                },
            },
        }

    def test_accepts_complete_four_source_manifest(self):
        module = self._module()
        manifest = self._valid_manifest(module)

        normalized = module.validate_collection_manifest(manifest, today=date(2026, 8, 5))

        self.assertEqual(normalized["window_start"], "2026-07-30")

    def test_rejects_manifest_without_candidate_artifact_attestation(self):
        module = self._module()
        manifest = self._valid_manifest(module)
        del manifest["sources"]["github"]["artifact_sha256"]

        with self.assertRaises(module.CollectionCoverageError) as ctx:
            module.validate_collection_manifest(manifest, today=date(2026, 8, 5))

        self.assertIn("artifact_sha256", str(ctx.exception))

    def test_required_candidate_artifact_cannot_be_missing(self):
        self.assertIn("required", inspect.signature(build_run_week.load).parameters)
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "candidates-hf.json"

            with self.assertRaises(Exception) as ctx:
                build_run_week.load(missing, required=True)

        self.assertIn("missing", str(ctx.exception).lower())

    def test_rejects_huggingface_manifest_missing_a_day(self):
        module = self._module()
        manifest = self._valid_manifest(module)
        manifest["sources"]["huggingface"]["dates_checked"].pop()

        with self.assertRaises(module.CollectionCoverageError) as ctx:
            module.validate_collection_manifest(manifest, today=date(2026, 8, 5))

        self.assertIn("huggingface", str(ctx.exception).lower())

    def test_rejects_arxiv_manifest_with_too_few_pages_for_broad_sweeps(self):
        module = self._module()
        manifest = self._valid_manifest(module)
        manifest["sources"]["arxiv"]["pages_fetched"] = len(module.REQUIRED_ARXIV_SWEEPS) - 1

        with self.assertRaises(module.CollectionCoverageError) as ctx:
            module.validate_collection_manifest(manifest, today=date(2026, 8, 5))

        self.assertIn("pages_fetched", str(ctx.exception))

    def test_rejects_vendor_manifest_missing_a_required_vendor(self):
        module = self._module()
        manifest = self._valid_manifest(module)
        manifest["sources"]["vendors"]["vendors_checked"].remove("NVIDIA")

        with self.assertRaises(module.CollectionCoverageError) as ctx:
            module.validate_collection_manifest(manifest, today=date(2026, 8, 5))

        self.assertIn("NVIDIA", str(ctx.exception))

    def test_rejects_vendor_manifest_without_successful_source_evidence(self):
        module = self._module()
        manifest = self._valid_manifest(module)
        manifest["sources"]["vendors"]["vendor_checks"]["Apple"] = {
            "status": "unreachable",
            "sources_succeeded": [],
        }

        with self.assertRaises(module.CollectionCoverageError) as ctx:
            module.validate_collection_manifest(manifest, today=date(2026, 8, 5))

        self.assertIn("Apple", str(ctx.exception))

    def test_candidate_counts_must_match_loaded_artifacts(self):
        module = self._module()
        manifest = self._valid_manifest(module)
        manifest["sources"]["huggingface"]["candidate_count"] = 2

        with self.assertRaises(module.CollectionCoverageError) as ctx:
            module.validate_candidate_counts(
                manifest,
                {"arxiv": 0, "huggingface": 1, "github": 0, "vendors": 0},
            )

        self.assertIn("huggingface", str(ctx.exception).lower())

    def test_candidate_artifact_hash_must_match_manifest(self):
        module = self._module()
        manifest = self._valid_manifest(module)
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact = Path(tmpdir) / "candidates-hf.json"
            artifact.write_text("[]", encoding="utf-8")
            manifest["sources"]["huggingface"].update(
                module.candidate_artifact_attestation(artifact, "huggingface")
            )
            artifact.write_text('[{"id": "changed"}]', encoding="utf-8")

            with self.assertRaises(module.CollectionCoverageError) as ctx:
                module.validate_candidate_artifacts(
                    manifest,
                    {"huggingface": artifact},
                )

        self.assertIn("sha256", str(ctx.exception).lower())

    def test_rejects_github_manifest_that_only_checked_trending(self):
        module = self._module()
        manifest = self._valid_manifest(module)
        manifest["sources"]["github"]["release_projects_checked"] = []

        with self.assertRaises(module.CollectionCoverageError) as ctx:
            module.validate_collection_manifest(manifest, today=date(2026, 8, 5))

        self.assertIn("release", str(ctx.exception).lower())

    def test_validate_cli_refuses_a_run_without_collection_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_path = Path(tmpdir) / "run-20260805-120000.json"
            run_path.write_text("{}", encoding="utf-8")
            with mock.patch.object(
                validate_research_run.research_run, "load_and_validate", return_value={}
            ) as load:
                code = validate_research_run.main([str(run_path), "--today", "2026-08-05"])

        self.assertEqual(code, 1)
        load.assert_not_called()


class OfficialSourceCoverageTests(unittest.TestCase):
    def test_required_model_lab_domains_are_official_sources(self):
        urls = [
            "https://www.kimi.com/blog/example",
            "https://www.zhipuai.cn/news/example",
            "https://www.baichuan-ai.com/news/example",
            "https://www.modelbest.cn/news/example",
            "https://www.minimaxi.com/news/example",
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertTrue(research_run.is_official_source_url(url))

    def test_publish_cli_refuses_a_run_without_collection_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_path = Path(tmpdir) / "run-20260805-120000.json"
            run_path.write_text(json.dumps({"run_id": "x", "papers": []}), encoding="utf-8")
            with mock.patch.object(
                publish_results.research_run,
                "load_and_validate",
                return_value={"run_id": "x", "papers": []},
            ) as load, mock.patch.object(publish_results, "publish_payload", return_value={}):
                code = publish_results.main([
                    str(run_path), "--server", "http://127.0.0.1:1", "--today", "2026-08-05",
                ])

        self.assertEqual(code, 1)
        load.assert_not_called()

    def test_publish_cli_cannot_bypass_collection_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_path = Path(tmpdir) / "run-20260805-120000.json"
            run_path.write_text(json.dumps({"run_id": "x", "papers": []}), encoding="utf-8")
            with mock.patch.object(
                publish_results.research_run,
                "load_and_validate",
                return_value={"run_id": "x", "papers": []},
            ) as load, mock.patch.object(publish_results, "publish_payload", return_value={}) as publish:
                code = publish_results.main([
                    str(run_path),
                    "--server",
                    "http://127.0.0.1:1",
                    "--today",
                    "2026-08-05",
                    "--allow-incomplete-coverage",
                ])

        self.assertEqual(code, 1)
        load.assert_not_called()
        publish.assert_not_called()


class VendorCollectorTests(unittest.TestCase):
    def test_collect_vendor_aggregates_all_known_feeds(self):
        first_feed = """<rss><channel><item>
            <title>Edge AI Runtime</title>
            <link>https://vendor.example/edge-runtime</link>
            <pubDate>Tue, 04 Aug 2026 00:00:00 GMT</pubDate>
        </item></channel></rss>"""
        second_feed = """<rss><channel><item>
            <title>Mobile LLM Release</title>
            <link>https://vendor.example/mobile-llm</link>
            <pubDate>Mon, 03 Aug 2026 00:00:00 GMT</pubDate>
        </item></channel></rss>"""

        def fake_fetch(url, timeout=20):
            if url.endswith("first.xml"):
                return first_feed
            if url.endswith("second.xml"):
                return second_feed
            return ""

        with mock.patch.object(collect_vendors, "fetch", side_effect=fake_fetch):
            items, check = collect_vendors.collect_vendor(
                "Example",
                "https://vendor.example",
                [
                    "https://vendor.example/first.xml",
                    "https://vendor.example/second.xml",
                ],
                date(2026, 7, 30),
                date(2026, 8, 5),
            )

        self.assertEqual(
            {item["url"] for item in items},
            {
                "https://vendor.example/edge-runtime",
                "https://vendor.example/mobile-llm",
            },
        )
        self.assertEqual(check["status"], "found")
        self.assertEqual(len(check["sources_succeeded"]), 2)


if __name__ == "__main__":
    unittest.main()
