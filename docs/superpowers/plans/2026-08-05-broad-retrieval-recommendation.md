# 广检索、推荐聚焦 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让每周调研动态覆盖最近 7 天的四类来源，尽可能保留相关内容，并只通过主 Agent 推荐控制用户优先阅读内容。

**Architecture:** 新增统一的检索窗口与覆盖清单模块；arXiv 和厂商脚本消费统一窗口，组装器校验四类来源覆盖后才生成 run。候选过滤只负责硬边界，推荐继续由主 Agent人工完成。

**Tech Stack:** Python 标准库、unittest、现有 JSON research run 契约。

---

### Task 1: 统一动态检索窗口

**Files:**
- Create: `agent/research_collection.py`
- Modify: `agent/arxiv_curl_sweep.py`
- Modify: `agent/collect_vendors.py`
- Modify: `agent/collect_github_trending.py`
- Test: `tests/test_research_collection.py`

- [ ] 写失败测试：固定运行日 `2026-08-05` 得到 `2026-07-30..2026-08-05`，共 7 个日期。
- [ ] 运行 `python -m unittest tests.test_research_collection.ResearchWindowTests -v`，确认因模块缺失而失败。
- [ ] 实现 `collection_window(today, days=7)` 和命令行 `--today` 注入。
- [ ] 移除三个采集脚本中的固定日期常量，统一使用窗口模块。
- [ ] 重跑测试确认通过。
- [ ] 不创建提交；用户未要求修改 Git 历史。

### Task 2: arXiv 分页和宽收录

**Files:**
- Modify: `agent/arxiv_curl_sweep.py`
- Modify: `agent/build_run_week.py`
- Test: `tests/test_research_collection.py`

- [ ] 写失败测试：第一页满 100 条时读取第二页；普通但相关的量化/serving 内容保留；完全无关医疗内容过滤。
- [ ] 运行对应测试并确认因缺少分页和边界 API 失败。
- [ ] 把 arXiv URL 构造拆为含 `start`/`max_results` 的纯函数，按页抓取并在窗口下界后停止。
- [ ] 将候选判断分为“端侧直接相关、端侧技术栈相邻、完全无关”，前两类保留，后者删除。
- [ ] 重跑测试确认通过。
- [ ] 不创建提交；用户未要求修改 Git 历史。

### Task 3: 检索覆盖清单

**Files:**
- Modify: `agent/research_collection.py`
- Modify: `agent/build_run_week.py`
- Test: `tests/test_research_collection.py`

- [ ] 写失败测试：HF 缺少窗口内一天、GitHub 未检查 release、厂商缺少规范清单成员时，覆盖校验分别失败。
- [ ] 运行测试并确认因覆盖校验尚不存在而失败。
- [ ] 定义 `research_runs/collection-manifest.json` 契约，验证窗口、四类来源状态、HF 日期、厂商名称和 GitHub release 检查。
- [ ] 组装器默认要求有效 manifest；提供只用于历史恢复的显式 `--allow-incomplete-coverage`，正常周流程不得使用。
- [ ] 重跑测试确认通过。
- [ ] 不创建提交；用户未要求修改 Git 历史。

### Task 4: 修正归属和推荐边界

**Files:**
- Modify: `agent/build_run_week.py`
- Modify: `tests/test_research_pipeline.py`

- [ ] 写失败测试：摘要中提到 Qwen/NVIDIA 但作者无公司信息时仍是学校预印本；自动转换条目永远不推荐。
- [ ] 运行测试确认厂商误判用例失败。
- [ ] 公司识别只读取候选的明确 affiliation/作者机构字段，不读取标题和摘要。
- [ ] 官方动态根据内容计算相关度，不再固定为 8；推荐字段继续固定为“纳入”。
- [ ] 重跑测试确认通过。
- [ ] 不创建提交；用户未要求修改 Git 历史。

### Task 5: 同步项目规则

**Files:**
- Modify: `AGENTS.md`
- Modify: `.agents/skills/edge-agent-research-pipeline/SKILL.md`
- Modify: `docs/harness.md`
- Modify: `docs/agent-guide/main-agent-workflow.md`
- Modify: `docs/agent-guide/research-prompt.md`
- Modify: `docs/agent-guide/output-contract.md`
- Modify: `docs/agent-guide/validation-rules.md`
- Modify: `docs/references/mcp-setup.md`

- [ ] 将所有文档统一为“广搜、硬边界少删、推荐聚焦”。
- [ ] 删除“普通方法无创新直接不收”和“纯云端一律排除”的冲突表述，改为相关内容保留但低分、不自动推荐。
- [ ] 写明动态窗口、分页、覆盖清单和公司归属证据规则。
- [ ] 搜索旧口径，确保强入口之间无相互冲突。
- [ ] 不创建提交；用户未要求修改 Git 历史。

### Task 6: 完整验证

**Files:**
- Test: `tests/test_research_collection.py`
- Test: `tests/test_research_pipeline.py`
- Test: `tests/test_build.py`
- Test: `app/gates/gate_all.py`

- [ ] 运行 `python -m unittest tests.test_research_collection -v`。
- [ ] 运行 `python tests/test_research_pipeline.py`。
- [ ] 运行 `python tests/test_build.py`。
- [ ] 运行 `python app/gates/gate_all.py`。
- [ ] 运行 `git diff --check`，只接受 Windows 行尾提醒，不接受空白错误。
- [ ] 检查 `git status --short`，确认保留用户原有 `research_runs/liverec.html`，未修改或删除。
- [ ] 不创建提交；用户未要求修改 Git 历史。

