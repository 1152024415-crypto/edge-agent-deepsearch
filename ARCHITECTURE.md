# ARCHITECTURE.md — edge_agent 顶层领域地图

## 核心原则
**搜索由 agent 执行，本仓负责规则、状态、内容、校验与展示。**

本仓不是传统爬虫 / 采集适配器项目。Codex / Hermes 等 agent 读取 `README.md` 的提示词，使用自身搜索、浏览、阅读工具去找文章；本仓只保存规则、产出、去重状态、质量 gate 和静态展示结果。

## 两类职责分离

### Agent 执行层（Codex / Hermes 等工具）
动态发生在 agent 的一次运行中：
- 读取 `README.md` / `AGENTS.md` / `SPEC.md`
- 读取 `data/.last_run` 计算过去一周窗口
- 读取 `data/index.json` 获取已收录集
- 使用 agent 自身工具检索四类信息源：学术论文 / 厂商博客 / GitHub releases / 产品大会发布
- 阅读原文，抽取可验证事实，禁止补编效果数据
- 按评分体系筛选与打分
- 写入 `content/posts/<slug>.md`，同步更新 `data/index.json`
- 运行 gate，build `site/`，按需要 push 到 GitHub

### 展示与记录层（本仓 + GitHub Pages）
稳定保存在仓库中，可审计、可恢复：
- 规则：`README.md` / `AGENTS.md` / `docs/product-specs/SPEC.md`
- 架构与设计：`ARCHITECTURE.md` / `docs/design-docs/DESIGN.md`
- 状态：`data/index.json` / `data/.last_run` / `data/vendors.yaml`
- 内容：`content/posts/*.md`
- 机械化强制：`scripts/gate_*.py` / `scripts/frontmatter.schema.json`
- 展示构建：`scripts/build.py` 生成 `site/`
- GitHub Pages：只展示 build 好的静态结果，不承担搜索、过滤、去重、状态判断

## 数据流

```
[README 搜集提示词 + SPEC 评分规则]
    │
    ▼
[Codex / Hermes 等 agent]
    │  读 .last_run + index.json
    │  搜索四类信息源：论文 / 厂商博客 / GitHub releases / 产品发布
    ▼
[候选条目] ──查 index.json 去重──▶ [新条目]
    │  阅读原文 + 按 SPEC 第六节评分
    ▼
[纳入条目] ──▶ content/posts/<slug>.md（frontmatter + 正文）
    │  更新 index.json
    ▼
[gate_all.py] ──▶ [build.py]
    │              │
    │              ▼
    │           site/（静态成品）
    │              │
    ▼              ▼
[修正 post/index]   [GitHub Pages 展示]
```

## 边界规则
- 搜索能力来自 agent 工具，不默认在仓内实现固定 API 适配器
- 本仓必须记录 agent 的内容产出与去重状态，不能只把进度留在对话里
- GitHub Pages 只展示 `site/` 成品；展示层不做搜索、过滤、去重
- `index.json` / `.last_run` 是项目内状态文件，随 agent 搜集更新并由 git 跟踪
- `content/posts/` 是核心调研资产，每条一个 Markdown，frontmatter 必须过 schema
- build/push 前必须跑 `python scripts/gate_all.py` 且 exit 0

## 状态与记忆边界
- **Agent 工具记忆**：只存项目指针和长期约束，不存已收录列表、运行进度、临时判断
- **项目内状态文件**（`data/`）：精确记录去重索引、时间窗口、vendor 白名单
- **调研内容**（`content/`）：收录条目的事实与分析，必须可由原文追溯
- **工作教训**（`AGENTS.md`）：每次 agent 犯错后追加防再犯规则

## 待定（影响 build / site 结构）
- 网站选型：沿用 `scripts/build.py` 极简 SSG，还是改 Hugo / Astro / MkDocs
- 是否增加 agent 周更运行清单或提醒机制
