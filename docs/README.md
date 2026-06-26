# Docs Index

本目录按“谁来读、解决什么问题”组织。新 codeagent 应先读项目 skill，再按这里加载具体文档。

## Agent Guide

| 文件 | 读者 | 用途 |
|---|---|---|
| `docs/agent-guide/main-agent-workflow.md` | 主 code agent | 调度子 agent、校验、发布 |
| `docs/agent-guide/research-prompt.md` | 调研子 agent | 搜索和研究提示词 |
| `docs/agent-guide/output-contract.md` | 主 agent / 子 agent | `research_runs/*.json` 输出契约 |
| `docs/agent-guide/validation-rules.md` | 主 agent / 子 agent | 论文真实性和时间窗口规则 |

## Product And Architecture

| 文件 | 用途 |
|---|---|
| `docs/product-specs/SPEC.md` | 产品目标、展示字段、收录规则 |
| `docs/design-docs/DESIGN.md` | 系统设计和组件边界 |
| `ARCHITECTURE.md` | 顶层数据流 |

## Server And Display

| 文件 | 用途 |
|---|---|
| `docs/site/api-contract.md` | 服务器 API 契约 |
| `docs/site/display-spec.md` | 服务器展示页规格 |
| `docs/site/github-pages-requirements.md` | 静态 fallback 的历史规格 |
| `app/server.py` | HTTP 路由和服务器入口 |
| `app/storage.py` | SQLite 存储 |
| `app/page.py` | 页面 shell |

## Plans And Debt

| 文件 | 用途 |
|---|---|
| `docs/plans/2026-06-25-agent-research-publish-pipeline.md` | research publish pipeline 实现计划 |
| `docs/plans/2026-06-25-github-pages-paper-table.md` | 静态 fallback 表格历史计划 |
| `docs/plans/tech-debt-tracker.md` | 后续技术债 |
