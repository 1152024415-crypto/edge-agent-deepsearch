# Design

## 设计原则

edge_agent 的核心不是网页生成器，而是 agent 调研结果的发布链路：

```text
main code agent -> research subagent -> research_runs/*.json -> validate -> publish -> server -> page refresh
```

## 组件

### 1. Agent Guide

`docs/agent-guide/` 给 agent 读：

- `research-prompt.md`：怎么搜。
- `output-contract.md`：怎么输出。
- `validation-rules.md`：哪些内容不能收。
- `main-agent-workflow.md`：主 agent 怎么调度、校验、发布。

### 2. Research Run

调研结果保存在 `research_runs/<run_id>.json`。这是子 agent 和主 agent 之间的交接格式。**完整字段以 `docs/agent-guide/output-contract.md` 为准**（方案 B：2 维评分 + 多标签 tags + source_tier + open_source），本节只列核心字段。

主字段：

- `title`
- `abstract`
- `effects`
- `mechanism`
- `paper_url`
- `date`
- `score`（= score_relevance + score_contribution，0-20）
- `source_tier`（官方动态 / 开源大项目 / 公司项目 / 学校顶会 / 学校预印本）
- `tags`（1-8，取自 data/tags.yaml）
- `insight_person`
- `wiki_url`

### 3. Validation

`agent/research_run.py` 是校验库。

`agent/validate_research_run.py` 是 CLI。

校验规则：

- 必须是真实论文。
- 必须是当前日期过去 7 天。
- `paper_url` 必须是 http(s) URL。
- `score` 必须是 0 到 20。
- `id` 不能重复。
- 必填字段不能为空。

### 4. Publish

`agent/publish_results.py` 负责把校验后的 payload POST 到：

```text
POST /api/research-runs
```

发布脚本不负责搜索、不负责修论文内容。

### 5. Server

`app/server.py` 使用 Python 标准库 HTTP server 和 SQLite。

接口：

- `GET /`
- `GET /api/papers`
- `POST /api/research-runs`
- `POST /api/insights`

服务器再次校验 research run，避免绕过本地脚本直接写坏数据。

### 6. Static Fallback

`app/build.py` 仍可从 `content/papers/*.md` 生成 `site/index.html`，但这只是 fallback。最终展示以服务器 `/api/papers` 为准。

## 错误处理

- 校验失败：主 agent 不发布，回到子 agent 结果修正。
- 服务器拒绝：`publish_results.py` 输出错误，主 agent 停止。
- 页面无数据：显示空状态。
- 洞察人/wiki 更新失败：服务器返回 400 或 404。

## 测试

- `tests/test_research_pipeline.py`：校验、发布、服务器 API。
- `tests/test_build.py`：静态 fallback 页面。
- `app/gates/gate_all.py`：旧 Markdown 内容 gate。
