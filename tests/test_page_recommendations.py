#!/usr/bin/env python3
"""Display-contract tests for the multi-source desktop editorial layout."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.page import INDEX_HTML


class DesktopRecommendationLayoutTest(unittest.TestCase):
    def test_static_build_prefers_inlined_papers_before_api_fallback(self):
        self.assertIn("let data=window.__PAPERS__||null;", INDEX_HTML)
        self.assertIn('const res=await fetch("/api/papers")', INDEX_HTML)

    def test_editorial_sections_follow_the_reader_priority_order(self):
        recommendation_pos = INDEX_HTML.find('id="recommendations"')
        weekly_pos = INDEX_HTML.find('id="weekly"')
        all_research_pos = INDEX_HTML.find('id="all-research"')
        discovery_pos = INDEX_HTML.find('id="discovery"')

        self.assertGreaterEqual(recommendation_pos, 0)
        self.assertGreaterEqual(all_research_pos, 0)
        self.assertGreaterEqual(discovery_pos, 0)
        self.assertLess(recommendation_pos, weekly_pos)
        self.assertLess(weekly_pos, all_research_pos)
        self.assertLess(all_research_pos, discovery_pos)

    def test_complete_research_contains_a_source_map(self):
        all_research_pos = INDEX_HTML.index('id="all-research"')
        source_map_pos = INDEX_HTML.index('id="source-map"')
        discovery_pos = INDEX_HTML.index('id="discovery"')

        self.assertLess(all_research_pos, source_map_pos)
        self.assertLess(source_map_pos, discovery_pos)

    def test_recommendation_count_comes_from_existing_agent_flag(self):
        self.assertIn(
            "const isRecommended=p=>p.recommendation==='推荐';",
            INDEX_HTML,
        )
        self.assertIn("ALL.filter(isRecommended)", INDEX_HTML)
        self.assertIn("Agent 本周推荐", INDEX_HTML)

    def test_complete_research_keeps_recommended_items(self):
        start = INDEX_HTML.index("function renderPapers()")
        end = INDEX_HTML.index("function renderTabs(", start)
        complete_renderer = INDEX_HTML[start:end]

        self.assertIn("const l=visible()", complete_renderer)
        self.assertNotIn("!isRecommended", complete_renderer)
        self.assertIn('class="rec-badge"', INDEX_HTML)
        self.assertIn("完整资料库包含全部", INDEX_HTML)

    def test_library_filters_combine_device_source_and_tags(self):
        self.assertIn('ACTIVE_SOURCE=""', INDEX_HTML)
        self.assertIn('ACTIVE_SCOPE=""', INDEX_HTML)
        self.assertIn("p.source_tier===ACTIVE_SOURCE", INDEX_HTML)
        self.assertIn("p.edge_agent_scope===ACTIVE_SCOPE", INDEX_HTML)
        self.assertIn("ACTIVE.size===0", INDEX_HTML)

    def test_long_filters_use_progressive_disclosure(self):
        self.assertIn('id="advanced-toggle"', INDEX_HTML)
        self.assertIn('aria-expanded="false"', INDEX_HTML)
        self.assertIn('id="advanced-filter"', INDEX_HTML)

    def test_github_trending_is_an_independent_discovery_area(self):
        start = INDEX_HTML.index("function renderTrending(")
        end = INDEX_HTML.index("async function loadTrending", start)
        renderer = INDEX_HTML[start:end]

        self.assertIn('document.querySelector("#discovery-list")', renderer)
        self.assertIn("待核验线索", INDEX_HTML)
        self.assertNotIn("band-trending", renderer)

    def test_weekly_highlights_use_progressive_disclosure(self):
        self.assertIn("const WEEKLY_PREVIEW=3", INDEX_HTML)
        self.assertIn('class="weekly-more"', INDEX_HTML)
        self.assertIn("展开其余", INDEX_HTML)

    def test_unreported_detail_fields_are_not_emphasized(self):
        self.assertIn("const hasContent=v=>v&&v!=='未报告';", INDEX_HTML)
        self.assertIn("hasContent(p.effects)", INDEX_HTML)
        self.assertIn("hasContent(p.mechanism)", INDEX_HTML)

    def test_week_switch_is_resynchronized_after_back_navigation(self):
        self.assertIn('window.addEventListener("pageshow",renderWeekSwitch)', INDEX_HTML)

    def test_recommendation_preview_copy_distinguishes_visible_and_total(self):
        self.assertIn("首屏精选 ${Math.min(recommended.length,REC_PREVIEW)} 条", INDEX_HTML)
        self.assertIn("共推荐 ${countLabel} 条", INDEX_HTML)
        self.assertIn("查看其余 '+(recommended.length-REC_PREVIEW)+' 条", INDEX_HTML)

    def test_recommendation_explanation_text_is_desktop_readable(self):
        self.assertIn(".rec-item{display:grid;grid-template-columns:72px minmax(0,1fr) minmax(260px,360px)", INDEX_HTML)
        self.assertIn(".rec-note{max-width:520px;margin:0;color:var(--muted);font-size:13px", INDEX_HTML)
        self.assertIn(".rec-title{display:block;color:var(--ink);font-weight:700;font-size:clamp(", INDEX_HTML)
        self.assertIn(".rec-summary{display:-webkit-box", INDEX_HTML)

    def test_recommendation_card_prioritizes_chinese_summary_and_reason(self):
        self.assertIn('class="rec-title"', INDEX_HTML)
        self.assertIn('class="rec-summary"', INDEX_HTML)
        self.assertIn('class="rec-tags"', INDEX_HTML)
        self.assertIn('class="rec-why"', INDEX_HTML)
        self.assertIn('class="rec-original"', INDEX_HTML)
        self.assertIn("关键词", INDEX_HTML)
        self.assertIn("值得优先看：", INDEX_HTML)
        self.assertIn("原标题：", INDEX_HTML)

    def test_recommendation_card_reads_name_intro_keywords_then_reason(self):
        start = INDEX_HTML.index("function renderRecommendations()")
        end = INDEX_HTML.index("function renderRadar()", start)
        recommendation_renderer = INDEX_HTML[start:end]

        title_pos = recommendation_renderer.index('class="rec-title"')
        summary_pos = recommendation_renderer.index('class="rec-summary"')
        tags_pos = recommendation_renderer.index('class="rec-tags"')
        why_pos = recommendation_renderer.index('class="rec-why"')
        original_pos = recommendation_renderer.index('class="rec-original"')

        self.assertLess(title_pos, summary_pos)
        self.assertLess(summary_pos, tags_pos)
        self.assertLess(tags_pos, why_pos)
        self.assertLess(why_pos, original_pos)
        self.assertIn("p.title_zh", recommendation_renderer)

    def test_recommendation_card_never_exposes_internal_score_reason(self):
        start = INDEX_HTML.index("function renderRecommendations()")
        end = INDEX_HTML.index("function renderRadar()", start)
        recommendation_renderer = INDEX_HTML[start:end]

        self.assertNotIn("score_reason", recommendation_renderer)
        self.assertIn("recommendation_reason", recommendation_renderer)

    def test_recommendation_kicker_is_chinese(self):
        self.assertIn("Agent 精选 · 推荐优先", INDEX_HTML)
        self.assertNotIn("agent curation · ranked first", INDEX_HTML)

    def test_recommendations_rank_phone_pc_and_other_edge_agents_first(self):
        self.assertIn(
            "const EDGE_AGENT_PRIORITY={\"手机\":0,\"PC\":1,\"其他端侧\":2,\"非端侧Agent\":3};",
            INDEX_HTML,
        )
        self.assertIn("edgeAgentPriority(a)-edgeAgentPriority(b)", INDEX_HTML)

    def test_recommendation_cards_show_verified_device_scope_badges(self):
        self.assertIn("const EDGE_AGENT_LABELS={\"手机\":\"手机端 Agent\",\"PC\":\"PC 端 Agent\",\"其他端侧\":\"其他端侧 Agent\"};", INDEX_HTML)
        self.assertIn('class="rec-edge-scope"', INDEX_HTML)
        self.assertIn("EDGE_AGENT_LABELS[p.edge_agent_scope]", INDEX_HTML)

    def test_original_title_keeps_up_to_two_lines(self):
        self.assertIn(".rec-original{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2", INDEX_HTML)
        original_style = INDEX_HTML.split(".rec-original{", 1)[1].split("}", 1)[0]
        self.assertNotIn("white-space:nowrap", original_style)


if __name__ == "__main__":
    unittest.main()
