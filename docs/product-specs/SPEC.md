---
doc: product-spec
status: source-of-truth
updated: 2026-06-25
---

# SPEC.md — 端侧 AI Agent 周报雷达 需求规格

> 本文件是项目**规格索引**（source of truth 的元信息与决策指针）。
> **完整运行提示词（检索式 / 纳入排除 / 评分体系 / 输出格式 / 语义分析）权威全文在 [README.md](../README.md)**，本文件不重复，避免漂移。
> spec 变更流程：先改 README 提示词 → 本文件记决策指针 → 再改实现；实现完对照 README 验证。

## 需求一句话
端侧 AI Agent 周报雷达：runtime agent 每周搜集端侧 agent / 推理最新动态（过去一周、大厂优先），本地 build，push 成品到 GitHub 纯展示。

## 核心边界
- 时间窗口：过去一周（滚动，读 `data/.last_run`）
- 范围：端侧 agent 优先，端侧推理引擎次之
- 大厂优先级（非硬排除学生）：评分加权
- 不分语言（英文为质量软信号）
- 数据可信：效果必须来自原文，摘不到写"未报告"，禁止补编
- 两层架构：runtime 搜集（本地）+ GitHub 纯展示

## 决策记录
决策理由留 `docs/decisions/`（ADR，待建）：评分权重 35/25/20/15/5、7 天窗口、两层分离、白名单 17 家、网站选型。

## 待定
- 网站选型（Hugo / Astro / MkDocs）→ 决定 build + `site/` 结构
- frontmatter schema 定稿（README 第八节字段 → `scripts/frontmatter.schema.json`）
- 归档策略（一周窗口 + 累积 posts）
