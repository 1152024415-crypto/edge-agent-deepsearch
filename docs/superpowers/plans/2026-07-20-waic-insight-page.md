# WAIC 洞察页 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在端侧 AI 雷达站新增 `site/waic.html`——一个 WAIC 2026 专项调研报告页（左侧章节 TOC + 右侧 marked.js+KaTeX 渲染），内容由我调研产出，架构完全复用 SNN 洞察页。

**Architecture:** 复用 `app/snn_page.py` + `agent/build_snn.py` 模式（已验证可用）：`app/waic_page.py`（= snn_page 模板，改标题/fetch 路径）+ `agent/build_waic.py`（= build_snn，源 `data/waic-insight.md`）→ `site/waic.html` + `site/waic/WAIC-insight.md`。index nav 加「WAIC」链接。

**Tech Stack:** Python 3.11（build 脚本）、HTML/CSS/JS（模板，无前端框架）、marked.js+KaTeX（CDN）、unittest、GitHub Pages。

## Global Constraints

- 复用 SNN 页 RADAR 终端美学：CSS 变量 `--bg:#eef1f3;--panel:#fff;--ink:#0b1a24;--amber:#c2410c`，IBM Plex Mono/Sans，`@media max-width:760px` 侧栏堆叠。
- WAIC 2026 专项（不覆盖历史）；内容由我 WebFetch 权威源（新华网/央视/财新/财联社/上观/厂商官网）核实产出，不编造。
- 链接用**权威媒体直链或厂商官方域名**，**不用 google news wrapper**（吸取上轮阶跃星辰链接教训）。
- 静态精选，不拉 run 数据，手动刷新（同 SNN）。
- Windows bash；CRLF 警告可接受；commit 末尾 `Co-Authored-By: Claude <noreply@anthropic.com>`。
- 工作目录 `D:\proj\edge_agent`，master 分支直接做。

---

### Task 1: gate_release 加 waic.html 存在检查（TDD）

**Files:**
- Modify: `app/gates/gate_release.py`（加 `check_waic_page` + 进 `run_all`）
- Test: `tests/test_gate_release.py`（加 1 测试 + 改 `_seed_good`）

**Interfaces:**
- Consumes: `gate_release._err`（已存在）
- Produces: `check_waic_page(root, errors)` —— 检查 `site/waic.html` 存在。

- [ ] **Step 1: 改 `_seed_good` 加 waic.html，跑现有测试确认全过（基线）**

在 `tests/test_gate_release.py` 的 `_seed_good` 末尾（`site/snn.html` 那行后）加：
```python
        _write(self.root, "site/waic.html", "<html>waic</html>")
```
Run: `python -m unittest tests.test_gate_release -q`
Expected: PASS（13 测试基线）

- [ ] **Step 2: 写失败测试 — waic.html 缺失要 FAIL**

在 `GateReleaseTest` 类内（`test_fail_when_snn_page_missing` 后）加：
```python
    def test_fail_when_waic_page_missing(self):
        self._seed_good()
        (self.root / "site" / "waic.html").unlink()
        errs = gr.run_all(self.root)
        self.assertTrue(any("waic.html" in e and "missing" in e for e in errs), errs)
```
Run: `python -m unittest tests.test_gate_release.GateReleaseTest.test_fail_when_waic_page_missing -q`
Expected: FAIL（`check_waic_page` 还没实现）

- [ ] **Step 3: 实现 `check_waic_page` + 进 `run_all`**

在 `app/gates/gate_release.py` 的 `check_snn_page` 函数后加：
```python
def check_waic_page(root: Path, errors: list) -> None:
    """site/waic.html must exist — the WAIC insight page nav link points at it."""
    if not (root / "site" / "waic.html").exists():
        _err(errors, "site/waic.html missing — run agent/build_waic.py (WAIC 洞察 nav 链接会 404)")
```
在 `run_all` 末尾 `check_snn_page` 后加 `check_waic_page(root, errors)`：
```python
def run_all(root: Path) -> list:
    errors = []
    check_contract(root, errors)
    check_links(root, errors)
    check_highlights(root, errors)
    check_vendor_tier(root, errors)
    check_trending_freshness(root, errors)
    check_snn_page(root, errors)
    check_waic_page(root, errors)
    return errors
```

- [ ] **Step 4: 跑全测试确认 PASS**

Run: `python -m unittest tests.test_gate_release -q`
Expected: PASS（14 测试）

- [ ] **Step 5: Commit**

```bash
git add app/gates/gate_release.py tests/test_gate_release.py
git commit -m "feat(gate): 加 waic.html 存在检查(+1测试)"
```

---

### Task 2: app/waic_page.py HTML 模板（TOC + KaTeX）

**Files:**
- Create: `app/waic_page.py`
- Test: `tests/test_waic_page.py`（新）

**Interfaces:**
- Consumes: 无（纯模板字符串）
- Produces: `WAIC_HTML`（str，HTML 模板）

- [ ] **Step 1: 写失败测试 — WAIC_HTML 存在且含关键标记**

Create `tests/test_waic_page.py`:
```python
#!/usr/bin/env python3
"""waic_page template renders the WAIC insight page shell."""
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.waic_page import WAIC_HTML

class WaicPageTest(unittest.TestCase):
    def test_template_has_key_markers(self):
        self.assertIn("<!doctype html>", WAIC_HTML)
        self.assertIn("marked.min.js", WAIC_HTML)
        self.assertIn("katex", WAIC_HTML.lower())
        self.assertIn("WAIC-insight.md", WAIC_HTML)
        self.assertIn('id="toc"', WAIC_HTML)
        self.assertIn('id="art"', WAIC_HTML)
        self.assertIn("index.html", WAIC_HTML)
    def test_template_has_toc_autobuild_js(self):
        self.assertIn("querySelectorAll('h2')", WAIC_HTML)
        self.assertIn("IntersectionObserver", WAIC_HTML)

if __name__ == "__main__":
    unittest.main()
```
Run: `python -m unittest tests.test_waic_page -q`
Expected: FAIL（`app/waic_page.py` 不存在）

- [ ] **Step 2: 实现 `app/waic_page.py`（= snn_page 模板，标题/fetch 改 WAIC）**

Create `app/waic_page.py`：拷贝 `app/snn_page.py` 的 `SNN_HTML` 全文，做 3 处替换：
1. 模块 docstring：`SNN insight page` → `WAIC insight page`，`site/snn/SNN-insight.md` → `site/waic/WAIC-insight.md`
2. 变量名 `SNN_HTML` → `WAIC_HTML`
3. 模板内：`<title>RADAR · SNN 洞察</title>` → `<title>RADAR · WAIC 洞察</title>`；`<h1>RADAR<span class="sub">SNN 洞察 · spiking neural networks</span></h1>` → `<h1>RADAR<span class="sub">WAIC 洞察 · 世界人工智能大会 2026</span></h1>`；`var MD_URL = 'snn/SNN-insight.md';` → `var MD_URL = 'waic/WAIC-insight.md';`

CSS/JS（TOC 自动生成 + IntersectionObserver + KaTeX auto-render + marked.js）完全照搬 snn_page，不改。

- [ ] **Step 3: 跑测试确认 PASS**

Run: `python -m unittest tests.test_waic_page -q`
Expected: PASS（2 测试）

- [ ] **Step 4: Commit**

```bash
git add app/waic_page.py tests/test_waic_page.py
git commit -m "feat(waic): waic_page.py HTML 模板(TOC自动生成+KaTeX)"
```

---

### Task 3: agent/build_waic.py + 最小 waic-insight.md 脚手架（TDD）

**Files:**
- Create: `agent/build_waic.py`
- Create: `data/waic-insight.md`（最小脚手架，Task 4 再填）
- Test: `tests/test_build_waic.py`（新）

**Interfaces:**
- Consumes: `app.waic_page.WAIC_HTML`（Task 2 产出）
- Produces: `agent/build_waic.main()` —— 读源 md → 拷到 `site/waic/WAIC-insight.md` → 写 `site/waic.html`

- [ ] **Step 1: 写最小脚手架 waic-insight.md**

Create `data/waic-insight.md`：
```markdown
# WAIC 洞察：世界人工智能大会 2026

> 脚手架，Task 4 填充完整 8 节内容。

## 1. WAIC 2026 概览

(待填)
```

- [ ] **Step 2: 写失败测试 — build_waic 产出 waic.html + waic/md**

Create `tests/test_build_waic.py`（仿 `tests/test_build_snn.py`，把 build_snn→build_waic、SNN_SRC→WAIC_SRC、SNN_SITE→WAIC_SITE、SNN-insight→WAIC-insight）：
```python
#!/usr/bin/env python3
"""build_waic renders site/waic.html + copies site/waic/WAIC-insight.md."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BuildWaicTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.site = Path(self._tmp.name)
        self.src = Path(self._tmp.name) / "WAIC-insight.md"

    def _load(self, src_md_text):
        self.src.write_text(src_md_text, encoding="utf-8")
        os.environ["WAIC_SRC"] = str(self.src)
        os.environ["WAIC_SITE"] = str(self.site)
        spec = importlib.util.spec_from_file_location("build_waic", ROOT / "agent" / "build_waic.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_build_writes_html_and_md(self):
        mod = self._load("# title\n## 1. A\nbody\n")
        self.assertEqual(mod.main(), 0)
        self.assertTrue((self.site / "waic.html").exists())
        self.assertTrue((self.site / "waic" / "WAIC-insight.md").exists())
        html = (self.site / "waic.html").read_text(encoding="utf-8")
        self.assertIn("WAIC-insight.md", html)
        self.assertIn('id="art"', html)

    def test_build_returns_1_when_src_missing(self):
        os.environ["WAIC_SRC"] = str(self.site / "nope.md")
        os.environ["WAIC_SITE"] = str(self.site)
        spec = importlib.util.spec_from_file_location("build_waic", ROOT / "agent" / "build_waic.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.main(), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 跑测试确认 FAIL**

Run: `python -m unittest tests.test_build_waic -q`
Expected: FAIL（`agent/build_waic.py` 不存在）

- [ ] **Step 4: 实现 `agent/build_waic.py`（= build_snn，源/目标改 waic）**

Create `agent/build_waic.py`：拷贝 `agent/build_snn.py` 全文，做替换：
1. docstring：`SNN insight page` → `WAIC insight page`，`data/snn-insight.md` → `data/waic-insight.md`，`SNN_SRC`→`WAIC_SRC`，`SNN_SITE`→`WAIC_SITE`，`site/snn/`→`site/waic/`，`snn.html`→`waic.html`，`SNN-insight.md`→`WAIC-insight.md`
2. `DEFAULT_SRC = ROOT / "data" / "waic-insight.md"`
3. `from app.snn_page import SNN_HTML` → `from app.waic_page import WAIC_HTML`
4. `(site / "snn").mkdir` → `(site / "waic").mkdir`；`shutil.copy2(src, site / "snn" / "SNN-insight.md")` → `shutil.copy2(src, site / "waic" / "WAIC-insight.md")`；`(site / "snn.html").write_text(SNN_HTML, ...)` → `(site / "waic.html").write_text(WAIC_HTML, ...)`
5. print 行 `[SNN]` → `[WAIC]`

- [ ] **Step 5: 跑测试确认 PASS**

Run: `python -m unittest tests.test_build_waic -q`
Expected: PASS（2 测试）

- [ ] **Step 6: 跑真实 build 确认产出**

Run: `python agent/build_waic.py`
Expected: 输出 `[WAIC] wrote site/waic.html + site/waic/WAIC-insight.md ...`，`site/waic.html` + `site/waic/WAIC-insight.md` 存在。

- [ ] **Step 7: Commit**

```bash
git add agent/build_waic.py data/waic-insight.md tests/test_build_waic.py
git commit -m "feat(waic): build_waic.py 构建脚本+最小脚手架"
```

---

### Task 4: 调研 + 写 waic-insight.md 8 节内容

**Files:**
- Modify: `data/waic-insight.md`（Task 3 脚手架 → 完整 8 节）

**调研方法（WebFetch 权威源核实，不编造）**：
- 已有 Google News RSS 线索（探索阶段）：习近平主旨讲话+开源战略、华为昇腾950超节点真机、百度搭子+秒哒3.5（镇馆之宝）、腾讯智能体、阿里秒悟+魔法原子×速卖通、阶跃星辰 STEPX Neo（镇馆之宝）+期智研究院、印奇三道必答题、镇馆之宝（蛋白质设计智能体/智元机器人）、DAA 2030 22亿、需求爆炸。
- 对每条线索 WebFetch 权威源（新华网/央视网/财新/财联社/上观新闻/科学网/厂商官网）核实事实 + 取直链。优先厂商官方域名（huawei.com/baidu.com/alibaba.com/tencent.com/stepfun.com）；取不到用权威媒体直链（财新/财联社/上观/新华）。**不用 google news wrapper**。
- 这个任务调研重，建议派 subagent（给线索 + 8 节结构 + 来源规则 + 输出路径 data/waic-insight.md + 自检）。

**章节结构（8 节，WAIC 2026 专项）**：
1. **WAIC 2026 概览** — 时间（07-16/17 开幕·进行中）、地点（上海）、规格（习近平出席开幕式+主旨讲话+人工智能全球治理高级别会议）、主题
2. **主线：Agent 爆发 + 物理 AI** — 「AI 长出身体」叙事、AI 终端争夺战、印奇「行业三道必答题」
3. **国内厂商发布** — 华为昇腾950超节点真机、百度搭子+秒哒3.5、腾讯智能体、阿里秒悟团队版+魔法原子×速卖通、阶跃星辰 STEPX Neo+期智研究院、小米/字节等（每条带厂商/媒体直链 + 1-2 句大白话）
4. **镇馆之宝** — 阶跃 STEPX Neo、百度搭子、对话式蛋白质设计智能体、智元机器人 等
5. **AI 终端争夺战** — 模型厂下场造机（阶跃 STEPX Neo 等，连雷达之前那条阶跃星辰 highlight）
6. **端侧/边缘相关信号** — 昇腾950 硬件、AI 终端、agent 手机（连雷达端侧主线）
7. **治理与开源** — 习近平主旨讲话、中国开源战略、全球治理高级别会议
8. **产业信号** — 「需求爆炸」、DAA 2030 全球 22 亿、资本/估值

- [ ] **Step 1: 派 subagent 调研 + 写 8 节**

subagent prompt 要点：给上述 8 节结构 + 线索清单 + 来源规则（WebFetch 权威源/官方域名直链，不 google news wrapper，不编造）+ 输出 `D:\proj\edge_agent\data\waic-insight.md`（覆盖脚手架，h1 `# WAIC 洞察：世界人工智能大会 2026`）+ 自检（h2≥8、无 google news wrapper URL、每条发布带来源链接）。

- [ ] **Step 2: 验证 — h2≥8 + 无 google news wrapper + 链接在**

Run:
```bash
python -c "import re;h=open(r'data/waic-insight.md',encoding='utf-8').read();print('h2:',len(re.findall(r'^## ',h,re.M)));print('google news wrapper:',len(re.findall(r'news\.google\.com',h)));print('size:',len(h))"
```
Expected: h2≥8；google news wrapper=0；size 合理（>5KB）。

- [ ] **Step 3: 跑 build + chrome 看渲染**

Run: `python agent/build_waic.py`；起静态 server `cd site && python -m http.server 8092`（后台），chrome 打开 `http://127.0.0.1:8092/waic.html`，evaluate_script 查：`#art h2` ≥8、`#toc a` ≥8、`#art .katex` ≥0、`#art` 非空、无「加载失败」。

- [ ] **Step 4: Commit**

```bash
git add data/waic-insight.md
git commit -m "feat(waic): waic-insight.md 8节WAIC2026专项(权威源核实,直链不wrapper)"
```

---

### Task 5: index nav + build.py 链接重写 + 全量 build + gate + chrome 实测 + 部署

**Files:**
- Modify: `app/page.py`（加 WAIC nav 链接，挨着 SNN 洞察）
- Modify: `app/build.py`（render_page re.sub 重写 waic.html 链接）

**Interfaces:**
- Consumes: Task 3 的 `site/waic.html` + `site/waic/WAIC-insight.md`
- Produces: index.html 有 `waic.html` nav 链接；部署到 gh-pages。

- [ ] **Step 1: page.py 加 WAIC nav 链接**

在 `app/page.py` 找到 `<a class="nav-link" href="snn.html">SNN 洞察 ↗</a>` 行（grep 定位），旁加：
```python
        <a class="nav-link" href="waic.html">WAIC ↗</a>
```

- [ ] **Step 2: build.py render_page 静态链接重写加 waic.html**

`app/build.py` 的 `render_page` 里 `if not runtime:` 块，已有 `snn.html` re.sub：
```python
        html = re.sub(r'href="snn\.html"', f'href="{weeks_base}snn.html"', html)
```
旁加：
```python
        html = re.sub(r'href="waic\.html"', f'href="{weeks_base}waic.html"', html)
```

- [ ] **Step 3: 重启 server（page.py 改了）+ 全量 build + gate**

```bash
# 杀旧 8001 server（page.py 改了要重启）
PID=$(netstat -ano | grep ':8001' | grep LISTENING | head -1 | awk '{print $NF}'); taskkill //F //PID $PID
python app/server.py --host 127.0.0.1 --port 8001 &  # 后台
sleep 4
python agent/build_waic.py
python agent/build_snn.py
python app/build.py --server http://127.0.0.1:8001
python agent/build_notes.py
python app/gates/gate_all.py
```
Expected: gate_all 全过（含新 waic.html 检查）。

- [ ] **Step 4: chrome 实测**

chrome 打开 `http://127.0.0.1:8092/index.html`（8092 静态 server），确认 nav 有「WAIC」链接 → 点 → waic.html 200 渲染。再开 `http://127.0.0.1:8092/waic.html`：h2≥8、TOC≥8、KaTeX、无坏链、返回雷达链接 200。

- [ ] **Step 5: 部署 gh-pages**

```bash
git add app/page.py app/build.py
git commit -m "feat(waic): index 加 WAIC nav 链接 + build.py 链接重写"
git push origin master
git fetch origin gh-pages
TMP=$(mktemp -d) && git worktree add --detach "$TMP" origin/gh-pages
cp -r D:/proj/edge_agent/site/* "$TMP"/
cd "$TMP" && git add -A && git commit -m "deploy: WAIC洞察页上线(WAIC2026专项8节)" && git push origin HEAD:gh-pages
cd D:/proj/edge_agent && git worktree remove --force "$TMP"
```

- [ ] **Step 6: 验证 live**

sleep 70; curl live `https://1152024415-crypto.github.io/edge-agent-deepsearch/waic.html` → 200 + 含 WAIC-insight.md。chrome live 打开 waic.html → 渲染 + TOC + KaTeX + 无坏链。index live nav 有「WAIC」链接。

---

## Self-Review

**1. Spec coverage**:
- waic-insight.md 8 节 ✓ (Task 4)
- waic_page.py 模板 ✓ (Task 2)
- build_waic.py ✓ (Task 3)
- index nav ✓ (Task 5)
- gate waic.html 检查 ✓ (Task 1)
- chrome 实测 ✓ (Task 5 Step 4)
- 部署 ✓ (Task 5 Step 5-6)
- 权威源直链不 wrapper ✓ (Task 4 来源规则)

**2. Placeholder scan**: Task 4 是调研+内容任务，给了线索清单 + 8 节结构 + 来源规则 + 自检（不粘贴 prose，内容由 subagent WebFetch 调研产出）。代码 task（1/2/3/5）全有完整代码/替换指令。✓

**3. Type consistency**: `WAIC_HTML` / `build_waic.main()` / `check_waic_page` / `WAIC_SRC`/`WAIC_SITE` env 各 task 间名字一致。✓

无 gap。Plan 完整。
