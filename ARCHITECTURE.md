# ARCHITECTURE.md — edge_agent 顶层领域地图

## 核心原则
**搜集是 runtime，GitHub 只是展示。** 搜集逻辑永远在本地，GitHub 只是个看板。

## 两层环境分离

### Runtime 层（本地 `D:\proj\edge_agent`）
agent 干活的地方，动态、运行时发生：
- 搜集（四类信息源检索）
- 过滤（硬门槛 gate + 评分体系）
- 去重（`data/index.json`）
- frontmatter 产出（`content/posts/`）
- 状态管理（`index.json` / `.last_run`）
- 本地 build 静态站
- 整套 harness（AGENTS.md 免疫系统 / 机械化强制 / 熵管理）

### 展示层（GitHub 仓库）
纯看板，零逻辑：
- 只接收 runtime build 好的静态成品
- GitHub Pages 开启即展示
- 不承担搜集 / 过滤 / 去重 / 状态（那些都在本地 runtime）

## 数据流

```
[四类信息源: 学术论文 / 厂商博客 / GitHub / 产品发布]
    │  runtime 搜集（每周，读 .last_run 算一周窗口）
    ▼
[候选条目] ──查 index.json 去重──▶ [新条目]
    │  评分体系评估（SPEC 第六节）
    ▼
[纳入条目] ──▶ content/posts/<slug>.md（frontmatter）
    │  更新 index.json + .last_run
    ▼
[本地 build] ──▶ site/（静态成品）
    │  push
    ▼
[GitHub 展示层] ──▶ GitHub Pages
```

## 边界规则
- 搜集 / 过滤 / 去重 / 状态逻辑永远在 runtime，不进 GitHub
- GitHub 只放 `site/` 成品
- 状态文件（`index.json` / `.last_run`）在本地 runtime，git 跟踪（可恢复、可审计）

## 状态与记忆边界
- **Hermes memory**：只存项目指针（位置 / spec-driven / 长期约束），不存进度、不存已收录列表
- **项目内状态文件**（`data/`）：易变、需精确跟踪（去重索引 / 时间戳），随每次更新变
- **调研内容**（`content/`）：核心资产，每条一个 Markdown
- **进度回顾**：跨 session "做到哪了"用 session_search，不存 memory

## 待定（影响 build / site 结构）
- 网站选型：Hugo / Astro / MkDocs（未定）
- 选型定后补 `scripts/` build 脚本和 `site/` 结构
