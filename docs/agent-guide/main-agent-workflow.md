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
- 不限论文，官方动态/开源大项目重大更新/技术博客都要（B 档边界：技术可迁移但作者必须提到端侧场景）。
- 过滤 GUI agent、过滤常见方法无创新。
- 每篇给 2 维评分 + 多标签 tags + source_tier + open_source + 大白话 abstract/effects/mechanism。
- arXiv date 取自元数据，不许自填。
- 输出符合 `output-contract.md`。子 agent 只产 JSON，不改代码/网页/服务器。

## 4. 保存调研结果

```text
research_runs/run-YYYYMMDD-HHMMSS.json
```

## 5. 主 agent 筛选 + 评分（不交给子 agent）

主 agent 亲自在候选上做：日期过滤 7 天 → 关键词粗筛 → 过滤 GUI → 过滤常见方法 → affiliation 粗筛 → 死链检查 → 去重 → 2 维评分 + tags + source_tier。合格的全收，列表轻量罗列不写详细分析，可以多一些。

## 6. 本地校验

```powershell
python agent/validate_research_run.py research_runs/run-YYYYMMDD-HHMMSS.json
```

校验：必填字段、source_tier 枚举、tags 词表、date 7 天窗口、score=2 维之和、官方域名、github URL、vendors 非空、死链检查、**arXiv date 核对**、跨 run 去重 warning。失败处理：date 与 arXiv 不一致改成真实提交日或丢弃；死链/内容不对题丢弃；字段缺失补全。不凑数。

## 7. 内容抽检

publish 前对 `source_tier=官方动态` 和 `source_tier=开源大项目` 条目：fetch URL 核验页面内容 vs 标题摘要，对不上就丢。

## 8. 发布到服务器

```powershell
python app/server.py --host 127.0.0.1 --port 8001
python agent/publish_results.py research_runs/run-YYYYMMDD-HHMMSS.json --server http://127.0.0.1:8001
```

publish 成功后自动写 `data/.last_run_papers.json`（下次 validate 跨 run 去重用）+ 触发 gh-pages 异步部署。

## 9. 验证页面

打开 `http://127.0.0.1:8001/`。页面按标签筛选展示，source_tier 优先 + score 排序。点标题进详情页（短摘要+标签+原文链接）。`GET /api/papers` 只返最新 run。无合格内容显示空状态。

## 10. 收尾

更新 `data/.last_run` 时间戳（ISO 8601）。本周错误沉淀进 `AGENTS.md` 教训 + `validation-rules.md` + `research-prompt.md`。跑 `python tests/test_research_pipeline.py`、`tests/test_build.py`、`app/gates/gate_all.py` 确认 harness 健康。
