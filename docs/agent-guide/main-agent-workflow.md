# Main Agent Workflow

本文件给主 code agent 使用。主 agent 负责调度、校验和发布；调研子 agent 只负责搜索和输出结构化结果。

## 1. 准备上下文

主 agent 必须先读取：

- `AGENTS.md` → `docs/harness.md` → `.agents/skills/edge-agent-research-pipeline/SKILL.md`
- `docs/agent-guide/research-prompt.md`、`output-contract.md`、`validation-rules.md`
- `docs/references/mcp-setup.md`（MCP 配置和工具用法）、`tag-taxonomy.md`、`big-projects-whitelist.md`、`vendor-research-guide.md`

## 2. 查时间窗口

读 `data/.last_run` 时间戳，距本次 ≥7 天才跑；<7 天提示「本周已调研」停止。窗口是当前日期过去 7 天。

## 3. 发起调研子 agent

prompt 必须注入 `docs/agent-guide/research-prompt.md` 全文 + 硬约束。**不许主 agent 自写简化版 prompt**。对子 agent 要求：

- 用 arXiv MCP + HF Daily Papers MCP + GitHub MCP + websearch 广搜集（详见 `mcp-setup.md`），**不定硬数量目标，有多少合格收多少**。某 query 返回过少就自行放宽/换词。
- 不限论文，官方动态/开源大项目重大更新/技术博客都要。明确端侧和端侧技术栈必收；有直接迁移价值的通用 AI 推理/serving 也保留并低分。常见方法不能因为“不够推荐”提前删除。
- 只硬过滤纯 GUI 且无系统贡献、完全无关、越窗、来源不可信、链接不匹配和重复项。
- 搜集阶段可给 2 维初值 + tags + source_tier + open_source + 大白话 abstract/effects/mechanism；统一 `title_zh=""`、`recommendation=纳入`、`recommendation_reason=""`、`edge_agent_scope=待核实`、`edge_agent_evidence=""`，且不自动添加`方向:端侧agent`。最终分数、标签、端侧 Agent 范围和 affiliation 由主 agent 确认。
- arXiv date 取自元数据，不许自填。旧论文由更新扫描召回时，逐篇对比旧版；只有实验、方法、数据、代码或结论有实质变化才填写 `arxiv_revision_note` 并保留，排版/勘误更新直接丢弃。
- 输出符合 `output-contract.md`。子 agent 只产 JSON，不改代码/网页/服务器。

## 4. 校验检索覆盖

四类来源必须共同生成 `research_runs/collection-manifest.json`。运行日向前含当日恰好 7 个自然日；arXiv 大类扫描必须分页并自然到达窗口外（命中页数上限算失败）；HF 必须列齐 7 个日期；GitHub 必须分别完成 Trending 和白名单 release；厂商必须为 24 个规范来源逐家记录至少一个成功访问的官方 feed/sitemap。四个最终候选 JSON 完成后运行 `python agent/attest_candidates.py`，把路径、条数、文件 SHA-256、逐记录指纹和稳定 title+URL+来源日期身份写入 manifest。组装器为每条内容写入唯一 `candidate_source` + `candidate_ref`；候选不能复用，最终原标题/URL/日期必须匹配。缺项、全不可达、条数/哈希/身份/血缘不一致时返回搜集步骤，不能继续组装。

## 5. 保存调研结果

```text
research_runs/run-YYYYMMDD-HHMMSS.json
```

## 6. 主 agent 筛选 + 评分（不交给子 agent）

主 agent 亲自在候选上做：日期过滤 → 完全无关过滤 → 纯 GUI 无系统贡献过滤 → affiliation 证据核实 → 链接匹配 → 去重 → 最终 2 维评分 + tags + source_tier → 逐条完成`edge_agent_scope`。只有 Agent 关键闭环至少部分运行在设备端才标`手机`/`PC`/`其他端侧`并填写证据；这些条目全部推荐，排序手机 > PC > 其他端侧。普通量化、缓存、检测或云端 Agent 基础设施标`非端侧Agent`，仍可按贡献推荐或完整收录。

## 7. 本地校验

```powershell
python agent/validate_research_run.py research_runs/run-YYYYMMDD-HHMMSS.json
```

校验首先检查同目录的 `collection-manifest.json`、候选文件证明和逐条候选血缘，再检查内容契约、精确 7 个自然日、评分、标签、官方域名、公司 affiliation 权威证据 URL、链接、arXiv date 和跨 run 去重。组装后的 run 内嵌 manifest 与血缘，发布客户端和服务器再次复验。服务端与发布端必须配置同一个 `EDGE_PUBLISH_TOKEN`。历史恢复才允许本地显式加 `--allow-incomplete-coverage`；正常周报禁止使用。

## 8. 内容抽检

publish 前对 `source_tier=官方动态` 和 `source_tier=开源大项目` 条目：fetch URL 核验页面内容 vs 标题摘要，对不上就丢。

## 9. 采集独立社区雷达

检索当前日期过去 7 个自然日的 X、Reddit、Hacker News、厂商论坛和开发者论坛，写 `data/community_radar.json`。每类来源必须记录覆盖状态与说明；条目按手机 > PC > 其他端侧 > 通用技术排序，并填写中文名称、总结、价值判断和核验状态。X 只能使用无需登录可打开、能核验发布时间的原帖；受限就明确写 `limited`。社区讨论不进入 research run，找到一手材料后仍须重新走正式来源校验。

## 10. 发布到服务器

```powershell
$env:EDGE_PUBLISH_TOKEN = "<服务端与发布端共享的随机长令牌>"
python app/server.py --host 127.0.0.1 --port 8001
python agent/publish_results.py research_runs/run-YYYYMMDD-HHMMSS.json --server http://127.0.0.1:8001
```

publish 成功后自动写 `data/.last_run_papers.json`（下次 validate 跨 run 去重用）+ 触发 gh-pages 异步部署。

## 11. 验证页面

打开 `http://127.0.0.1:8001/`。页面按标签筛选展示，source_tier 优先 + score 排序。点标题进详情页（短摘要+标签+原文链接）。`GET /api/papers` 只返最新 run；`GET /api/community` 只返独立社区线索。确认社区雷达在完整资料库之后、GitHub 发现线索之前，来源覆盖和 X 受限状态可见，社区筛选不改变正式列表。无合格内容显示空状态。

## 12. 收尾

更新 `data/.last_run` 时间戳（ISO 8601）。本周错误沉淀进 `AGENTS.md` 教训 + `validation-rules.md` + `research-prompt.md`。跑 `python tests/test_research_pipeline.py`、`tests/test_build.py`、`app/gates/gate_all.py` 确认 harness 健康。
