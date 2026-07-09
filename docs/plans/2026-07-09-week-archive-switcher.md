# 周归档 + 切换器 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让端侧 AI Agent 信号周报站点保留所有过往周的页面，用户可在顶部下拉切换「本周 / 历史周」，静态站（GitHub Pages）与本地运行时服务器都支持。

**Architecture:** 引入 `app/weeks.py` 作为周归档/manifest/解析的单一边界模块。`app/build.py` 每次 build 把当前周完整 payload 写入 `data/weeks/<label>.json` + 刷新 manifest，并为每个历史周渲染 `site/week/<label>.html`（冻结页，payload 内联）。`app/server.py` 加 `/api/weeks` 与 `/week/<label>` 路由，并在 `/` 注入 `window.__WEEKS__`。`app/page.py` 顶部加 `<select>` 切换器，读内联的 `__WEEKS__/__WEEK_LABEL__` 导航。

**Tech Stack:** Python 3（标准库 http.server / unittest / regex）、原生 JS + marked.js、静态 HTML。

## Global Constraints

- 不引入新依赖（仅标准库 + 已有 CDN 的 marked.js）。
- 测试用 `unittest`，遵循 `tests/test_build.py` 既有模式（起真实 server、subprocess 跑 build.py）。
- `weekly_summary.json` 仍由用户手写，不在 repo 内程序化写入（仅 server.py 读取）。
- 静态站链接一律相对路径（兼容 gh-pages 子路径部署）；运行时用绝对路径 `/`、`/week/<label>`。
- 归档页是「冻结」的（payload 内联、不 fetch）；本周页在运行时 live、静态 build 时快照。
- label = 周窗口起始日 `YYYY-MM-DD`；title 沿用 overview 里的 `MM-DD~MM-DD` 原文。
- 中文文案；提交信息可用中文（沿用既有 commit 风格）。

---

## File Structure

| 文件 | 职责 |
|---|---|
| `app/weeks.py`（新建） | 周元数据解析、归档读写、manifest 读写、HTML payload 抽取、切换器 href 计算。纯逻辑、无 IO 副作用除读写 `data/weeks/`。 |
| `app/build.py`（改） | 调 `app.weeks`：每次 build 写当前周归档 + manifest，渲染 `site/index.html` 与各 `site/week/<label>.html`；加 `--backfill`。 |
| `app/server.py`（改） | 加 `/api/weeks`、`/week/<label>` 路由；`/` 注入 `window.__WEEKS__`。 |
| `app/page.py`（改） | header 加 `<select#week-switch>` + 加载时渲染 + change 导航 JS；加 `.week-switch` 样式。 |
| `tests/test_weeks.py`（新建） | `app.weeks` 单元测试。 |
| `tests/test_build.py`（改） | 扩展：assert 归档 json + manifest + `site/week/*.html` + 切换器标记。 |
| `tests/test_server_weeks.py`（新建） | `/api/weeks`、`/week/<label>`、`/` 注入 `__WEEKS__` 的路由测试。 |

---

## Task 1: `app/weeks.py` — 周元数据解析

**Files:**
- Create: `app/weeks.py`
- Test: `tests/test_weeks.py`

**Interfaces:**
- Produces: `parse_week_meta(overview: str, fallback_iso: str) -> dict` 返回 `{"label": "YYYY-MM-DD", "title": "MM-DD~MM-DD", "range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}}`。

- [ ] **Step 1: 写失败测试**

创建 `tests/test_weeks.py`：

```python
#!/usr/bin/env python3
"""Unit tests for app.weeks (week archive / manifest / parse logic)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import weeks


class ParseWeekMetaTest(unittest.TestCase):
    def test_parses_range_from_overview(self):
        ov = "本周端侧 AI 技术动态(06-26~07-03)：edge AI 板卡/整机..."
        m = weeks.parse_week_meta(ov, "2026-07-09")
        self.assertEqual(m["label"], "2026-06-26")
        self.assertEqual(m["title"], "06-26~07-03")
        self.assertEqual(m["range"]["start"], "2026-06-26")
        self.assertEqual(m["range"]["end"], "2026-07-03")

    def test_uses_fallback_year(self):
        # 2025 年的 overview 也用 fallback 年份
        ov = "本周动态(12-26~01-02)：..."
        m = weeks.parse_week_meta(ov, "2026-01-05")
        self.assertEqual(m["label"], "2026-12-26")
        self.assertEqual(m["range"]["end"], "2026-01-02")

    def test_no_range_falls_back_to_date(self):
        ov = "本周动态：无日期范围"
        m = weeks.parse_week_meta(ov, "2026-07-09")
        self.assertEqual(m["label"], "2026-07-09")
        self.assertEqual(m["title"], "2026-07-09")
        self.assertEqual(m["range"]["start"], "2026-07-09")
        self.assertEqual(m["range"]["end"], "2026-07-09")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m unittest tests.test_weeks -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.weeks'`

- [ ] **Step 3: 写最小实现**

创建 `app/weeks.py`：

```python
"""Week archive / manifest / parse logic for the research-radar site.

A "week" is a frozen snapshot of one weekly cycle: the papers list, the
weekly summary (overview + highlights), and the trending list. This module
owns the data model and disk layout under ``data/weeks/``; both the static
builder (app.build) and the runtime server (app.server) call into it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEEKS_DIR = ROOT / "data" / "weeks"

_RANGE_RE = re.compile(r"(\d{2})-(\d{2})~(\d{2})-(\d{2})")


def parse_week_meta(overview: str, fallback_iso: str) -> dict:
    """Derive {label, title, range} from the weekly overview text.

    Parses the first ``MM-DD~MM-DD`` occurrence; year taken from
    ``fallback_iso`` (a YYYY-MM-DD string). If no range is found, falls
    back to ``fallback_iso`` for every field.
    """
    year = fallback_iso[:4]
    m = _RANGE_RE.search(overview or "")
    if not m:
        return {
            "label": fallback_iso,
            "title": fallback_iso,
            "range": {"start": fallback_iso, "end": fallback_iso},
        }
    sm, sd, em, ed = m.groups()
    start = f"{year}-{sm}-{sd}"
    end = f"{year}-{em}-{ed}"
    title = f"{sm}-{sd}~{em}-{ed}"
    return {"label": start, "title": title, "range": {"start": start, "end": end}}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m unittest tests.test_weeks -v`
Expected: PASS（3 个用例）

- [ ] **Step 5: 提交**

```bash
git add app/weeks.py tests/test_weeks.py
git commit -m "feat(weeks): 周元数据解析 parse_week_meta + 单测"
```

---

## Task 2: `app/weeks.py` — 归档读写 + manifest + href 计算

**Files:**
- Modify: `app/weeks.py`
- Modify: `tests/test_weeks.py`

**Interfaces:**
- Produces:
  - `archive_path(label: str) -> Path`
  - `read_archive(label: str) -> dict | None`
  - `write_archive(meta: dict, papers: list, weekly: dict, trending: dict) -> None`（`meta` = Task1 的返回结构）
  - `build_manifest(current_label: str) -> list[dict]`（写 `data/weeks/manifest.json`，返回 `[{label,title,range,current}]` 按 start 倒序）
  - `read_manifest() -> list[dict]`（缺文件返回 `[]`）
  - `attach_hrefs(manifest: list[dict], weeks_base: str, runtime: bool) -> list[dict]`（每项加 `href` 字段）

- [ ] **Step 1: 写失败测试**

在 `tests/test_weeks.py` 追加：

```python
import tempfile


class ArchiveManifestTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._orig = weeks.WEEKS_DIR
        weeks.WEEKS_DIR = Path(self._tmp.name)
        self.addCleanup(self._restore)

    def _restore(self):
        weeks.WEEKS_DIR = self._orig

    def _meta(self, label, title=None, start=None, end=None):
        return {"label": label, "title": title or label,
                "range": {"start": start or label, "end": end or label}}

    def test_write_then_read_archive(self):
        meta = self._meta("2026-06-26", "06-26~07-03", "2026-06-26", "2026-07-03")
        weeks.write_archive(meta, [{"id": "p1"}], {"overview": "ov"}, {"items": []})
        self.assertEqual(weeks.archive_path("2026-06-26"), Path(self._tmp.name) / "2026-06-26.json")
        a = weeks.read_archive("2026-06-26")
        self.assertEqual(a["label"], "2026-06-26")
        self.assertEqual(a["papers"], [{"id": "p1"}])
        self.assertEqual(a["weekly"], {"overview": "ov"})
        self.assertEqual(a["trending"], {"items": []})

    def test_read_missing_returns_none(self):
        self.assertIsNone(weeks.read_archive("nope"))

    def test_build_manifest_sorts_desc_and_marks_current(self):
        weeks.write_archive(self._meta("2026-06-26", "06-26~07-03", "2026-06-26", "2026-07-03"), [], {}, {})
        weeks.write_archive(self._meta("2026-07-02", "07-02~07-09", "2026-07-02", "2026-07-09"), [], {}, {})
        m = weeks.build_manifest("2026-07-02")
        self.assertEqual(m[0]["label"], "2026-07-02")
        self.assertTrue(m[0]["current"])
        self.assertFalse(m[1]["current"])
        self.assertEqual(m[1]["label"], "2026-06-26")
        # manifest persisted
        self.assertEqual(weeks.read_manifest(), m)

    def test_read_manifest_missing_returns_empty(self):
        weeks.WEEKS_DIR = Path(self._tmp.name) / "nope"  # 不存在的目录
        self.assertEqual(weeks.read_manifest(), [])

    def test_attach_hrefs_static_root(self):
        manifest = [
            {"label": "2026-07-02", "title": "07-02~07-09", "range": {"start": "2026-07-02", "end": "2026-07-09"}, "current": True},
            {"label": "2026-06-26", "title": "06-26~07-03", "range": {"start": "2026-06-26", "end": "2026-07-03"}, "current": False},
        ]
        out = weeks.attach_hrefs(manifest, weeks_base="", runtime=False)
        self.assertEqual(out[0]["href"], "index.html")
        self.assertEqual(out[1]["href"], "week/2026-06-26.html")

    def test_attach_hrefs_static_subdir(self):
        manifest = [{"label": "2026-07-02", "current": True}, {"label": "2026-06-26", "current": False}]
        out = weeks.attach_hrefs(manifest, weeks_base="../", runtime=False)
        self.assertEqual(out[0]["href"], "../index.html")
        self.assertEqual(out[1]["href"], "../week/2026-06-26.html")

    def test_attach_hrefs_runtime(self):
        manifest = [{"label": "2026-07-02", "current": True}, {"label": "2026-06-26", "current": False}]
        out = weeks.attach_hrefs(manifest, weeks_base="", runtime=True)
        self.assertEqual(out[0]["href"], "/")
        self.assertEqual(out[1]["href"], "/week/2026-06-26")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m unittest tests.test_weeks -v`
Expected: FAIL（新用例 AttributeError on missing functions）

- [ ] **Step 3: 扩展 `app/weeks.py`**

在 `app/weeks.py` 末尾追加：

```python
def archive_path(label: str) -> Path:
    return WEEKS_DIR / f"{label}.json"


def read_archive(label: str) -> dict | None:
    p = archive_path(label)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def write_archive(meta: dict, papers: list, weekly: dict, trending: dict) -> None:
    WEEKS_DIR.mkdir(parents=True, exist_ok=True)
    rec = {
        "label": meta["label"],
        "title": meta["title"],
        "range": meta["range"],
        "papers": papers,
        "weekly": weekly,
        "trending": trending,
    }
    archive_path(meta["label"]).write_text(
        json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")


def build_manifest(current_label: str) -> list[dict]:
    """Scan data/weeks/*.json, sort by range.start desc, mark current; persist."""
    WEEKS_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for p in sorted(WEEKS_DIR.glob("*.json")):
        if p.name == "manifest.json":
            continue
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        entries.append({
            "label": rec["label"],
            "title": rec.get("title") or rec["label"],
            "range": rec.get("range") or {"start": rec["label"], "end": rec["label"]},
            "current": rec["label"] == current_label,
        })
    entries.sort(key=lambda e: e["range"]["start"], reverse=True)
    (WEEKS_DIR / "manifest.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    return entries


def read_manifest() -> list[dict]:
    p = WEEKS_DIR / "manifest.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def attach_hrefs(manifest: list[dict], weeks_base: str, runtime: bool) -> list[dict]:
    """Add an `href` to each manifest entry for the switcher to navigate to."""
    out = []
    for e in manifest:
        if runtime:
            href = "/" if e.get("current") else f"/week/{e['label']}"
        else:
            href = weeks_base + "index.html" if e.get("current") else f"{weeks_base}week/{e['label']}.html"
        out.append({**e, "href": href})
    return out
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m unittest tests.test_weeks -v`
Expected: PASS（全部用例）

- [ ] **Step 5: 提交**

```bash
git add app/weeks.py tests/test_weeks.py
git commit -m "feat(weeks): 归档读写+manifest+切换器href计算"
```

---

## Task 3: `app/weeks.py` — 从 HTML 抽取内联 payload（回填用）

**Files:**
- Modify: `app/weeks.py`
- Modify: `tests/test_weeks.py`

**Interfaces:**
- Produces: `extract_payloads_from_html(html: str) -> dict` 返回 `{"papers": list, "weekly": dict, "trending": dict}`。任一缺失返回空默认（papers `[]`、weekly `{"overview":"","highlights":[]}`、trending `{"items":[]}`）。

- [ ] **Step 1: 写失败测试**

在 `tests/test_weeks.py` 追加：

```python
class ExtractPayloadsTest(unittest.TestCase):
    def test_extracts_three_payloads(self):
        html = (
            '<script>window.__PAPERS__ = [{"id":"p1"}];'
            'window.__WEEKLY__ = {"overview":"ov","highlights":[]};'
            'window.__TRENDING__ = {"items":[{"repo":"r"}]};</script>'
        )
        out = weeks.extract_payloads_from_html(html)
        self.assertEqual(out["papers"], [{"id": "p1"}])
        self.assertEqual(out["weekly"]["overview"], "ov")
        self.assertEqual(out["trending"]["items"], [{"repo": "r"}])

    def test_missing_payloads_use_defaults(self):
        out = weeks.extract_payloads_from_html("<html>no scripts</html>")
        self.assertEqual(out["papers"], [])
        self.assertEqual(out["weekly"], {"overview": "", "highlights": []})
        self.assertEqual(out["trending"], {"items": []})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m unittest tests.test_weeks.ExtractPayloadsTest -v`
Expected: FAIL AttributeError

- [ ] **Step 3: 扩展 `app/weeks.py`**

追加：

```python
_PAPERS_RE = re.compile(r"window\.__PAPERS__\s*=\s*(\[.*?\]);", re.S)
_WEEKLY_RE = re.compile(r"window\.__WEEKLY__\s*=\s*(\{.*?\});\s*window\.__TRENDING__", re.S)
_TRENDING_RE = re.compile(r"window\.__TRENDING__\s*=\s*(\{.*?\});</script>", re.S)


def extract_payloads_from_html(html: str) -> dict:
    """Pull the three inlined payloads back out of a built index.html (for backfill)."""
    def grab(rx, default):
        m = rx.search(html)
        if not m:
            return default
        try:
            return json.loads(m.group(1))
        except Exception:
            return default
    return {
        "papers": grab(_PAPERS_RE, []),
        "weekly": grab(_WEEKLY_RE, {"overview": "", "highlights": []}),
        "trending": grab(_TRENDING_RE, {"items": []}),
    }
```

注意：`_WEEKLY_RE` 用 `;\s*window\.__TRENDING__` 作右界、`_TRENDING_RE` 用 `;</script>` 作右界——因 build.py 把三者在同一段 `<script>` 内联、顺序固定为 PAPERS;WEEKLY;TRENDING。若正则失败，回退默认值不崩。

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m unittest tests.test_weeks -v`
Expected: PASS（全部）

- [ ] **Step 5: 提交**

```bash
git add app/weeks.py tests/test_weeks.py
git commit -m "feat(weeks): extract_payloads_from_html 用于回填"
```

---

## Task 4: `app/build.py` — 抽出 `render_page` 并渲染归档页

**Files:**
- Modify: `app/build.py`
- Test: `tests/test_build.py`（本任务只加 `render_page` 的轻量断言，集成在 Task 6）

**Interfaces:**
- Produces: `render_page(html: str, papers: list, weekly: dict, trending: dict, weeks: list, week_label: str|None, weeks_base: str, runtime: bool) -> str`
- Consumes: `app.weeks.attach_hrefs`

- [ ] **Step 1: 写失败测试**

在 `tests/test_build.py` 顶部 import 区加 `from app import build as build_app`，并在 `MirrorBuildTest` 同级新增：

```python
class RenderPageTest(unittest.TestCase):
    def test_render_page_inlines_weeks_and_label_and_prefixes_paper_links(self):
        html = (
            '<html><head></head><body>'
            '<script>const res=await fetch("/api/papers");const data=await res.json();'
            'const wr=await fetch("/api/weekly");const w=await wr.json();</script>'
            '<a href="/paper/abc">x</a><a href="/paper/${escapeAttr(p.id)}">y</a>'
            '</body></html>'
        )
        weeks = [{"label": "2026-06-26", "title": "06-26~07-03", "current": False, "href": "../week/2026-06-26.html"}]
        out = build_app.render_page(html, [{"id": "abc"}], {"overview": ""}, {"items": []},
                                    weeks, week_label="2026-06-26", weeks_base="../", runtime=False)
        self.assertIn("window.__PAPERS__", out)
        self.assertIn("window.__WEEKS__", out)
        self.assertIn('"2026-06-26"', out)  # week_label inlined
        self.assertIn('window.__WEEKS_BASE__="../"', out)
        # fetch rewritten to globals
        self.assertNotIn('fetch("/api/papers")', out)
        # paper links prefixed with ../
        self.assertIn('href="../paper/abc.html"', out)
        self.assertIn('href="../paper/${escapeAttr(p.id)}.html"', out)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m unittest tests.test_build.RenderPageTest -v`
Expected: FAIL `AttributeError: module 'app.build' has no attribute 'render_page'`

- [ ] **Step 3: 重构 `app/build.py`**

把现有 `rewrite_index` 替换为更通用的 `render_page`，并让旧调用点经新函数。修改 `app/build.py`：

替换 `rewrite_index` 函数（第 43-73 行）为：

```python
def render_page(html, papers, weekly, trending, weeks, week_label, weeks_base, runtime):
    """Inline all payloads + switcher globals into page.py's HTML, rewrite fetches
    to read globals, and rewrite /paper/<id> links to relative {weeks_base}paper/<id>.html.

    ``weeks`` already carries per-entry ``href`` (see app.weeks.attach_hrefs).
    ``week_label`` is this page's label, or None for the current-week page.
    """
    inline = (
        '<script>window.__PAPERS__ = '
        + json.dumps(papers, ensure_ascii=False)
        + ';window.__WEEKLY__ = '
        + json.dumps(weekly, ensure_ascii=False)
        + ';window.__TRENDING__ = '
        + json.dumps(trending, ensure_ascii=False)
        + ';window.__WEEKS__ = '
        + json.dumps(weeks, ensure_ascii=False)
        + ';window.__WEEK_LABEL__ = '
        + json.dumps(week_label, ensure_ascii=False)
        + ';window.__WEEKS_BASE__ = '
        + json.dumps(weeks_base, ensure_ascii=False)
        + ';</script>'
    )
    html = re.sub(
        r'const\s+res\s*=\s*await\s*fetch\("/api/papers"\)\s*;\s*'
        r'const\s+data\s*=\s*await\s+res\.json\(\)\s*;',
        'const data = window.__PAPERS__;',
        html,
    )
    html = re.sub(
        r'const\s+wr\s*=\s*await\s*fetch\("/api/weekly"\)\s*;\s*'
        r'const\s+w\s*=\s*await\s*wr\.json\(\)\s*;',
        'const w = window.__WEEKLY__;',
        html,
    )
    html = html.replace("<script>", inline + "\n    <script>", 1)
    # rewrite /paper/<id> links (incl. JS template-literal form) to relative
    html = re.sub(r'href="/paper/([^"]+)"', r'href="' + weeks_base + r'paper/\1.html"', html)
    return html
```

并在文件顶部 import 区加：

```python
sys.path.insert(0, str(ROOT))
from app import weeks as weeks_mod
```

（`weeks` 作为参数名与模块冲突，故别名 `weeks_mod`。）

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m unittest tests.test_build.RenderPageTest -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/build.py tests/test_build.py
git commit -m "feat(build): 抽出 render_page 支持归档页渲染(内联WEEKS/LABEL/BASE+前缀paper链接)"
```

---

## Task 5: `app/build.py` — 写当前周归档 + 渲染历史周 + backfill

**Files:**
- Modify: `app/build.py`（`mirror()` 与 `main()`）
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `app.weeks.{parse_week_meta, write_archive, build_manifest, read_archive, attach_hrefs, extract_payloads_from_html, read_manifest}`
- Produces: `mirror()` 每次构建写 `data/weeks/<当前label>.json` + manifest + `site/week/<历史label>.html`；`--backfill` 从现有 `site/index.html` 回填。

- [ ] **Step 1: 写失败测试**

在 `tests/test_build.py` 新增（沿用既有的 server fixture 模式，但本测试不需要 server，直接造 site/index.html）：

```python
class WeekArchiveBuildTest(unittest.TestCase):
    def setUp(self):
        self.site_dir = ROOT / "site"
        self.weeks_dir = ROOT / "data" / "weeks"
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)
        if self.weeks_dir.exists():
            shutil.rmtree(self.weeks_dir)
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)
        if self.weeks_dir.exists():
            shutil.rmtree(self.weeks_dir)

    def _seed_index(self, overview):
        """Stand in for an existing built index.html with inlined payloads."""
        html = (
            '<html><head></head><body>'
            f'<script>window.__PAPERS__ = [{{"id":"p1","title":"T","date":"2026-06-28"}}];'
            f'window.__WEEKLY__ = {{"overview":"{overview}","highlights":[]}};'
            f'window.__TRENDING__ = {{"items":[]}};</script>'
            '</body></html>'
        )
        self.site_dir.mkdir(parents=True, exist_ok=True)
        (self.site_dir / "index.html").write_text(html, encoding="utf-8")

    def test_backfill_creates_archive_from_existing_index(self):
        self._seed_index("本周端侧动态(06-26~07-03)：...")
        result = subprocess.run(
            [sys.executable, str(ROOT / "app" / "build.py"), "--backfill"],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=f"{result.stdout}\n{result.stderr}")
        a = weeks_mod.read_archive("2026-06-26")
        self.assertIsNotNone(a)
        self.assertEqual(a["papers"], [{"id": "p1", "title": "T", "date": "2026-06-28"}])
        self.assertEqual(a["weekly"]["overview"], "本周端侧动态(06-26~07-03)：...")

    def test_backfill_missing_index_is_noop(self):
        # no site/index.html -> backfill prints warning, returns 0, no archive
        result = subprocess.run(
            [sys.executable, str(ROOT / "app" / "build.py"), "--backfill"],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(weeks_mod.read_manifest(), [])
```

并在 `tests/test_build.py` import 区加：

```python
from app import weeks as weeks_mod
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m unittest tests.test_build.WeekArchiveBuildTest -v`
Expected: FAIL（`--backfill` 未识别 / archive 不存在）

- [ ] **Step 3: 改 `mirror()` + 加 `backfill()` + 改 `main()`**

修改 `app/build.py` 的 `mirror` 函数体（替换第 81-116 行的 `mirror` 整体）：

```python
def mirror(server: str, site: Path = SITE) -> int:
    """Mirror server into site/: write current-week archive + manifest, render
    index.html (current) and site/week/<label>.html (each past week)."""
    site.mkdir(parents=True, exist_ok=True)
    (site / "paper").mkdir(parents=True, exist_ok=True)

    print(f"[BUILD] mirroring {server} -> {site}")
    papers_payload = fetch_json(f"{server}/api/papers")
    papers = list(papers_payload.get("papers") or [])
    try:
        weekly_payload = fetch_json(f"{server}/api/weekly")
    except Exception:
        weekly_payload = {"overview": "", "highlights": []}
    try:
        trending_payload = fetch_json(f"{server}/api/trending")
    except Exception:
        trending_payload = {"items": []}

    import datetime
    fallback_iso = datetime.date.today().isoformat()
    meta = weeks_mod.parse_week_meta(weekly_payload.get("overview", ""), fallback_iso)
    current_label = meta["label"]

    # 1) archive current week + manifest
    weeks_mod.write_archive(meta, papers, weekly_payload, trending_payload)
    manifest = weeks_mod.build_manifest(current_label)

    # 2) render site/index.html (current) — weeks_base="" (root)
    index_html = render_page(
        fetch_text(f"{server}/"),
        papers, weekly_payload, trending_payload,
        weeks_mod.attach_hrefs(manifest, weeks_base="", runtime=False),
        week_label=None, weeks_base="", runtime=False,
    )
    (site / "index.html").write_text(index_html, encoding="utf-8")
    print(f"[BUILD] index.html ({len(papers)} papers, week={current_label})")

    # 3) render site/week/<label>.html for every PAST week
    for entry in manifest:
        if entry["current"]:
            continue
        rec = weeks_mod.read_archive(entry["label"])
        if not rec:
            continue
        (site / "week").mkdir(parents=True, exist_ok=True)
        page = render_page(
            fetch_text(f"{server}/"),
            rec["papers"], rec["weekly"], rec["trending"],
            weeks_mod.attach_hrefs(manifest, weeks_base="../", runtime=False),
            week_label=entry["label"], weeks_base="../", runtime=False,
        )
        (site / "week" / f"{entry['label']}.html").write_text(page, encoding="utf-8")
        print(f"[BUILD] week/{entry['label']}.html")

    # 4) detail pages (unchanged from before)
    for p in papers:
        pid = str(p.get("id") or "")
        if not pid:
            continue
        detail_html = rewrite_detail(fetch_text(f"{server}/paper/{pid}"))
        (site / "paper" / f"{pid}.html").write_text(detail_html, encoding="utf-8")

    print(f"[BUILD] done: index.html + {len(papers)} detail + "
          f"{sum(1 for e in manifest if not e['current'])} week archive page(s)")
    return 0
```

在 `mirror` 之后、`main` 之前新增 `backfill`：

```python
def backfill(site: Path = SITE) -> int:
    """One-time: extract the inlined payloads from an existing site/index.html
    into data/weeks/<label>.json so the first new-week build has a past week to render.
    """
    idx = site / "index.html"
    if not idx.exists():
        print("[BACKFILL] no site/index.html to backfill from — nothing to do")
        return 0
    html = idx.read_text(encoding="utf-8")
    payloads = weeks_mod.extract_payloads_from_html(html)
    import datetime
    fallback_iso = datetime.date.today().isoformat()
    meta = weeks_mod.parse_week_meta(
        payloads["weekly"].get("overview", ""), fallback_iso)
    weeks_mod.write_archive(meta, payloads["papers"], payloads["weekly"], payloads["trending"])
    weeks_mod.build_manifest(meta["label"])
    print(f"[BACKFILL] wrote data/weeks/{meta['label']}.json from existing index.html")
    return 0
```

修改 `main`（替换第 119-129 行）：

```python
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Mirror a running display server into a static site/."
    )
    parser.add_argument("--server", default=DEFAULT_SERVER,
                        help=f"Display server base URL (default: {DEFAULT_SERVER}).")
    parser.add_argument("--backfill", action="store_true",
                        help="Backfill data/weeks/ from an existing site/index.html (one-time).")
    args = parser.parse_args(argv)
    if args.backfill:
        return backfill()
    return mirror(args.server)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m unittest tests.test_build.WeekArchiveBuildTest -v`
Expected: PASS（2 个用例）

- [ ] **Step 5: 跑全部 build 测试确认未回归**

Run: `python -m unittest tests.test_build -v`
Expected: PASS（含既有 `MirrorBuildTest` + `RenderPageTest` + `WeekArchiveBuildTest`）

注：`MirrorBuildTest` 现在会额外写 `data/weeks/`，其 `_cleanup_site` 只清 site/；为防污染，在 `MirrorBuildTest.setUp` 里也清 `data/weeks/`。修改 `tests/test_build.py` 的 `MirrorBuildTest.setUp`，在 `self.site_dir` 清理后加：

```python
        self.weeks_dir = ROOT / "data" / "weeks"
        if self.weeks_dir.exists():
            shutil.rmtree(self.weeks_dir)
```

并在 `MirrorBuildTest` 加清理方法（紧接 `_cleanup_site` 之后）：

```python
    def _cleanup_weeks(self):
        if (ROOT / "data" / "weeks").exists():
            shutil.rmtree(ROOT / "data" / "weeks")
```

并在 `setUp` 的 `self.addCleanup(self._cleanup_site)` 后加 `self.addCleanup(self._cleanup_weeks)`。

- [ ] **Step 6: 提交**

```bash
git add app/build.py tests/test_build.py
git commit -m "feat(build): 每次build写当前周归档+渲染历史周; --backfill从现有index回填"
```

---

## Task 6: `app/server.py` — `/api/weeks`、`/week/<label>` 路由 + `/` 注入 `__WEEKS__`

**Files:**
- Modify: `app/server.py`（`do_GET`）
- Test: `tests/test_server_weeks.py`（新建）

**Interfaces:**
- Consumes: `app.weeks.{read_manifest, read_archive, attach_hrefs, parse_week_meta}`、`app.build.render_page`
- Produces: `GET /api/weeks` → manifest；`GET /week/<label>` → 冻结 HTML；`GET /` → INDEX_HTML 注入 `window.__WEEKS__`。

- [ ] **Step 1: 写失败测试**

创建 `tests/test_server_weeks.py`：

```python
#!/usr/bin/env python3
"""Server routes for week archive browsing."""
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agent"))

from app import server as server_app
from app import weeks as weeks_mod


class ServerWeeksTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        db_path = Path(self._tmp.name) / "papers.sqlite"
        # redirect weeks dir into tmp so tests don't touch real data/weeks
        self._orig_wd = weeks_mod.WEEKS_DIR
        weeks_mod.WEEKS_DIR = Path(self._tmp.name) / "weeks"
        self.addCleanup(self._restore)

        self.httpd = server_app.create_server(("127.0.0.1", 0), db_path)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_port}"
        self.addCleanup(self._stop)

    def _restore(self):
        weeks_mod.WEEKS_DIR = self._orig_wd

    def _stop(self):
        self.httpd.shutdown()
        self.thread.join(timeout=5)
        self.httpd.server_close()

    def _get(self, path):
        import urllib.request
        with urllib.request.urlopen(self.base_url + path, timeout=10) as r:
            return r.read().decode("utf-8")

    def _seed(self):
        meta = {"label": "2026-06-26", "title": "06-26~07-03",
                "range": {"start": "2026-06-26", "end": "2026-07-03"}}
        weeks_mod.write_archive(meta, [{"id": "p1"}], {"overview": "ov(06-26~07-03)"}, {"items": []})
        weeks_mod.build_manifest("2026-07-02")  # current is some other week

    def test_api_weeks_returns_manifest(self):
        self._seed()
        body = self._get("/api/weeks")
        m = json.loads(body)
        self.assertEqual(m[0]["label"], "2026-06-26")
        self.assertFalse(m[0]["current"])  # current is 2026-07-02 which has no archive

    def test_week_route_serves_frozen_page(self):
        self._seed()
        html = self._get("/week/2026-06-26")
        self.assertIn("window.__PAPERS__", html)
        self.assertIn('"p1"', html)
        self.assertIn('window.__WEEK_LABEL__ = "2026-06-26"', html)
        # frozen: fetches rewritten to globals
        self.assertNotIn('fetch("/api/papers")', html)

    def test_week_route_404_for_unknown(self):
        try:
            self._get("/week/nope")
            self.fail("expected 404")
        except Exception as e:
            self.assertIn("404", str(e))

    def test_root_injects_weeks_global(self):
        self._seed()
        html = self._get("/")
        self.assertIn("window.__WEEKS__", html)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m unittest tests.test_server_weeks -v`
Expected: FAIL（路由不存在，`/api/weeks` 走到 404）

- [ ] **Step 3: 改 `app/server.py`**

顶部 import 区（第 26 行 `from app.page import INDEX_HTML` 之后）加：

```python
from app import weeks as weeks_mod
from app import build as build_app
```

在 `do_GET` 里，把 `if parsed.path == "/":` 分支（第 191-193 行）替换为：

```python
        if parsed.path == "/":
            manifest = weeks_mod.attach_hrefs(
                weeks_mod.read_manifest(), weeks_base="", runtime=True)
            html = INDEX_HTML.replace(
                "<script>",
                '<script>window.__WEEKS__ = '
                + json.dumps(manifest, ensure_ascii=False)
                + ';window.__WEEK_LABEL__ = null;'
                + 'window.__WEEKS_BASE__ = "";</script>\n    <script>',
                1)
            self.send_html(html)
            return
```

在 `/api/trending` 分支之后、`/paper/` 分支之前（第 212 行之后）加：

```python
        if parsed.path == "/api/weeks":
            self.send_json(200, {"weeks": weeks_mod.read_manifest()})
            return
        if parsed.path.startswith("/week/"):
            label = parsed.path.rsplit("/", 1)[-1]
            rec = weeks_mod.read_archive(label)
            if rec is None:
                self.send_json(404, {"ok": False, "error": f"week {label} not found"})
                return
            manifest = weeks_mod.attach_hrefs(
                weeks_mod.read_manifest(), weeks_base="", runtime=True)
            page = build_app.render_page(
                INDEX_HTML, rec["papers"], rec["weekly"], rec["trending"],
                manifest, week_label=label, weeks_base="", runtime=True)
            self.send_html(page)
            return
```

注意：`/api/weeks` 返回 `{"weeks": [...]}` 以与既有 `{"papers":...}`、`{"items":...}` 风格一致；测试里取 `m[0]` 即 `body["weeks"][0]`。修正测试 Step 1 的 `test_api_weeks_returns_manifest`：`m = json.loads(body)["weeks"]`。

（修正：将 Step 1 测试中 `m = json.loads(body)` 改为 `m = json.loads(body)["weeks"]`。）

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m unittest tests.test_server_weeks -v`
Expected: PASS（4 个用例）

- [ ] **Step 5: 提交**

```bash
git add app/server.py tests/test_server_weeks.py
git commit -m "feat(server): /api/weeks + /week/<label> 冻结页 + /注入__WEEKS__"
```

---

## Task 7: `app/page.py` — 顶部周切换器 UI

**Files:**
- Modify: `app/page.py`（CSS + header markup + JS）

**Interfaces:**
- Consumes: 运行时/静态均内联的 `window.__WEEKS__`（含 `href`）、`window.__WEEK_LABEL__`、`window.__WEEKS_BASE__`。

- [ ] **Step 1: 写失败测试（结构断言）**

在 `tests/test_build.py` 加：

```python
class PageSwitcherTest(unittest.TestCase):
    def test_index_html_has_switcher_select_and_js(self):
        from app.page import INDEX_HTML
        self.assertIn('id="week-switch"', INDEX_HTML)
        self.assertIn("renderWeekSwitch", INDEX_HTML)
        # reads the inlined globals
        self.assertIn("window.__WEEKS__", INDEX_HTML)
        self.assertIn("window.__WEEK_LABEL__", INDEX_HTML)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m unittest tests.test_build.PageSwitcherTest -v`
Expected: FAIL（`id="week-switch"` 不存在）

- [ ] **Step 3: 改 `app/page.py`**

3a. CSS：在 `.nav-link:hover{...}`（第 32 行）之后加：

```css
    .week-switch{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--amber);border:1px solid var(--amber);border-radius:3px;padding:3px 6px;background:#fbfcfd;cursor:pointer}
    .week-switch:hover{border-color:var(--ink)}
```

3b. header markup：把 `.scope-top` 内的 nav 链接行（第 134 行）改为：

```html
        <a class="nav-link" href="notes.html">调研笔记 ↗</a>
        <select class="week-switch" id="week-switch" title="切换周"></select>
```

注意：`notes.html` 在 `site/week/` 子目录下需要 `../notes.html`——但因 build.py 的 `render_page` 未重写 `notes.html` 链接，需在 `render_page` 里追加一条重写。修改 Task 4 的 `render_page`，在 paper 链接重写之后加：

```python
    html = re.sub(r'href="notes\.html"', f'href="{weeks_base}notes.html"', html)
```

（更新 Task 4 Step 3 的 `render_page` 实现追加此行；若 Task 4 已提交，作为本任务的一部分补进 `app/build.py` 的 `render_page`。）

3c. JS：在 `loadTrending().catch(()=>{});`（第 300 行）之前加：

```js
    function renderWeekSwitch(){
      const ws=window.__WEEKS__||[];
      const sel=document.querySelector('#week-switch');
      if(!ws.length){sel.style.display='none';return;}
      const mine=window.__WEEK_LABEL__||null;
      sel.innerHTML=ws.map(w=>{
        const isMine=(w.current&&mine===null)||(w.label===mine);
        return `<option value="${escapeAttr(w.href)}"${isMine?' selected':''}>${w.current?'本周 · ':''}${escapeHtml(w.title)}</option>`;
      }).join('');
    }
    document.querySelector('#week-switch').addEventListener('change',e=>{if(e.target.value&&e.target.value!==location.pathname)location.href=e.target.value;});
    renderWeekSwitch();
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m unittest tests.test_build.PageSwitcherTest -v`
Expected: PASS

- [ ] **Step 5: 跑全部测试确认未回归**

Run: `python -m unittest tests.test_build tests.test_server_weeks tests.test_weeks tests.test_research_pipeline -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add app/page.py app/build.py tests/test_build.py
git commit -m "feat(page): 顶部周切换器<select>+JS(renderWeekSwitch); notes链接按weeks_base重写"
```

---

## Task 8: 端到端回填 + 双周切换验证

**Files:**
- Test: `tests/test_build.py`（集成用例）

**Interfaces:**
- Consumes: Task 5 `--backfill`、Task 4/5 `mirror`、Task 6 路由、Task 7 切换器。

- [ ] **Step 1: 写失败测试**

在 `tests/test_build.py` 加：

```python
class TwoWeekFlowTest(unittest.TestCase):
    """Backfill last week from an existing index, then build a new week against
    a live server, and assert both weeks render + switcher present."""

    def setUp(self):
        self.site_dir = ROOT / "site"
        self.weeks_dir = ROOT / "data" / "weeks"
        for d in (self.site_dir, self.weeks_dir):
            if d.exists():
                shutil.rmtree(d)
        self.addCleanup(self._cleanup)
        # real server + one paper (reuse fixtures)
        self._orig_link = None
        import research_run
        patcher = unittest.mock.patch("research_run.is_link_alive", return_value=True)
        self.addCleanup(patcher.stop)
        patcher.start()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        db_path = Path(self._tmp.name) / "papers.sqlite"
        self.httpd = server_app.create_server(("127.0.0.1", 0), db_path)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_port}"
        self.addCleanup(self._stop)

    def _cleanup(self):
        for d in (self.site_dir, self.weeks_dir):
            if d.exists():
                shutil.rmtree(d)

    def _stop(self):
        self.httpd.shutdown()
        self.thread.join(timeout=5)
        self.httpd.server_close()

    def test_backfill_then_build_renders_both_weeks(self):
        # 1) seed an "old" built index with last week's inlined payload
        old_html = ('<html><body>'
                    '<script>window.__PAPERS__ = [{"id":"old","title":"Old","date":"2026-06-28"}];'
                    'window.__WEEKLY__ = {"overview":"本周动态(06-26~07-03)：...","highlights":[]};'
                    'window.__TRENDING__ = {"items":[]};</script></body></html>')
        self.site_dir.mkdir(parents=True, exist_ok=True)
        (self.site_dir / "index.html").write_text(old_html, encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "app" / "build.py"), "--backfill"],
                           cwd=ROOT, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, msg=f"{r.stdout}\n{r.stderr}")

        # 2) publish a "new week" paper to the live server and build
        payload = research_run.validate_payload(
            run_payload(valid_paper(id="new-week-paper", title="New Week Paper",
                                   date=TODAY.isoformat())),
            today=TODAY)
        # put a current-week overview in weekly_summary.json so parse picks 07-02
        wp = ROOT / "data" / "weekly_summary.json"
        wp.parent.mkdir(parents=True, exist_ok=True)
        wp.write_text(json.dumps(
            {"overview": "本周动态(07-02~07-09)：...", "highlights": []},
            ensure_ascii=False), encoding="utf-8")
        self.addCleanup(lambda: wp.unlink(missing_ok=True))
        publish_results.publish_payload(self.base_url, payload)

        r = subprocess.run([sys.executable, str(ROOT / "app" / "build.py"),
                            "--server", self.base_url],
                           cwd=ROOT, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, msg=f"{r.stdout}\n{r.stderr}")

        # 3) current index = new week, has switcher
        idx = (self.site_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn("New Week Paper", idx)
        self.assertIn("window.__WEEKS__", idx)
        self.assertIn('window.__WEEK_LABEL__ = null', idx)

        # 4) past week page rendered
        past = self.site_dir / "week" / "2026-06-26.html"
        self.assertTrue(past.exists(), "past week page not rendered")
        past_html = past.read_text(encoding="utf-8")
        self.assertIn("Old", past_html)
        self.assertIn('window.__WEEK_LABEL__ = "2026-06-26"', past_html)
        # switcher hrefs in subdir use ../ prefix
        self.assertIn("../index.html", past_html)
        self.assertIn("../week/2026-06-26.html", past_html)
```

（`valid_paper` 已在 `tests/test_build.py` 顶部定义为接受 `**overrides`，故 `id=`/`title=`/`date=` 可直接覆盖。`run_payload` 接受 `*papers`，传一个 paper 即可。）

- [ ] **Step 2: 跑测试确认失败/通过**

Run: `python -m unittest tests.test_build.TwoWeekFlowTest -v`
Expected: 若前序任务都对，PASS。若失败，根据失败点修对应模块。

- [ ] **Step 3: 跑全量测试**

Run: `python -m unittest discover -s tests -v`
Expected: PASS（全部）

- [ ] **Step 4: 人工验证（本地）**

```bash
python app/build.py --backfill   # 回填上一周（当前 site/index.html 是 06-26~07-03）
# 起服务器，本周 weekly_summary.json 写好后：
python app/server.py --port 8001
# 另一终端：
python app/build.py --server http://127.0.0.1:8001
# 浏览器打开 site/index.html，确认顶部下拉有「本周」+「06-26~07-03」，
# 切到 06-26 页能看到上周论文列表，切回本周正常。
```

Expected: 切换器在两周间跳转正常，归档页 paper 链接点开不 404。

- [ ] **Step 5: 提交**

```bash
git add tests/test_build.py
git commit -m "test: 端到端回填+双周切换集成测试"
```

---

## Self-Review

**1. Spec coverage:**
- §3.1 数据模型 → Task 1（parse）+ Task 2（archive/manifest/href）。✓
- §3.2 归档触发（每次 build 写当前周 + 渲染历史周）→ Task 5。✓
- §3.3 一次性回填 → Task 5 `--backfill` + Task 8 验证。✓
- §3.4 render_page → Task 4。✓
- §3.5 运行时路由 `/api/weeks`、`/week/<label>`、`/` 注入 → Task 6。✓
- §3.6 切换器 UI → Task 7。✓
- §5 错误处理（归档缺失 404、manifest 空只显本周、fetch 失败回退）→ Task 6（404）、Task 2（read_manifest 返回 []）、Task 5（fetch try/except）。✓
- §6 测试 → 各 Task TDD + Task 8 端到端 + 人工。✓

**2. Placeholder scan:** 无 TBD/TODO；每个代码步骤都给了完整代码。

**3. Type consistency:**
- `parse_week_meta` 返回 `{label,title,range}` — Task 2 `write_archive(meta,...)` 接收同结构。✓
- `build_manifest` 返回 `[{label,title,range,current}]` — `attach_hrefs` 加 `href`。✓
- `render_page(html,papers,weekly,trending,weeks,week_label,weeks_base,runtime)` 签名在 Task 4、Task 5、Task 6 三处调用一致。✓
- `window.__WEEKS__` 含 `href`，page.py JS 读 `w.href` — Task 7 与 Task 2 `attach_hrefs` 一致。✓
- Task 7 3b 追加的 `notes.html` 重写行与 Task 4 `render_page` 同函数——已在 Task 7 Step 3 说明补进 `render_page`。✓

注：Task 6 Step 1 测试里 `/api/weeks` 取值已在 Step 3 修正为 `["weeks"]`，实现与测试一致。
