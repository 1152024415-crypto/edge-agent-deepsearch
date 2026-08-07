import unittest

from agent.rebase_curated_run import rebase_curated_run


class RebaseCuratedRunTests(unittest.TestCase):
    def test_keeps_fresh_lineage_and_previous_editorial_copy(self):
        fresh = {
            "run_id": "fresh",
            "generated_at": "2026-08-05T18:00:00+08:00",
            "collection_manifest": {"window": {"start": "2026-07-30", "end": "2026-08-05"}},
            "papers": [{
                "id": "paper-1",
                "title": "Fresh title",
                "title_zh": "",
                "abstract": "English source copy.",
                "effects": "未报告",
                "mechanism": "未报告",
                "paper_url": "https://example.com/fresh",
                "date": "2026-08-05",
                "score": 10,
                "score_relevance": 5,
                "score_contribution": 5,
                "score_reason": "fresh",
                "source_tier": "学校预印本",
                "open_source": False,
                "tags": ["方向:端侧agent"],
                "edge_agent_scope": "待核实",
                "edge_agent_evidence": "",
                "authors": "A",
                "vendors": "",
                "affiliation_evidence_url": "",
                "venue": "arXiv",
                "recommendation": "纳入",
                "recommendation_reason": "",
                "candidate_source": "arxiv",
                "candidate_ref": "fresh-ref",
            }],
        }
        previous = {"papers": [{
            **fresh["papers"][0],
            "abstract": "这是中文摘要。",
            "candidate_ref": "stale-ref",
            "paper_url": "https://example.com/stale",
        }]}

        result = rebase_curated_run(fresh, previous, {"run_id": "curated", "include_ids": []})

        paper = result["papers"][0]
        self.assertEqual(result["run_id"], "curated")
        self.assertEqual(paper["abstract"], "这是中文摘要。")
        self.assertEqual(paper["candidate_ref"], "fresh-ref")
        self.assertEqual(paper["paper_url"], "https://example.com/fresh")
        self.assertEqual(paper["edge_agent_scope"], "非端侧Agent")
        self.assertNotIn("方向:端侧agent", paper["tags"])

    def test_applies_explicit_direct_agent_decision_and_includes_new_item(self):
        paper = {
            "id": "phone-agent",
            "title": "Phone Agent",
            "title_zh": "",
            "abstract": "English.",
            "effects": "未报告",
            "mechanism": "未报告",
            "paper_url": "https://example.com/phone",
            "date": "2026-08-05",
            "score": 10,
            "score_relevance": 5,
            "score_contribution": 5,
            "score_reason": "fresh",
            "source_tier": "学校预印本",
            "open_source": False,
            "tags": ["应用:手机"],
            "edge_agent_scope": "待核实",
            "edge_agent_evidence": "",
            "authors": "A",
            "vendors": "",
            "affiliation_evidence_url": "",
            "venue": "arXiv",
            "recommendation": "纳入",
            "recommendation_reason": "",
            "candidate_source": "arxiv",
            "candidate_ref": "ref",
        }
        decisions = {
            "run_id": "curated",
            "include_ids": ["phone-agent"],
            "overrides": {
                "phone-agent": {
                    "edge_agent_scope": "手机",
                    "edge_agent_evidence": "模型在手机本地完成判断和动作。",
                    "recommendation": "推荐",
                    "score_relevance": 9,
                    "score_contribution": 6,
                }
            },
        }

        result = rebase_curated_run(
            {"run_id": "fresh", "generated_at": "now", "papers": [paper]},
            {"papers": []},
            decisions,
        )

        selected = result["papers"][0]
        self.assertEqual(selected["edge_agent_scope"], "手机")
        self.assertIn("方向:端侧agent", selected["tags"])
        self.assertEqual(selected["score"], 15)


if __name__ == "__main__":
    unittest.main()
