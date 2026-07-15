# SNN 洞察页 设计 spec

**日期**: 2026-07-15
**目标**: 在端侧 AI 雷达站新增一个 SNN（脉冲神经网络）洞察页，作为深度精选报告 + 我自己的 SNN 调研产出。

## 目标与范围

在 `site/snn.html` 提供一个静态精选报告页，复用 `调研笔记`（notes 页）的模式：左侧粘性章节目录 + 右侧 marked.js 客户端渲染的 markdown 报告，同样的 RADAR 终端美学。内容来自整合 `D:\proj\snn-research` 两份 md（技术深读 + 深度调研事实审计）+ 我自己的新调研，去华为化后写成一份额精选 markdown。

**在范围内**：
- 一份 `SNN-insight.md`（11 节精选报告，去华为化）
- `site/snn.html` + `site/snn/SNN-insight.md`（静态产物）
- `app/snn_page.py`（HTML 模板，notes 页同美学）
- `agent/build_snn.py`（构建脚本：读 md → 拷到 site/snn/ → 渲染 site/snn.html）
- index.html 加「SNN 洞察」nav 链接
- 我自己的新调研：arXiv SNN 近 1-3 月扫 + GitHub 框架实查 + 厂商动态 fetch
- gate_release 加 snn.html 存在检查 + chrome 实测

**不在范围内**：
- 不自动拉 weekly run 数据（静态精选，手动刷新；run 的 SNN 论文手动纳入第 10 节）
- 不做动态子雷达（用户已确认静态精选）
- 不重写 notes 页

## 架构

复用 notes 页模式（`app/notes_page.py` + `agent/build_notes.py`），区别是 notes 是「多文档集合侧栏」，SNN 页是「单长报告 + 章节目录侧栏」。

```
D:\proj\snn-research\SNN-insight.md   (主 agent 整合产出的精选报告源)
        │ agent/build_snn.py
        ├→ site/snn/SNN-insight.md    (拷贝，供 fetch)
        └→ site/snn.html              (app/snn_page.py 模板渲染,marked.js 客户端渲染 md)
```

页面结构：
- 左侧 `<aside>` 粘性侧栏：从渲染后 markdown 的 `<h2>` 自动生成目录（JS 扫 `#art h2` 建链接），点击滚动到对应节，当前节高亮（IntersectionObserver）。
- 右侧 `<article id=art>`：marked.js 渲染的 markdown；渲染后调 KaTeX auto-render (`renderMathInElement`) 把 `$...$`/`$$...$$` 渲染成公式（报告含 LIF 方程/代理梯度/STDP 等核心数学，必须渲染）。
- 顶部 header：`RADAR · SNN 洞察` + `← 返回雷达` + 扫描动画条（同 notes 页）。
- CDN：marked.js + KaTeX（core + auto-render）。

## 内容结构（SNN-insight.md，11 节）

1. **SNN 是什么** — 定义 / 生物神经元 / LIF 模型 / 信息编码 / 三特性（事件驱动/时间/稀疏）/ 局限（取自 file1 §1）
2. **SNN vs ANN** — 对比表 + 灯泡类比（file1 §2）
3. **发展历史** — 里程碑表 1907→2026.7（file1 §3，用 file2 的事实审计修正）
4. **怎么训练** — 代理梯度+BPTT / ANN-to-SNN / STDP / Spiking Transformer / e-prop，含手算例子与决策树（file1 §4，file2 §3 修正）
5. **硬件平台** — 神经形态芯片对比表（Loihi/TrueNorth/Hala Point/Akida/Speck/Innatera/SpiNNaker2/Tianjic/Darwin3 等）+ 三梯队 + 关键瓶颈（file1 §5，file2 §4「神经元数/TOPS-W 误导」caveat）
6. **使用场景** — 适合/不适合 + 判断标准（file1 §6）
7. **产业生态** — 融资 / 专利 / 开源框架 / 开发者（file1 §7 + 我新调研的框架对比表见第 11 节）
8. **大厂态度** — Intel/IBM/Qualcomm/Samsung/Sony+Prophesee/BrainChip/SynSense/Innatera/Kaspersky/NVIDIA-Google-Apple-Tesla（file1 §8 + 我新调研的厂商动态）
9. **SNN 对移动旗舰 SoC 的参考** — file1 §9 去华为化：Kirin/CANN/HiAI/Da Vinci → 泛化「移动旗舰 SoC / NPU 软件栈 / 端侧 AI 框架 / NPU 架构」；保留三路线（专用协处理器 / 扩展 NPU / 授权 IP）+ 推荐路线 A + 风险机会
10. **近期 SNN 论文（新）** — 我扫 arXiv 近 1-3 月 SNN（spiking neural network/spikformer/spiking transformer 等查询，~30-50 候选精选 ~15-20）+ 本周 run 的 5-6 篇 SNN，每篇：标题/日期/arxiv 链接/一句大白话
11. **SNN 框架对比表（新）** — SpikingJelly/snnTorch/BindsNET/Brian2/Lava/Norse/Sinabs/NEST：stars/最近更新/语言/许可/定位/状态（GitHub MCP 或 api 实查，标注 Lava 已归档）

## 去华为化规则

- 丢弃所有 `wiki.huawei.com/vision-file-storage/...` 图片（公网 404）。不替换为外部图（找不到对应公网图），靠表格/公式/代码块承载——内容已足够实。
- 第 9 节标题与正文去 Kirin 品牌：`Kirin` → `移动旗舰 SoC`；`CANN` → `NPU 软件栈`；`HiAI` → `端侧 AI 框架`；`Da Vinci NPU` → `NPU 架构`；保留分析逻辑（三路线 + 推荐路线 A + 软件生态挑战 + 风险机会）。
- 其他节不涉及华为内部内容，原样整合修正。

## 我自己的新调研（深）

- **arXiv SNN 近 1-3 月扫**：扩展 `agent/arxiv_curl_sweep.py` 的窗口或新跑一轮，查询 `spiking neural network` / `spikformer` / `spiking transformer` / `neuromorphic`（注意：neuromorphic 作搜集词 OK，但打 tag 仍按收紧后的 `方向:SNN` 规则只标真 SNN）。窗口 ~2026-04-15~2026-07-15，~30-50 候选，精选 ~15-20 进第 10 节。
- **GitHub 框架实查**：用 GitHub MCP（`list_repositories`/`search_repositories`/`list_tags`/`list_commits`）查 SpikingJelly(fangwei123456/spikingjelly)、snnTorch(snf-lab/snnTorch)、BindsNET(BindsNET/bindsnet)、Brian2(brian-team/brian2)、Lava(intel/neuromorphic)、Norse(norse/norse)、Sinabs(synsense/sinabs)、NEST(neuralnest) 的 stars + 最近 commit 日期 + 语言 + 许可 → 第 11 节对比表。MCP 限速 curl api.github.com 兜底。
- **厂商动态 fetch**：WebFetch 查 Intel Lava 归档确认、BrainChip/SynSense/Innatera 近期产品/融资新闻（命中各自官网域名）→ 更新第 7/8 节。

## 构建 / 部署

- `agent/build_snn.py`：
  1. 读 `D:\proj\snn-research\SNN-insight.md`
  2. 拷到 `site/snn/SNN-insight.md`
  3. 用 `app/snn_page.py` 的 `SNN_HTML` 模板渲染 `site/snn.html`（marked.js CDN，TOC 客户端从渲染后 H2 生成）
- 接入构建流程：`app/build.py` 不动（它镜像 server）；`build_snn.py` 独立跑（像 `build_notes.py`），部署前一起跑。
- index.html nav：在 `调研笔记` 链接旁加 `SNN 洞察 → snn.html`（page.py 改 + build.py mirror）。
- 部署：gh-pages worktree push site/（同 notes 流程）。

## 测试 / 验证

- `gate_release.py` 加 `check_snn_page`：`site/snn.html` 存在（否则 nav 链接 404）。加 1 测试。
- `tests/test_build.py` 或新 `tests/test_build_snn.py`：build_snn 产出 snn.html + snn/md。
- chrome 实测（release-check 用户视角浏览）：打开 snn.html → markdown 渲染（h1/表格/公式/代码块）→ 侧栏 TOC 点击滚动到对应节 → 当前节高亮 → 无 wiki.huawei 坏图（grep 确认 0 个 wiki.huawei 链接）→ 返回雷达链接 200。

## 文件清单

- 新建 `D:\proj\snn-research\SNN-insight.md`（整合产出，去华为化，11 节）
- 新建 `app/snn_page.py`（HTML 模板，notes 页同美学，TOC 客户端生成）
- 新建 `agent/build_snn.py`（构建脚本）
- 改 `app/page.py`（index nav 加 SNN 洞察链接）
- 改 `app/gates/gate_release.py` + `tests/test_gate_release.py`（snn.html 存在检查 + 测试）
- 部署产物：`site/snn.html` + `site/snn/SNN-insight.md`

## 非目标 / 取舍

- 不做搜索/筛选交互（静态报告，YAGNI）。
- 不做移动端 TOC 抽屉优化（v1 复用 notes 页的 `@media max-width:760px` 侧栏堆叠）。
- 图片全去（不找公网替代），靠表格/公式/文字。数学公式用 KaTeX 渲染（已纳入架构）。
