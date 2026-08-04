# 中文优先推荐卡 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让推荐区用中文结论和中文推荐理由完成首屏扫读，并用生成、校验、发布三层机制阻止英文原文或内部占位语再次上线。

**Architecture:** 保留 `title` 作为原始来源标题，以现有 `abstract` 作为中文主结论，新增 `recommendation_reason` 作为推荐编辑字段。生成脚本不再自动推荐；research-run validator 和静态 release gate 共同执行中文与完成度规则，页面只展示读者字段。

**Tech Stack:** Python 3、SQLite、原生 HTML/CSS/JavaScript、unittest、GitHub Pages 静态构建。

---

### Task 1: 锁定中文内容与推荐完成度契约

**Files:**
- Modify: `tests/test_research_pipeline.py`
- Modify: `tests/test_page_recommendations.py`
- Modify: `tests/test_build.py`
- Modify: `app/gates/gate_release.py`

- [ ] **Step 1: 写 research-run 失败测试**

新增三项测试：全英文 `abstract` 抛出 `ValidationError`；`recommendation="推荐"` 缺 `recommendation_reason` 抛错；推荐理由含 `auto-converted` 或 `待核实` 抛错。测试样例使用中文 `abstract/effects/mechanism/score_reason`，避免旧英文 fixture 掩盖新契约。

- [ ] **Step 2: 运行测试确认 RED**

Run: `python tests/test_research_pipeline.py`

Expected: 新增测试因当前 validator 接受英文摘要和缺失推荐理由而失败。

- [ ] **Step 3: 写页面契约失败测试**

断言 `renderRecommendations()` 使用 `p.abstract` 渲染 `.rec-summary`，使用 `p.recommendation_reason` 渲染 `.rec-why`，使用 `p.title` 渲染带“原标题”的 `.rec-original`，并断言推荐渲染函数不读取 `p.score_reason`。

- [ ] **Step 4: 运行页面测试确认 RED**

Run: `python tests/test_page_recommendations.py`

Expected: 当前页面仍把英文 `title` 作为 `.rec-title` 并读取 `score_reason`，测试失败。

- [ ] **Step 5: 写 release gate 失败测试**

在 `tests/test_build.py` 构造当前周静态数据：无推荐、推荐缺理由、英文摘要三种情况，调用 gate helper 并断言分别产生清晰错误。

- [ ] **Step 6: 运行构建测试确认 RED**

Run: `python tests/test_build.py`

Expected: 当前 gate 没有中文推荐检查，新增测试失败。

- [ ] **Step 7: 检查提交策略并提交测试**

检查 `.agent/config.yml`；缺失时按 `auto_commit: true`。仅提交上述测试文件，提交信息：`test: lock Chinese recommendation contract`。

### Task 2: 实现 validator、存储与静态发布门

**Files:**
- Modify: `agent/research_run.py`
- Modify: `app/storage.py`
- Modify: `app/gates/gate_release.py`
- Modify: `tests/test_research_pipeline.py`
- Modify: `tests/test_build.py`

- [ ] **Step 1: 实现中文可读性 helper**

在 `agent/research_run.py` 增加 `validate_reader_text(value, field, paper_id, allow_unreported=False)`：要求 `abstract` 至少含 8 个 CJK 字符；拒绝大小写不敏感的 `auto-converted|待核实|待后续补|精修.*待补|votes=`。`effects/mechanism` 的 `未报告` 继续合法。

- [ ] **Step 2: 实现推荐条件校验**

在 `normalize_paper()` 中读取 `recommendation`。值为“推荐”时，要求 `recommendation_reason` 通过同一中文与占位语检查；非推荐允许空字符串。normalized paper 始终返回 `recommendation_reason`。

- [ ] **Step 3: 扩展 SQLite**

在 `app/storage.py` 的 `PAPER_COLUMNS`、建表、旧库迁移、INSERT、UPDATE 中加入 `recommendation_reason TEXT`，确保 API 和静态构建能读到该字段。

- [ ] **Step 4: 增加静态发布检查**

在 `app/gates/gate_release.py` 从 `site/index.html` 的 `__PAPERS__` 读取 papers：当前周非空时至少有一条“推荐”；每条推荐必须有中文 `abstract` 和中文 `recommendation_reason`，并拒绝内部占位语。把该检查加入 `run_all()`。

- [ ] **Step 5: 运行 validator 与 build 测试确认 GREEN**

Run: `python tests/test_research_pipeline.py` and `python tests/test_build.py`

Expected: 所有测试通过，新规则的错误信息包含 paper id 和失败字段。

- [ ] **Step 6: 检查提交策略并提交**

检查 `.agent/config.yml`；按配置提交生产代码与对应测试，提交信息：`feat: enforce Chinese recommendation content`。

### Task 3: 修改推荐卡信息层级

**Files:**
- Modify: `app/page.py`
- Modify: `tests/test_page_recommendations.py`

- [ ] **Step 1: 实现推荐卡字段映射**

把当前 `score_reason` fallback 删除。每条卡片按 `.rec-summary`=`abstract`、`.rec-why`=`recommendation_reason`、`.rec-original`=`原标题：title` 渲染；元数据和详情点击逻辑不变。

- [ ] **Step 2: 调整桌面样式**

中文总结使用 14–15px、600 字重和高对比色；推荐理由使用 12.5–13px；原标题使用 11px、低对比色并限制两行。保持两列三行在约 1280×720 首屏完整显示，按钮仍可键盘操作并有可见焦点。

- [ ] **Step 3: 运行页面测试确认 GREEN**

Run: `python tests/test_page_recommendations.py`

Expected: 中文主层级、推荐理由、原标题和“不显示 score_reason”契约全部通过。

- [ ] **Step 4: 检查提交策略并提交**

检查 `.agent/config.yml`；按配置提交页面与测试，提交信息：`feat: make recommendation cards Chinese first`。

### Task 4: 取消脚本自动推荐并固化每周流程

**Files:**
- Modify: `agent/build_run_week.py`
- Modify: `tests/test_research_pipeline.py`
- Modify: `AGENTS.md`
- Modify: `.agents/skills/edge-agent-research-pipeline/SKILL.md`
- Modify: `docs/harness.md`
- Modify: `docs/agent-guide/main-agent-workflow.md`
- Modify: `docs/agent-guide/research-prompt.md`
- Modify: `docs/agent-guide/output-contract.md`
- Modify: `docs/agent-guide/validation-rules.md`
- Modify: `docs/agent-guide/release-check.md`
- Modify: `docs/site/api-contract.md`

- [ ] **Step 1: 写自动推荐回归测试并确认 RED**

构造含端侧关键词的 arXiv/HF/vendor 候选，断言 `build_run_week.py` 转换后仍为 `recommendation="纳入"` 且理由为空。运行 `python tests/test_research_pipeline.py`，确认当前关键词逻辑使测试失败。

- [ ] **Step 2: 修改生成脚本**

所有自动转换条目统一写 `recommendation="纳入"`、`recommendation_reason=""`。保留 `is_core_edge_title()` 仅作候选审查辅助或删除其输出依赖，不允许直接发布为推荐。

- [ ] **Step 3: 同步强入口文档**

明确“全量搜集”和“Agent 推荐编辑”是两层：脚本收集不减量；主 Agent 在 validate 前填写中文结论与推荐理由并晋升推荐。记录本次教训：已有中文摘要但页面误用内部字段，以及关键词自动推荐使未完成条目进入首屏。

- [ ] **Step 4: 运行流程测试确认 GREEN**

Run: `python tests/test_research_pipeline.py`

Expected: 自动转换不会产生推荐，validator 仍要求最终 run 至少由人工/Agent 提供合格推荐。

- [ ] **Step 5: 检查提交策略并提交**

检查 `.agent/config.yml`；按配置提交脚本、测试与文档，提交信息：`fix: separate collection from recommendation curation`。

### Task 5: 重审本周推荐并重建页面

**Files:**
- Modify: `research_runs/run-20260804-104118.json`（本地审计产物，不提交）
- Modify: `data/weeks/2026-07-31.json`

- [ ] **Step 1: 获取权威摘要**

对拟保留的官方动态读取官方来源，对 arXiv 条目读取 arXiv 元数据摘要。仅根据来源重写，不从标题猜测结果；没有量化结果继续写“未报告”。

- [ ] **Step 2: 重做推荐集合**

逐条审视现有 27 条，弱相关内容改为“纳入”。保留项的 `abstract` 改成直接说明“做了什么”的中文一句话，并填写具体 `recommendation_reason`；数量由质量决定，不维持 27 条目标。

- [ ] **Step 3: 校验本周 run**

Run: `python agent/validate_research_run.py research_runs/run-20260804-104118.json --today 2026-08-04`

Expected: 结构、中文推荐字段、URL、日期、score 和 tags 全部通过。

- [ ] **Step 4: 发布到本地服务并构建静态站**

把校验后的 run 发布到现有本地服务，运行 `python app/build.py --server http://127.0.0.1:8001`，再构建 notes/SNN/WAIC 页面。

- [ ] **Step 5: 运行全部发布门**

Run: `python app/gates/gate_all.py`

Expected: release gate 包括中文推荐检查在内全部通过。

- [ ] **Step 6: 检查提交策略并提交周数据**

确认 `data/weeks/2026-07-31.json` 的既有用户改动被完整保留，只提交本任务新增的推荐字段与内容修订，提交信息：`content: curate Chinese weekly recommendations`。

### Task 6: 全量验证、部署与线上验收

**Files:**
- Generated: `site/`

- [ ] **Step 1: 运行完整测试**

Run: `python tests/test_page_recommendations.py`, `python tests/test_research_pipeline.py`, `python tests/test_build.py`, `python app/gates/gate_all.py`, `git diff --check`。

Expected: 所有测试与发布门通过，无空白错误。

- [ ] **Step 2: 部署源代码与 GitHub Pages**

仅推送本任务提交到 `master`；把已验证的 `site/` 覆盖到临时 `gh-pages` worktree，提交并推送，不删除线上历史 paper/week 文件。

- [ ] **Step 3: 在线桌面验收**

打开带缓存穿透参数的线上 URL，在约 1280×720 桌面视口检查：6 条首屏推荐均以中文结论为主；推荐理由可读；原标题弱化；内部占位语为 0；展开、搜索、详情、周切换和返回正常；关键内外链可访问；浏览器日志无 error。

- [ ] **Step 4: 视觉复核**

保存线上首屏截图并检查文字层级、裁切、重叠、对比度和首屏密度。P0/P1 问题必须修复后重新部署；P2 明确记录。

- [ ] **Step 5: 最终远端核对**

确认 `origin/master` 和 `origin/gh-pages` 指向本次提交，并确认工作区只剩用户原有、与本任务无关的未提交文件。

## Plan Self-Review

- Spec coverage：展示、字段、脚本边界、双层 gate、本周内容修订和线上验收均有对应任务。
- Placeholder scan：计划无待定实现项；“未报告”仅表示来源未提供效果，是项目合法值。
- Type consistency：全流程统一使用 `recommendation_reason: string`；仅当 `recommendation == "推荐"` 时必填。
