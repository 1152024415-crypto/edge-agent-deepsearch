# 真正端侧 Agent 强制推荐 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让经来源核实的手机、PC和其他端侧 Agent 必须被推荐并按设备优先级展示，同时保持完整收录不缩水。

**Architecture:** 在 research run 中增加经主 Agent 核实的`edge_agent_scope`和`edge_agent_evidence`，把自动搜集与编辑认定分开。校验器、存储、页面和 release gate 共用同一语义，并通过测试拦截漏推荐、关键词误判和排序回归。

**Tech Stack:** Python 3 标准库、SQLite、原生 HTML/CSS/JavaScript、unittest、GitHub Pages 构建发布流程。

---

### Task 1: 固化 research run 端侧 Agent 契约

**Files:**
- Modify: `tests/test_research_pipeline.py`
- Modify: `agent/research_run.py`
- Modify: `docs/agent-guide/output-contract.md`
- Modify: `docs/agent-guide/validation-rules.md`

- [ ] **Step 1: 写失败测试**

增加四组最小用例：`待核实`不能发布；手机/PC/其他端侧必须带中文证据、`方向:端侧agent`、`score_relevance>=8`且必须推荐；`非端侧Agent`不得带端侧 Agent 标签；合法手机端 Agent 可以通过。

- [ ] **Step 2: 运行测试并确认按预期失败**

Run: `python -m unittest tests.test_research_pipeline.ResearchRunValidationTest -v`  
Expected: 新增断言因字段尚未校验而失败。

- [ ] **Step 3: 实现最小契约**

在`agent/research_run.py`增加：

```python
ALLOWED_EDGE_AGENT_SCOPES = {"待核实", "手机", "PC", "其他端侧", "非端侧Agent"}
DIRECT_EDGE_AGENT_SCOPES = {"手机", "PC", "其他端侧"}
```

标准化输出保留`edge_agent_scope`和`edge_agent_evidence`，按设计文档执行交叉校验。更新输出契约和校验规则中的字段表、正反例与强制推荐规则。

- [ ] **Step 4: 运行测试并确认通过**

Run: `python -m unittest tests.test_research_pipeline.ResearchRunValidationTest -v`  
Expected: PASS。

- [ ] **Step 5: 检查`.agent/config.yml`后提交**

默认`auto_commit: true`；只暂存本任务涉及的文件并提交`feat: validate direct edge agent recommendations`。

### Task 2: 阻止自动脚本把关键词当成端侧 Agent 事实

**Files:**
- Modify: `tests/test_research_collection.py`
- Modify: `tests/test_build.py`
- Modify: `agent/build_run_week.py`
- Modify: `docs/agent-guide/research-prompt.md`
- Modify: `.agents/skills/edge-agent-research-pipeline/SKILL.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: 写失败测试**

构造标题含`edge/mobile/agent`的普通推理条目和真正手机 Agent 条目，断言自动转换都只能输出`edge_agent_scope=待核实`、空证据、`recommendation=纳入`，并且不能自动添加`方向:端侧agent`。

- [ ] **Step 2: 运行测试并确认按预期失败**

Run: `python -m unittest tests.test_research_collection tests.test_build -v`  
Expected: 现有自动标签或缺失新字段导致失败。

- [ ] **Step 3: 实现最小自动搜集行为**

所有`convert_*`输出统一增加：

```python
"edge_agent_scope": "待核实",
"edge_agent_evidence": "",
```

移除以“没有方向标签”为理由自动插入`方向:端侧agent`的逻辑。prompt、Skill和AGENTS明确主 Agent 必须阅读来源后分类，手机优先、PC次之、其他端侧仍强制推荐。

- [ ] **Step 4: 运行测试并确认通过**

Run: `python -m unittest tests.test_research_collection tests.test_build -v`  
Expected: PASS。

- [ ] **Step 5: 检查`.agent/config.yml`后提交**

默认`auto_commit: true`；只暂存本任务文件并提交`fix: require source review for edge agent classification`。

### Task 3: 持久化范围并统一排序

**Files:**
- Modify: `tests/test_research_pipeline.py`
- Modify: `app/storage.py`
- Modify: `app/server.py`
- Modify: `agent/publish_results.py`
- Modify: `docs/site/api-contract.md`

- [ ] **Step 1: 写失败测试**

增加数据库迁移、发布字段保留和排序测试：推荐条目顺序必须为手机、PC、其他端侧、非端侧推荐；同范围内继续按来源层级和分数排序。

- [ ] **Step 2: 运行测试并确认按预期失败**

Run: `python -m unittest tests.test_research_pipeline -v`  
Expected: 新字段未持久化或排序仍以来源层级为第一键而失败。

- [ ] **Step 3: 实现存储和 API**

SQLite新增文本列并给旧库默认值`非端侧Agent`和空证据；upsert、行映射、发布 payload 全链路传递字段。排序使用范围优先级：手机 0、PC 1、其他端侧 2、其余 3，再接既有来源层级和分数。

- [ ] **Step 4: 运行测试并确认通过**

Run: `python -m unittest tests.test_research_pipeline -v`  
Expected: PASS。

- [ ] **Step 5: 检查`.agent/config.yml`后提交**

默认`auto_commit: true`；提交`feat: persist and rank edge agent scope`。

### Task 4: 桌面推荐区突出设备范围并增加发布门

**Files:**
- Modify: `tests/test_page_recommendations.py`
- Modify: `tests/test_gate_release.py`
- Modify: `app/page.py`
- Modify: `app/gates/gate_release.py`
- Modify: `app/frontmatter.schema.json`

- [ ] **Step 1: 写失败测试**

页面测试要求统一范围排序函数和三个中文徽标；gate 测试要求任何真正端侧 Agent 未推荐、缺证据、标签不一致或构建产物仍有`待核实`时失败。

- [ ] **Step 2: 运行测试并确认按预期失败**

Run: `python -m unittest tests.test_page_recommendations tests.test_gate_release -v`  
Expected: 页面无范围排序/徽标且 gate 未拦截而失败。

- [ ] **Step 3: 实现页面和 gate**

推荐列表排序第一键改为`EDGE_AGENT_PRIORITY[p.edge_agent_scope]`，卡片在中文项目名前显示`手机端 Agent`、`PC 端 Agent`或`其他端侧 Agent`徽标。gate 解析最终`__PAPERS__`并重复执行契约的关键交叉校验；schema同步新字段和`推荐`枚举。

- [ ] **Step 4: 运行测试并确认通过**

Run: `python -m unittest tests.test_page_recommendations tests.test_gate_release -v`  
Expected: PASS。

- [ ] **Step 5: 检查`.agent/config.yml`后提交**

默认`auto_commit: true`；提交`feat: highlight direct edge agents on desktop`。

### Task 5: 用修复后的流程重跑本周调研并部署验收

**Files:**
- Modify: `research_runs/run-20260805-*.json`
- Modify: `data/weekly_summary.json`
- Modify: `data/github_trending_top20.json`
- Modify: `data/weeks/2026-08-05.json`
- Modify: `data/weeks/manifest.json`
- Modify: `data/.last_run`

- [ ] **Step 1: 执行四路检索并补 Microsoft 漏检路径**

按北京时间`2026-07-30..2026-08-05`搜索 arXiv、HF Daily Papers、GitHub 与厂商官方来源；Microsoft Research 和`microsoft`官方 GitHub 需检查“首次公开代码/大提交”，不能只查 release tag 或仓库创建日。

- [ ] **Step 2: 主 Agent逐条核实和编辑**

把每条`待核实`改为四个最终范围之一。真正端侧 Agent全部推荐并填写中文名称、摘要、理由和证据；Orchard 按实际贡献收录但标`非端侧Agent`。

- [ ] **Step 3: 校验、测试和构建**

Run:

```powershell
python agent/validate_research_run.py research_runs/<run>.json
python tests/test_research_pipeline.py
python tests/test_build.py
python app/gates/gate_all.py
```

Expected: 全部 exit 0，gate 无 FAIL。

- [ ] **Step 4: 发布并部署**

使用项目现有 publish/deploy 命令发布服务器数据并更新 GitHub Pages；不得绕过 gate。

- [ ] **Step 5: 线上桌面验收**

硬刷新线上页面，核对推荐顺序、设备徽标、中文内容、完整收录数量、Orchard 分类和原文链接；检查控制台无错误。

- [ ] **Step 6: 检查`.agent/config.yml`后提交**

默认`auto_commit: true`；仅在所有验证完成后提交本轮数据和文档，提交信息`data: publish 2026-08-05 edge agent research`。

## 自检记录

- 需求覆盖：判定边界、手机/PC/其他设备优先级、完整收录、强制推荐、Orchard 漏检和线上验收均有对应任务。
- 占位扫描：计划没有把实现细节留为 TBD/TODO；`<run>`仅表示本次命令实际生成的时间戳文件名。
- 类型一致性：全计划统一使用`edge_agent_scope`、`edge_agent_evidence`和五个固定枚举值。
