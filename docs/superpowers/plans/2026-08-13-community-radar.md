# 社区雷达 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为桌面周报增加独立、可归档、可校验的 X/论坛社区发现层，并用本周公开线索填充。

**Architecture:** `data/community_radar.json` 是独立编辑产物；服务器通过 `/api/community` 提供，静态构建内联为 `window.__COMMUNITY__`，历史周随 archive 冻结。页面只在发现层展示，正式 papers 契约不变。

**Tech Stack:** Python 标准库 HTTP server/build/gates、Vanilla HTML/CSS/JS、unittest、GitHub Pages 静态构建。

---

### Task 1: 社区数据校验器与样例数据

**Files:**
- Create: `app/community.py`
- Create: `tests/test_community.py`
- Create: `data/community_radar.json`

- [ ] **Step 1: 写失败测试**：覆盖合法记录、非法来源/设备/核验状态、缺失中文字段、非 HTTP URL、越出七日窗口、X limited coverage 缺说明。
- [ ] **Step 2: 运行 `python tests/test_community.py`**，确认因 `app.community` 不存在而失败。
- [ ] **Step 3: 实现 `load_community(path, today)` 与 `validate_community(payload, today)`**，返回规范化 `{window,coverage,items}`，非法数据抛 `CommunityValidationError`。
- [ ] **Step 4: 用公开搜索结果写本周 JSON**，每条只保留原帖直达 URL 和可核验日期；无法访问的来源写 coverage，不凑数。
- [ ] **Step 5: 重跑测试并提交**。提交前检查 `.agent/config.yml`；默认 auto commit 时提交 `feat: add validated community radar data`。

### Task 2: API、静态构建与历史周归档

**Files:**
- Modify: `app/server.py`
- Modify: `app/build.py`
- Modify: `app/weeks.py`
- Modify: `tests/test_build.py`
- Modify: `tests/test_weeks.py`
- Modify: `tests/test_server_weeks.py`

- [ ] **Step 1: 写失败测试**：`GET /api/community` 返回 items；`render_page` 含 `window.__COMMUNITY__`；archive 写入/读取 community；历史周内联自己的 community。
- [ ] **Step 2: 运行三个测试文件，确认缺接口/参数而失败。**
- [ ] **Step 3: 最小实现**：server 读取校验后的 JSON；`render_page(..., community, ...)` 固定内联顺序 `PAPERS→WEEKLY→TRENDING→COMMUNITY→WEEKS`；`write_archive` 与 `extract_payloads_from_html` 增加 community，旧归档回退空数据。
- [ ] **Step 4: 重跑测试并提交**。提交前检查 auto commit；提交 `feat: archive community radar with each week`。

### Task 3: 桌面社区雷达页面

**Files:**
- Modify: `app/page.py`
- Modify: `tests/test_page_recommendations.py`
- Modify: `docs/site/display-spec.md`
- Modify: `docs/site/api-contract.md`

- [ ] **Step 1: 写失败测试**：`community` 位于 `all-research` 与 `discovery` 之间；存在来源/设备筛选、8 条预览、核验徽标、覆盖说明、空状态；数据优先读 `window.__COMMUNITY__`。
- [ ] **Step 2: 运行页面测试，确认因社区板块缺失而失败。**
- [ ] **Step 3: 实现页面**：单列紧凑行、来源和设备按钮、中文标题/总结/价值、原帖外链；筛选只影响社区板块；GitHub 仍独立。
- [ ] **Step 4: 更新显示与 API 文档，重跑测试并提交**。提交前检查 auto commit；提交 `feat: show community signals separately`。

### Task 4: 发布门禁与每周流程

**Files:**
- Modify: `app/gates/gate_release.py`
- Modify: `tests/test_gate_release.py`
- Modify: `docs/agent-guide/research-prompt.md`
- Modify: `docs/agent-guide/release-check.md`
- Modify: `.agents/skills/edge-agent-research-pipeline/SKILL.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: 写失败测试**：缺 community 板块/内联数据、字段非法、越窗、社区 URL 混入 papers 均使 gate 失败；空 items 但 coverage 完整可以发布。
- [ ] **Step 2: 运行 gate 测试确认失败。**
- [ ] **Step 3: 实现机械门并更新流程**：每周正式四来源完成后独立采社区；社媒永远不能直接写入 papers；X/论坛不可达必须记 coverage。
- [ ] **Step 4: 重跑测试并提交**。提交前检查 auto commit；提交 `test: guard community discovery contract`。

### Task 5: 构建、部署和真实浏览验收

**Files:**
- Generated: `site/`

- [ ] **Step 1: 运行 `python tests/test_community.py`、`python tests/test_research_pipeline.py`、`python tests/test_build.py`、`python app/gates/gate_all.py` 与 `git diff --check`。**
- [ ] **Step 2: 启动本地服务，构建 site；浏览器检查社区条数、来源/设备筛选、展开、原帖 URL、历史周切换、空/limited coverage 与控制台错误。**
- [ ] **Step 3: 推送功能分支，合并到 master 并推送；以保留历史文件的方式部署 gh-pages。**
- [ ] **Step 4: 在线硬刷新并重复 DOM 数量、筛选、原帖链接、周切换和 console 验收。**
- [ ] **Step 5: 清理本地服务和隔离 worktree；提交前检查 auto commit。**

## 自检

- 规格覆盖：独立数据、公开免登录、覆盖说明、设备优先、静态/动态/历史周、页面、门禁和真实部署均有任务。
- 无占位内容；字段名在所有任务中一致。
- 没有改变 papers/source_tier 或推荐评分契约，避免社区噪声污染正式周报。
