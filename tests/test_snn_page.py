#!/usr/bin/env python3
"""snn_page template renders the SNN insight page shell."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.snn_page import SNN_HTML


class SNNPageTest(unittest.TestCase):
    def test_template_has_key_markers(self):
        self.assertIn("<!doctype html>", SNN_HTML)
        self.assertIn("marked.min.js", SNN_HTML)      # markdown 渲染
        self.assertIn("katex", SNN_HTML.lower())       # 数学渲染
        self.assertIn("SNN-insight.md", SNN_HTML)     # 客户端 fetch 目标
        self.assertIn('id="toc"', SNN_HTML)           # TOC 侧栏
        self.assertIn('id="art"', SNN_HTML)           # 正文容器
        self.assertIn("index.html", SNN_HTML)          # 返回雷达链接

    def test_template_has_toc_autobuild_js(self):
        # TOC 从渲染后 h2 自动生成 + 当前节高亮
        self.assertIn("querySelectorAll('h2')", SNN_HTML)
        self.assertIn("IntersectionObserver", SNN_HTML)


if __name__ == "__main__":
    unittest.main()
