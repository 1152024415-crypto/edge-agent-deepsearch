# SNN 洞察页 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在端侧 AI 雷达站新增 `site/snn.html`——一个静态精选 SNN 洞察报告页（左侧章节 TOC + 右侧 marked.js+KaTeX 渲染），内容来自整合 `D:\proj\snn-research` 两份 md（去华为化）+ 我自己的新 SNN 调研。

**Architecture:** 复用 `调研笔记`（notes 页）模式：单 markdown 报告由 marked.js 客户端渲染，TOC 从渲染后 H2 自动生成，KaTeX 渲染数学公式。`agent/build_snn.py` 读 `D:\proj\snn-research\SNN-insight.md` → 拷到 `site/snn/` → 用 `app/snn_page.py` 模板渲染 `site/snn.html`。index.html 加 nav 链接。

**Tech Stack:** Python 3.11（build 脚本）、HTML/CSS/JS（模板，无前端框架）、marked.js（CDN markdown 渲染）、KaTeX（CDN 数学渲染）、unittest（测试）、GitHub Pages（部署）。

## Global Constraints

- 复用 notes 页 RADAR 终端美学：CSS 变量 `--bg:#eef1f3;--panel:#fff;--ink:#0b1a24;--amber:#c2410c;--green:#15803d`，IBM Plex Mono/Sans，`@media max-width:760px` 侧栏堆叠。
- 去华为化：丢弃所有 `wiki.huuawei.com/vision-file-storage/...` 图片（公网 404）；第 9 节 Kirin/CANN/HiAI/Da Vinci 泛化为「移动旗舰 SoC / NPU 软件栈 / 端侧 AI 框架 / NPU 架构」。
- 数学公式必须渲染（KaTeX auto-render），报告含 LIF 方程/代理梯度/STDP 公式。
- 静态精选，不拉 weekly run 数据；本周 run 的 SNN 论文手动纳入第 10 节。
- SNN tag 规则按 07-15 收紧版（`方向:SNN` 只用 `spiking neural network`/`\bsnn\b`/`spikformer`/`spiking transformer`/`spiking neuron model`，不许裸 `neuromorphic`）。
- Windows bash；CRLF 警告可接受；commit 末尾 `Co-Authored-By: Claude <noreply@anthropic.com>`。
- 工作目录 `D:\proj\edge_agent`，master 分支直接做（用户已确认）。

---

### Task 1: gate_release 加 snn.html 存在检查（TDD）

**Files:**
- Modify: `app/gates/gate_release.py`（加 `check_snn_page` + 进 `run_all`）
- Test: `tests/test_gate_release.py`（加 2 测试 + 改 `_seed_good`）

**Interfaces:**
- Consumes: `gate_release._read_json` / `_err`（已存在）
- Produces: `check_snn_page(root, errors)` —— 检查 `site/snn.html` 存在；`run_all` 多调一道。

- [ ] **Step 1: 改 `_seed_good` 加 snn.html，跑现有测试确认全过（基线）**

在 `tests/test_gate_release.py` 的 `_seed_good` 末尾（`site/notes.html` 那行后）加：
```python
        _write(self.root, "site/snn.html", "<html>snn</html>")
```
Run: `python -m unittest tests.test_gate_release -q`
Expected: PASS（11 测试，新检查还没加，snn.html 存在不影响）

- [ ] **Step 2: 写失败测试 — snn.html 缺失要 FAIL**

在 `GateReleaseTest` 类内（`test_pass_good_layout` 前）加：
```python
    # ---- snn page ----
    def test_fail_when_snn_page_missing(self):
        self._seed_good()
        (self.root / "site" / "snn.html").unlink()
        errs = gr.run_all(self.root)
        self.assertTrue(any("snn.html" in e and "missing" in e for e in errs), errs)
```
Run: `python -m unittest tests.test_gate_release.GateReleaseTest.test_fail_when_snn_page_missing -q`
Expected: FAIL（`check_snn_page` 还没实现，errs 为空，assertTrue 失败）

- [ ] **Step 3: 实现 `check_snn_page` + 进 `run_all`**

在 `app/gates/gate_release.py` 的 `check_vendor_tier` 函数后加：
```python
def check_snn_page(root: Path, errors: list) -> None:
    """site/snn.html must exist — the SNN insight page nav link points at it."""
    if not (root / "site" / "snn.html").exists():
        _err(errors, "site/snn.html missing — run agent/build_snn.py (SNN 洞察 nav 链接会 404)")
```
在 `run_all` 末尾 `check_trending_freshness` 后加 `check_snn_page(root, errors)`：
```python
def run_all(root: Path) -> list:
    errors = []
    check_contract(root, errors)
    check_links(root, errors)
    check_highlights(root, errors)
    check_vendor_tier(root, errors)
    check_trending_freshness(root, errors)
    check_snn_page(root, errors)
    return errors
```

- [ ] **Step 4: 跑全测试确认 PASS**

Run: `python -m unittest tests.test_gate_release -q`
Expected: PASS（12 测试，含新 snn 缺失测试 + 既有全过）

- [ ] **Step 5: Commit**

```bash
git add app/gates/gate_release.py tests/test_gate_release.py
git commit -m "feat(gate): 加 snn.html 存在检查(+1测试)"
```

---

### Task 2: app/snn_page.py HTML 模板（TOC + KaTeX）

**Files:**
- Create: `app/snn_page.py`
- Test: `tests/test_snn_page.py`（新）

**Interfaces:**
- Consumes: 无（纯模板字符串）
- Produces: `SNN_HTML`（str，HTML 模板，含 marked.js+KaTeX CDN + TOC 自动生成 JS）

- [ ] **Step 1: 写失败测试 — SNN_HTML 存在且含关键标记**

Create `tests/test_snn_page.py`:
```python
#!/usr/bin/env python3
"""snn_page template renders the SNN insight page shell."""
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.snn_page import SNN_HTML

class SNNPageTest(unittest.TestCase):
    def test_template_has_key_markers(self):
        self.assertIn("<!doctype html>", SNN_HTML)
        self.assertIn("marked.min.js", SNN_HTML)        # markdown 渲染
        self.assertIn("katex", SNN_HTML.lower())         # 数学渲染
        self.assertIn("SNN-insight.md", SNN_HTML)        # 客户端 fetch 目标
        self.assertIn("id=\"toc\"", SNN_HTML)             # TOC 侧栏
        self.assertIn("id=\"art\"", SNN_HTML)            # 正文容器
        self.assertIn("index.html", SNN_HTML)            # 返回雷达链接
    def test_template_has_toc_autobuild_js(self):
        # TOC 从渲染后 h2 自动生成 + 当前节高亮
        self.assertIn("querySelectorAll('h2')", SNN_HTML)
        self.assertIn("IntersectionObserver", SNN_HTML)

if __name__ == "__main__":
    unittest.main()
```
Run: `python -m unittest tests.test_snn_page -q`
Expected: FAIL（`app/snn_page.py` 不存在，ImportError）

- [ ] **Step 2: 实现 `app/snn_page.py`**

Create `app/snn_page.py`（仿 `app/notes_page.py` 美学，单报告 + TOC 自动生成 + KaTeX）：
```python
"""Static shell for the SNN insight page (signal-monitor terminal aesthetic).

Single curated markdown report (site/snn/SNN-insight.md) fetched client-side,
rendered by marked.js, with a left sidebar TOC auto-built from the rendered
h2 headings (IntersectionObserver highlights current section), and KaTeX
auto-rendering $...$ / $$...$$ math.
"""

SNN_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RADAR · SNN 洞察</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
  <style>
    *{box-sizing:border-box}
    :root{--bg:#eef1f3;--panel:#ffffff;--ink:#0b1a24;--muted:#5a6b78;--faint:#8a99a6;--rule:#d4dae0;--hair:#e3e8ec;--amber:#c2410c;--green:#15803d}
    body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans","PingFang SC","Noto Sans SC",system-ui,sans-serif;font-size:14.5px;line-height:1.7}
    main{max-width:1180px;margin:0 auto;padding:18px 22px 80px}
    a{color:var(--amber);text-decoration:none}
    a:hover{text-decoration:underline}
    .scope{background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:12px 16px;margin-bottom:14px;display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap}
    h1{margin:0;font-family:"IBM Plex Mono",monospace;font-size:20px;font-weight:600;letter-spacing:1.5px}
    h1 .sub{font-family:"IBM Plex Sans",sans-serif;font-weight:500;font-size:13px;color:var(--muted);letter-spacing:0;margin-left:8px}
    .back{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--faint)}
    .sweep{height:2px;margin:10px -16px -12px;background:linear-gradient(90deg,transparent,var(--hair) 20%,var(--hair) 80%,transparent);position:relative;overflow:hidden}
    .sweep::after{content:"";position:absolute;inset:0;width:30%;background:linear-gradient(90deg,transparent,var(--amber),transparent);animation:sweep 3.2s linear infinite}
    @keyframes sweep{0%{transform:translateX(-100%)}100%{transform:translateX(400%)}}
    @media(prefers-reduced-motion:reduce){.sweep::after{animation:none;opacity:.5}}
    .layout{display:grid;grid-template-columns:230px 1fr;gap:16px;align-items:start}
    .toc{background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:12px 10px;position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto}
    .toc-title{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--faint);text-transform:uppercase;letter-spacing:.5px;padding:4px 6px 8px;border-bottom:1px solid var(--hair);margin-bottom:6px}
    .toc a{display:block;padding:4px 8px;font-size:12.5px;color:var(--muted);border-radius:3px;line-height:1.4}
    .toc a:hover{background:var(--hair);color:var(--ink)}
    .toc a.active{background:#fbeae3;color:var(--amber);font-weight:600}
    .art{background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:22px 28px;min-height:60vh}
    .art:empty::before{content:"loading…";color:var(--faint);font-family:"IBM Plex Mono",monospace}
    .art h1{font-family:"IBM Plex Sans",sans-serif;font-size:22px;letter-spacing:0;margin:0 0 6px;border-bottom:1px solid var(--rule);padding-bottom:8px}
    .art h2{font-size:18px;margin:26px 0 8px;padding-bottom:4px;border-bottom:1px solid var(--hair);scroll-margin-top:20px}
    .art h3{font-size:15px;margin:18px 0 6px;color:var(--ink)}
    .art p{margin:8px 0}
    .art ul,.art ol{margin:8px 0;padding-left:22px}
    .art li{margin:3px 0}
    .art blockquote{margin:10px 0;padding:6px 14px;border-left:3px solid var(--amber);background:#fdf3ee;color:var(--muted);border-radius:0 4px 4px 0}
    .art code{font-family:"IBM Plex Mono",monospace;font-size:12.5px;background:var(--hair);padding:1px 5px;border-radius:3px}
    .art pre{background:#0b1a24;color:#dbe4ea;padding:12px 14px;border-radius:5px;overflow:auto;margin:10px 0}
    .art pre code{background:none;padding:0;color:inherit;font-size:12.5px}
    .art img{max-width:100%;height:auto;border:1px solid var(--hair);border-radius:4px;margin:8px 0}
    .art table{border-collapse:collapse;margin:10px 0;width:100%;font-size:12.5px}
    .art th,.art td{border:1px solid var(--rule);padding:5px 9px;text-align:left}
    .art th{background:var(--hair)}
    .art hr{border:none;border-top:1px solid var(--rule);margin:18px 0}
    @media(max-width:760px){.layout{grid-template-columns:1fr}.toc{position:static;max-height:none}}
  </style>
</head>
<body>
  <main>
    <header class="scope">
      <h1>RADAR<span class="sub">SNN 洞察 · spiking neural networks</span></h1>
      <a class="back" href="index.html">← 返回雷达</a>
      <div class="sweep"></div>
    </header>
    <div class="layout">
      <aside class="toc" id="toc"></aside>
      <article class="art" id="art"></article>
    </div>
  </main>
  <script>
    var MD_URL = 'snn/SNN-insight.md';
    function render(md){
      var art = document.getElementById('art');
      art.innerHTML = marked.parse(md);
      // build TOC from h2
      var toc = document.getElementById('toc');
      var heads = art.querySelectorAll('h2');
      var html = '<div class="toc-title">sections</div>';
      for(var i=0;i<heads.length;i++){
        var h = heads[i];
        if(!h.id) h.id = 'sec-' + i;
        html += '<a href="#' + h.id + '" data-target="' + h.id + '">' + h.innerText.replace(/^\d+\.?\s*/,'').slice(0,40) + '</a>';
      }
      toc.innerHTML = html;
      // KaTeX render
      if(window.renderMathInElement){
        renderMathInElement(art, {delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]});
      }
      // current section highlight
      var links = toc.querySelectorAll('a');
      if('IntersectionObserver' in window){
        var obs = new IntersectionObserver(function(entries){
          entries.forEach(function(en){
            if(en.isIntersecting){
              var id = en.target.id;
              links.forEach(function(l){l.classList.toggle('active', l.getAttribute('data-target')===id);});
            }
          });
        },{rootMargin:'-20% 0px -70% 0px'});
        heads.forEach(function(h){obs.observe(h);});
      }
    }
    fetch(MD_URL).then(function(r){
      if(!r.ok){document.getElementById('art').innerHTML='<p>加载失败 ('+r.status+')：'+MD_URL+'</p>';return '';}
      return r.text();
    }).then(function(md){if(md)render(md);}).catch(function(e){
      document.getElementById('art').innerHTML='<p>加载出错：'+String(e)+'</p>';
    });
  </script>
</body>
</html>
"""
```

- [ ] **Step 3: 跑测试确认 PASS**

Run: `python -m unittest tests.test_snn_page -q`
Expected: PASS（2 测试）

- [ ] **Step 4: Commit**

```bash
git add app/snn_page.py tests/test_snn_page.py
git commit -m "feat(snn): snn_page.py HTML 模板(TOC自动生成+KaTeX)"
```

---

### Task 3: agent/build_snn.py + 最小 SNN-insight.md 脚手架（TDD）

**Files:**
- Create: `agent/build_snn.py`
- Create: `D:\proj\snn-research\SNN-insight.md`（最小脚手架，Task 4 再填内容）
- Test: `tests/test_build_snn.py`（新）

**Interfaces:**
- Consumes: `app.snn_page.SNN_HTML`（Task 2 产出）
- Produces: `agent/build_snn.main()` —— 读源 md → 拷到 `site/snn/SNN-insight.md` → 写 `site/snn.html`（= SNN_HTML，无内联，客户端 fetch）

- [ ] **Step 1: 写最小脚手架 SNN-insight.md（Task 4 再填）**

Create `D:\proj\snn-research\SNN-insight.md`：
```markdown
# SNN 洞察：脉冲神经网络端侧落地

> 脚手架，Task 4 填充完整内容。

## 1. SNN 是什么

(待填)
```

- [ ] **Step 2: 写失败测试 — build_snn 产出 snn.html + snn/md**

Create `tests/test_build_snn.py`:
```python
#!/usr/bin/env python3
"""build_snn renders site/snn.html + copies site/snn/SNN-insight.md."""
import sys, unittest, tempfile, importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class BuildSnnTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.site = Path(self._tmp.name)
    def _load_build_snn(self, src_md_text, site_root):
        # write a temp SNN-insight.md and a temp snn_page, then load build_snn against them
        src = Path(self._tmp.name) / "SNN-insight.md"
        src.write_text(src_md_text, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("build_snn", ROOT/"agent"/"build_snn.py")
        mod = importlib.util.module_from_spec(spec)
        # monkeypatch ROOT/site paths via env
        import os
        os.environ["SNN_SRC"] = str(src)
        os.environ["SNN_SITE"] = str(site_root)
        spec.loader.exec_module(mod)
        return mod
    def test_build_writes_html_and_md(self):
        mod = self._load_build_snn("# title\n## 1. A\nbody", self.site)
        mod.main()
        self.assertTrue((self.site / "snn.html").exists())
        self.assertTrue((self.site / "snn" / "SNN-insight.md").exists())
        html = (self.site / "snn.html").read_text(encoding="utf-8")
        self.assertIn("SNN-insight.md", html)
        self.assertIn("id=\"art\"", html)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 跑测试确认 FAIL**

Run: `python -m unittest tests.test_build_snn -q`
Expected: FAIL（`agent/build_snn.py` 不存在）

- [ ] **Step 4: 实现 `agent/build_snn.py`**

Create `agent/build_snn.py`：
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the SNN insight page: copy the curated markdown into site/snn/ and
render site/snn.html from app/snn_page.SNN_HTML (client-side fetches the md).

Re-run after editing D:\\proj\\snn-research\\SNN-insight.md.
Override paths via SNN_SRC (the .md) and SNN_SITE (the site/ dir) for tests.
"""
import os, sys, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEFAULT_SRC = Path(r"D:\proj\snn-research\SNN-insight.md")
DEFAULT_SITE = ROOT / "site"


def main() -> int:
    src = Path(os.environ.get("SNN_SRC") or DEFAULT_SRC)
    site = Path(os.environ.get("SNN_SITE") or DEFAULT_SITE)
    if not src.exists():
        print(f"[SNN] WARN source missing: {src}")
        return 1
    site.mkdir(parents=True, exist_ok=True)
    (site / "snn").mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, site / "snn" / "SNN-insight.md")
    from app.snn_page import SNN_HTML
    (site / "snn.html").write_text(SNN_HTML, encoding="utf-8")
    print(f"[SNN] wrote site/snn.html + site/snn/SNN-insight.md (src {src.stat().st_size}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: 跑测试确认 PASS**

Run: `python -m unittest tests.test_build_snn -q`
Expected: PASS

- [ ] **Step 6: 跑真实 build 确认产出**

Run: `python agent/build_snn.py`
Expected: 输出 `[SNN] wrote site/snn.html + site/snn/SNN-insight.md ...`，`site/snn.html` + `site/snn/SNN-insight.md` 存在。

- [ ] **Step 7: Commit**

```bash
git add agent/build_snn.py tests/test_build_snn.py
git commit -m "feat(snn): build_snn.py 构建脚本+最小脚手架"
```

---

### Task 4: 写 SNN-insight.md 1-9 节（整合 file1+file2，去华为化）

**Files:**
- Modify: `D:\proj\snn-research\SNN-insight.md`（Task 3 的脚手架 → 完整 1-9 节）

**Source**:
- `D:\proj\snn-research\SNN-端侧落地-技术深读.md`（file1，932 行，全面讲解）
- `D:\proj\snn-research\SNN-端侧落地-深度调研报告-2026.md`（file2，805 行，事实审计+修正）

**去华为化规则（硬）**:
- 丢弃所有 `![image](https://wiki.huawei.com/...)` 图片行（grep 删除）。
- 第 9 节：`Kirin` → `移动旗舰 SoC`；`CANN` → `NPU 软件栈`；`HiAI` → `端侧 AI 框架`；`Da Vinci NPU` → `NPU 架构`；标题改 `SNN 对移动旗舰 SoC 的参考`。保留三路线 + 推荐路线 A + 软件生态挑战 + 风险机会。

**章节结构（1-9，从 file1 取，file2 修正）**:
1. SNN 是什么（定义/生物神经元/LIF 微分方程 `$\frac{dV}{dt}=-\frac{V-V_{rest}}{\tau}+RI(t)$`/发放规则/信息编码表/三特性/局限）—— file1 §1
2. SNN vs ANN（对比表 + 灯泡类比）—— file1 §2
3. 发展历史（里程碑表 1907→2026.7）—— file1 §3。**file2 修正**：核对 file2 §9「事实审计」对 file1 历史日期/数值的更正，以 file2 为准。
4. 怎么训练（代理梯度+BPTT 手算例子/ANN-to-SNN/STDP/Spiking Transformer/e-prop + 决策树）—— file1 §4。**file2 修正**：file2 §3.4「Spiking Transformer 精度突破不等于部署突破」要加进 caveat。
5. 硬件平台（芯片对比表 Loihi/TrueNorth/Hala Point/Akida/Speck/Innatera/SpiNNaker2/Tianjic/Darwin3 + 三梯队 + 瓶颈）—— file1 §5。**file2 修正**：file2 §4「神经元数/TOPS-W 横比误导」+ §4.3「不能直接横比的原因」作为 caveat 加在表后。
6. 使用场景（适合/不适合表 + 判断标准）—— file1 §6
7. 产业生态（融资/专利/开源框架/开发者）—— file1 §7。框架部分留指针到第 11 节（Task 5 实查的对比表）。
8. 大厂态度（Intel/IBM/Qualcomm/Samsung/Sony+Prophesee/BrainChip/SynSense/Innatera/Kaspersky/NVIDIA-Google-Apple-Tesla）—— file1 §8。**Task 5 厂商动态 fetch 后更新**。
9. SNN 对移动旗舰 SoC 的参考（去华为化版 file1 §9：三路线 + 推荐路线 A + 软件生态挑战 + 风险机会）

- [ ] **Step 1: 写 1-9 节**

把 file1 §1-§9 整合进 `D:\proj\snn-research\SNN-insight.md`，按上述 file2 修正点调整，按去华为化规则删 wiki.huawei 图片 + 改 Kirin 段。保留 LaTeX 公式（`$$...$$`）和表格/代码块。file2 的「0. 一页纸结论」可作为报告开头摘要段（1 段）。

- [ ] **Step 2: 验证 — 无 wiki.huawei 图片 + 节数齐全**

Run:
```bash
python -c "import re; h=open(r'D:\proj\snn-research\SNN-insight.md',encoding='utf-8').read(); print('wiki.huawei images:', len(re.findall(r'wiki\.huawei\.com', h))); print('h2 sections:', len(re.findall(r'^## ', h, re.M)))"
```
Expected: `wiki.huawei images: 0`；`h2 sections: ≥10`（含 1-9 + 后面 10/11）

- [ ] **Step 3: 跑 build + chrome 看渲染**

Run: `python agent/build_snn.py`，然后 chrome-devtools 打开 `site/snn.html`（用 runtime server: 先 `python app/server.py --port 8001` 再访问 `http://127.0.0.1:8001/snn.html`? 不——server 无 /snn 路由，直接 file:// 打开 `site/snn.html`）。
用 evaluate_script 查：`document.querySelectorAll('#art h2').length`（应 ≥10）、`document.querySelectorAll('#toc a').length`（应 ≥10，TOC 自动生成）、`#art` 非空、无 404。
Expected: h2 ≥10，TOC 链接 ≥10，正文渲染，KaTeX 公式渲染（查 `#art .katex` 元素 >0）。

- [ ] **Step 4: Commit**

```bash
git add "D:/proj/snn-research/SNN-insight.md"  # 注意：snn-research 不在 edge_agent repo，需用绝对路径或拷贝
```
**注意**：`D:\proj\snn-research` 不在 `D:\proj\edge_agent` git repo 内，不能直接 `git add`。把 `SNN-insight.md` 也拷一份到 `D:\proj\edge_agent\data\snn-insight.md` 进 repo（build_snn 默认源改指向 repo 内的 `data/snn-insight.md`，便于 git 跟踪 + 部署可复现）。

修正 `agent/build_snn.py` 的 `DEFAULT_SRC` 改为 `ROOT / "data" / "snn-insight.md"`，并把 `D:\proj\snn-research\SNN-insight.md` 拷到 `data/snn-insight.md`：
```bash
cp "D:/proj/snn-research/SNN-insight.md" "D:/proj/edge_agent/data/snn-insight.md"
git add agent/build_snn.py data/snn-insight.md
git commit -m "feat(snn): SNN-insight.md 1-9节整合(去华为化,file2修正)"
```
同步更新 `tests/test_build_snn.py`（DEFAULT_SRC 已通过 env 覆盖，测试不受影响，但跑一遍确认）。

---

### Task 5: 新调研 — arXiv SNN 扫 + GitHub 框架实查 + 厂商动态（→ 第 10/11 节 + 更新 7/8）

**Files:**
- Modify: `data/snn-insight.md`（加第 10/11 节，更新 7/8）
- Modify: `agent/arxiv_curl_sweep.py`（窗口/查询临时扩 SNN 3 个月）OR 一次性脚本

**调研项**:

**5a. arXiv SNN 近 3 月扫（→ 第 10 节「近期 SNN 论文」）**:
- 跑 arXiv Atom API（curl `http://export.arxiv.org/api/query?search_query=abs:"spiking neural network" OR abs:spikformer OR abs:"spiking transformer"&start=0&max_results=100&sortBy=submittedDate&sortOrder=descending`），筛 2026-04-15~2026-07-15。
- 也可重用 `agent/arxiv_curl_sweep.py`（临时改窗口 + SNN 查询组）。
- 精选 ~15-20 篇真 SNN（按 07-15 收紧 tag 规则判：含 `spiking neural network`/`spikformer`/`spiking transformer`，不含则丢）。每篇：标题/日期/arxiv abs 链接/一句大白话（从摘要取）。
- 含本周 run 的 5-6 篇 SNN（从 `research_runs/run-20260715-*.json` 取 `tags` 含 `方向:SNN` 的）。

- [ ] **Step 5a.1**: 跑 SNN arXiv 扫，得候选列表。
- [ ] **Step 5a.2**: 精选 15-20 篇，写进 `data/snn-insight.md` 第 10 节（表格：标题 | 日期 | 链接 | 一句话）。

**5b. GitHub SNN 框架实查（→ 第 11 节「框架对比表」）**:
- 用 GitHub MCP 或 curl `api.github.com/repos/{owner}/{repo}` 查：
  - `fangwei123456/spikingjelly`（SpikingJelly）
  - `snf-lab/snnTorch`
  - `BindsNET/bindsnet`
  - `brian-team/brian2`
  - `intel/neuromorphic`（Lava —— 确认 archived 2026.5）
  - `norse/norse`
  - `synsense/sinabs`
  - `nest/nest-simulator`（NEST）
- 每个取：`stargazers_count`、`pushed_at`（最近更新）、`language`、`license.spdx_id`、`archived`（bool）。
- 编对比表：框架 | stars | 最近更新 | 语言 | 许可 | 定位 | 状态。

- [ ] **Step 5b.1**: curl/MCP 查 8 个框架 repo 元数据。
- [ ] **Step 5b.2**: 写进 `data/snn-insight.md` 第 11 节对比表。Lava 标注「已归档 2026.5」。

**5c. 厂商动态 fetch（→ 更新第 7/8 节）**:
- WebFetch BrainChip (`brainchip.ai`)、SynSense (`synsense.ai`)、Innatera (`innatera.com`) 近期产品/融资动态。
- 确认 Intel Lava (`github.com/intel/neuromorphic`) archived 状态（5b 已含）。
- 命中官方域名才算；非官方二手新闻标为「据 X 报道」。

- [ ] **Step 5c.1**: WebFetch 3 家 SNN 芯片公司官网近期动态。
- [ ] **Step 5c.2**: 更新 `data/snn-insight.md` 第 7 节融资表 + 第 8 节公司态度。

- [ ] **Step 5d: rebuild + 验证 + Commit**

Run: `python agent/build_snn.py`，chrome 看第 10/11 节渲染。
Commit:
```bash
git add data/snn-insight.md
git commit -m "feat(snn): 第10节近期SNN论文+第11节框架对比表+厂商动态(自调研)"
```

---

### Task 6: index nav 链接 + 全量 build + gate + chrome 实测 + 部署 gh-pages

**Files:**
- Modify: `app/page.py`（加 SNN 洞察 nav 链接，挨着 调研笔记）
- Modify: `app/build.py`（render_page rewrite `notes.html` → 也 rewrite `snn.html` 链接，静态根 weeks_base）

**Interfaces:**
- Consumes: Task 3 的 `site/snn.html` + `site/snn/SNN-insight.md`
- Produces: index.html 有 `snn.html` nav 链接；部署到 gh-pages。

- [ ] **Step 1: page.py 加 SNN nav 链接**

在 `app/page.py` 找到 `调研笔记` / `notes.html` 的 nav 链接处，旁加 `SNN 洞察 → snn.html`（同样的 class/样式）。先 grep 定位：
Run: `grep -n "notes.html\|调研笔记" app/page.py`
按现有 `notes.html` 链接的 pattern 加一行 `snn.html`（文字「SNN 洞察」）。

- [ ] **Step 2: build.py render_page 静态链接重写加 snn.html**

`app/build.py` 的 `render_page` 里 `if not runtime:` 块，已有 `notes.html` 重写：
```python
        html = html.replace('href="notes.html"', f'href="{weeks_base}notes.html"')
```
旁加：
```python
        html = html.replace('href="snn.html"', f'href="{weeks_base}snn.html"')
```

- [ ] **Step 3: 全量 build + gate**

Run:
```bash
python agent/build_snn.py
python app/build.py --server http://127.0.0.1:8001
python app/gates/gate_all.py
```
Expected: gate_all 全过（含新 snn.html 检查）。

- [ ] **Step 4: chrome 实测（release-check 用户视角浏览）**

chrome-devtools 打开 `file:///D:/proj/edge_agent/site/index.html`，确认 nav 有「SNN 洞察」链接 → 点 → `site/snn.html` 200。再打开 `site/snn.html`（file://）：markdown 渲染（h2 ≥11）、TOC 侧栏 ≥11 链接、点 TOC 滚动到对应节、当前节高亮、KaTeX 公式渲染（`#art .katex` >0）、无 wiki.huawei 坏图、返回雷达链接 200。
注意：file:// 下 fetch('snn/SNN-insight.md') 可能被 file protocol 拦（CORS）。改用 runtime server 验证：`python app/server.py --port 8001`，但 server 无 /snn 路由。**解决**：用 `python -m http.server` 在 site/ 目录起一个静态 server：`cd site && python -m http.server 8091`，访问 `http://127.0.0.1:8091/snn.html`（fetch 正常）。

- [ ] **Step 5: 部署 gh-pages**

Run（手动 worktree push，同 notes 流程）:
```bash
git fetch origin gh-pages
TMP=$(mktemp -d) && git worktree add --detach "$TMP" origin/gh-pages
cp -r D:/proj/edge_agent/site/* "$TMP"/
cd "$TMP" && git add -A && git commit -m "deploy: SNN洞察页(静态精选报告+TOC+KaTeX)" && git push origin HEAD:gh-pages
cd D:/proj/edge_agent && git worktree remove --force "$TMP"
```

- [ ] **Step 6: push master + 验证 live**

```bash
git add app/page.py app/build.py agent/build_snn.py data/snn-insight.md app/gates/gate_release.py tests/
git commit -m "feat: SNN洞察页上线(nav+build+gate+测试)"
git push origin master
```
sleep 60; curl live `https://1152024415-crypto.github.io/edge-agent-deepsearch/snn.html` → 200 + 含 `SNN-insight.md`。
chrome live 打开 snn.html → 渲染 + TOC + KaTeX + 无坏图。

- [ ] **Step 7: Commit deploy + 收尾**

更新 `data/.last_run` 不需要（非周刷新）。沉淀教训进 `AGENTS.md`（如有新错）。

---

## Self-Review

**1. Spec coverage**:
- 静态精选报告 ✓ (Task 4 内容 + Task 3 build)
- 侧边 TOC + 正文 + KaTeX ✓ (Task 2 模板)
- 去华为化 ✓ (Task 4 规则 + 验证 grep wiki.huawei=0)
- 新调研（论文/框架/公司）✓ (Task 5)
- index nav ✓ (Task 6)
- gate snn.html 检查 ✓ (Task 1)
- chrome 实测 ✓ (Task 6 Step 4)
- 部署 gh-pages ✓ (Task 6 Step 5-6)

**2. Placeholder scan**: Task 4/5 是内容/调研任务，步骤里给了「取哪节、按什么规则、验证什么」而非粘贴 1000 行 prose（源 md 文件就是内容，task 描述如何整合）。这不算 placeholder——源文件是已存在的具体内容，task 是整合指令。代码 task（1/2/3/6）全有完整代码。✓

**3. Type consistency**: `build_snn.main()` / `SNN_HTML` / `check_snn_page` 在各 task 间名字一致。`DEFAULT_SRC` 在 Task 3 建为 `D:\proj\snn-research\...`，Task 4 Step 4 改为 `data/snn-insight.md`（注明）。✓

无 gap。Plan 完整。
