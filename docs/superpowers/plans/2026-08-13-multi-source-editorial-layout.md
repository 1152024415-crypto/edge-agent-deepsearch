# 多消息源周报编辑布局 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把百条级、多来源的周报重排为“编辑推荐优先、完整资料库不漏、待核验线索分离”的桌面页面。

**Architecture:** 保留现有原生 HTML/CSS/JavaScript 单页和 API 字段，不修改核心检索或存储 schema。页面把 `ALL` 同时投影成推荐视图、来源构成、完整资料库和 Trending 线索区；筛选只作用于完整资料库，推荐与编辑热点保持稳定。

**Tech Stack:** Python 3、原生 HTML/CSS/JavaScript、unittest、GitHub Pages 静态构建、浏览器桌面验收。

---

### Task 1: 锁定新的展示契约

**Files:**
- Modify: `tests/test_page_recommendations.py`
- Modify: `tests/test_gate_release.py`

- [ ] **Step 1: 写页面顺序失败测试**

断言 `recommendations`、`weekly`、`all-research`、`discovery` 按顺序出现，并要求 `source-map` 位于完整资料库内部。

- [ ] **Step 2: 写完整性失败测试**

断言 `renderPapers()` 直接使用全部筛选结果，不含 `visible().filter(p=>!isRecommended(p))`，并保留推荐 badge。

- [ ] **Step 3: 写筛选和线索分区失败测试**

断言设备、来源、标签三类状态可组合；更多标签使用带 `aria-expanded` 的按钮；Trending 只渲染到 `discovery`，并带“待核验线索”文案。

- [ ] **Step 4: 写构建门失败测试**

在临时构建产物中移除任一关键分区，或注入排除推荐项的旧表达式，断言 `gate_release` 返回明确错误。

- [ ] **Step 5: 运行 RED**

Run: `python tests/test_page_recommendations.py` and `python tests/test_gate_release.py`

Expected: 新断言因旧页面缺少来源构成、发现线索分区且完整列表剔除推荐而失败。

- [ ] **Step 6: 检查提交策略**

检查 `.agent/config.yml`；缺失时按 `auto_commit: true`，但仅暂存本任务测试文件，不包含用户已有的 `research_runs/` 和 `data/weeks/` 改动。

### Task 2: 实现编辑前台与全量资料库

**Files:**
- Modify: `app/page.py`
- Modify: `tests/test_page_recommendations.py`

- [ ] **Step 1: 重排页面骨架**

把搜索和排序移入 `all-research`；新增 `source-map`、`primary-filter`、`advanced-filter` 和独立 `discovery`；保留现有 notes/SNN/WAIC/周切换入口。

- [ ] **Step 2: 重做推荐名录**

使用单列三段网格，并继续按设备范围 → source tier → score → date 排序。每条保持 `title_zh`、`abstract`、`tags`、`recommendation_reason`、`title` 的固定顺序。

- [ ] **Step 3: 实现分层筛选**

增加 `ACTIVE_SOURCE` 与 `ACTIVE_SCOPE` 状态。`visible()` 组合设备、来源、tags 和搜索条件；推荐渲染直接读取 `ALL.filter(isRecommended)`，不受这些状态影响。

- [ ] **Step 4: 恢复真正完整列表**

`renderPapers()` 使用 `visible()` 的全部结果。推荐条目在列表中带橙色推荐标识；各 source tier 计数和来源构成均从完整 `ALL` 计算。

- [ ] **Step 5: 分离 Trending**

`renderTrending()` 只写入 `#discovery`，默认显示前 8 条，可展开全部，标题明确“GitHub 待核验线索”。

- [ ] **Step 6: 补可访问性和状态**

为搜索提供 label，为筛选和展开按钮提供 `aria-pressed`/`aria-expanded`，详情层使用 button、dialog 语义和焦点归还；加载失败在资料库内显示重试按钮。

- [ ] **Step 7: 运行 GREEN**

Run: `python tests/test_page_recommendations.py`

Expected: 新展示契约全部通过，旧中文字段顺序和端侧 Agent 优先级测试继续通过。

- [ ] **Step 8: 检查提交策略**

检查 `.agent/config.yml`；按配置暂存 `app/page.py` 和页面测试，提交信息使用 `feat: reorganize multi-source weekly layout`。

### Task 3: 把布局契约写入发布门和站点规范

**Files:**
- Modify: `app/gates/gate_release.py`
- Modify: `tests/test_gate_release.py`
- Modify: `docs/site/display-spec.md`

- [ ] **Step 1: 实现真实构建布局检查**

新增 `check_editorial_layout()`：检查推荐、本周判断、完整资料库、发现线索的存在与顺序；检查来源构成存在；检查旧的推荐排除表达式不存在。

- [ ] **Step 2: 接入发布门**

把 `check_editorial_layout()` 加入 `run_all()`，错误信息直接说明缺少的分区或完整性回归。

- [ ] **Step 3: 更新展示规格**

把旧 signal-terminal 默认视图改为本设计的五层结构，明确完整列表包含推荐、Trending 是待核验线索、筛选只作用于资料库。

- [ ] **Step 4: 运行 gate 测试**

Run: `python tests/test_gate_release.py`

Expected: 正常 fixture 通过，缺区块或剔除推荐的 fixture 失败。

- [ ] **Step 5: 检查提交策略**

检查 `.agent/config.yml`；按配置暂存 gate、测试和展示规格，提交信息使用 `test: guard editorial page structure`。

### Task 4: 本地构建和桌面验收

**Files:**
- Generated: `site/`

- [ ] **Step 1: 启动现有数据服务**

Run: `python app/server.py --host 127.0.0.1 --port 8001`

Expected: `/api/papers` 返回当前周完整数据，页面可加载。

- [ ] **Step 2: 构建静态站与辅助页面**

Run: `python app/build.py --server http://127.0.0.1:8001`, `python agent/build_notes.py`, `python agent/build_snn.py`, `python agent/build_waic.py`.

Expected: `site/index.html`、114 个当前周详情和历史周页面生成。

- [ ] **Step 3: 运行全部机械门**

Run: `python tests/test_page_recommendations.py`, `python tests/test_research_pipeline.py`, `python tests/test_build.py`, `python app/gates/gate_all.py`, `git diff --check`.

Expected: 全部退出 0，无空白错误。

- [ ] **Step 4: 浏览器验收 1440px 桌面页**

检查总数与来源计数、6 条推荐字段层级、推荐在完整库中仍存在、设备/来源/标签组合筛选、清除筛选、详情开关、周切换、Trending 展开以及控制台 error。

- [ ] **Step 5: 修复并复验**

任何布局溢出、文本截断、键盘不可达、计数不一致或错误日志必须先修复，再重新执行 Step 3 和 Step 4。

### Task 5: 部署和线上复验

**Files:**
- Generated: `site/`

- [ ] **Step 1: 部署已验证快照**

使用项目现有临时 gh-pages worktree 流程，仅复制 `site/`，保留历史 paper/week 文件策略，提交并推送 `gh-pages`。

- [ ] **Step 2: 在线缓存穿透复验**

打开 `https://1152024415-crypto.github.io/edge-agent-deepsearch/?v=<commit>`，在 1440px 桌面视口重复本地关键验收，并读取浏览器错误日志。

- [ ] **Step 3: 核对工作区**

确认只留下用户原有未提交改动；不暂存或覆盖 `data/weeks/2026-08-05.json`、`research_runs/livefix.html`、`research_runs/live0807.html`。

- [ ] **Step 4: 最终报告**

报告页面结构变化、验证命令结果、部署 URL 和任何仍存在但不阻塞的限制。

## Plan Self-Review

- Spec coverage：五层信息架构、完整性、筛选、线索分离、可访问性、发布门、构建和线上验收均有任务。
- Placeholder scan：每个步骤均给出具体文件、行为和验证命令。
- Type consistency：继续使用现有 `source_tier`、`edge_agent_scope`、`tags` 和 `recommendation` 字段，不新增 schema。
- Scope：仅修改桌面网页展示、展示规格和机械回归，不触碰检索逻辑或本周研究数据。
