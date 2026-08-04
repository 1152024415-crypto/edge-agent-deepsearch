#!/usr/bin/env python3
"""Display-contract tests for the desktop recommendation-first layout."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.page import INDEX_HTML


class DesktopRecommendationLayoutTest(unittest.TestCase):
    def test_agent_recommendations_precede_weekly_and_full_research(self):
        recommendation_pos = INDEX_HTML.find('id="recommendations"')
        weekly_pos = INDEX_HTML.find('id="weekly"')
        all_research_pos = INDEX_HTML.find('id="all-research"')

        self.assertGreaterEqual(recommendation_pos, 0)
        self.assertGreaterEqual(all_research_pos, 0)
        self.assertLess(recommendation_pos, weekly_pos)
        self.assertLess(weekly_pos, all_research_pos)

    def test_recommendation_count_comes_from_existing_agent_flag(self):
        self.assertIn(
            "const isRecommended=p=>p.recommendation==='推荐';",
            INDEX_HTML,
        )
        self.assertIn("visible().filter(isRecommended)", INDEX_HTML)
        self.assertIn("Agent 本周推荐", INDEX_HTML)

    def test_full_research_does_not_repeat_recommended_items(self):
        self.assertIn("visible().filter(p=>!isRecommended(p))", INDEX_HTML)
        self.assertIn("推荐已在上方展示", INDEX_HTML)

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
        self.assertIn(".rec-note{max-width:430px;margin:0;color:#d5dfe4;font-size:13px", INDEX_HTML)
        self.assertIn(".rec-summary{display:block;color:#fffaf2", INDEX_HTML)

    def test_recommendation_card_prioritizes_chinese_summary_and_reason(self):
        self.assertIn('class="rec-summary"', INDEX_HTML)
        self.assertIn('class="rec-why"', INDEX_HTML)
        self.assertIn('class="rec-original"', INDEX_HTML)
        self.assertIn("值得优先看：", INDEX_HTML)
        self.assertIn("原标题：", INDEX_HTML)

    def test_recommendation_card_never_exposes_internal_score_reason(self):
        start = INDEX_HTML.index("function renderRecommendations()")
        end = INDEX_HTML.index("function renderRadar()", start)
        recommendation_renderer = INDEX_HTML[start:end]

        self.assertNotIn("score_reason", recommendation_renderer)
        self.assertIn("recommendation_reason", recommendation_renderer)

    def test_recommendation_kicker_is_chinese(self):
        self.assertIn("Agent 精选 · 推荐优先", INDEX_HTML)
        self.assertNotIn("agent curation · ranked first", INDEX_HTML)

    def test_original_title_keeps_up_to_two_lines(self):
        self.assertIn(".rec-original{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2", INDEX_HTML)
        original_style = INDEX_HTML.split(".rec-original{", 1)[1].split("}", 1)[0]
        self.assertNotIn("white-space:nowrap", original_style)


if __name__ == "__main__":
    unittest.main()
