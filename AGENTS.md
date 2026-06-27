# AGENTS.md — edge_agent 项目工作指引

> 本文件是 agent 在此项目工作的目录表和免疫系统。
> 仓库是唯一记录系统：流程、契约、教训都写进 repo，不靠对话记忆。

## 必读项目 Skill

新的 codeagent 进入本仓库后，先读取项目内 skill：

```text
.agents/skills/edge-agent-research-pipeline/SKILL.md
```

这个 skill 是本项目的工作入口，说明项目目标、主 agent / 子 agent 边界、research run 契约、校验发布命令和不可违反规则。后续维护时，`AGENTS.md` 和该 skill 必须保持一致。

## 项目一句话

端侧 AI Agent 论文雷达：主 code agent 调度调研子 agent 搜索最近两周端侧 agent 相关论文，主 agent 校验后把结构化结果发布到服务器，网页从服务器刷新最新论文列表。

## 架构边界

项目按两大模块解耦 + 能力层：

- **Agent 调研模块**（`agent/`）：research_run 校验库、validate CLI、publish 脚本。主 agent 调度子 agent 搜索论文，产出 `research_runs/*.json`，校验后发布。
- **网页 App 模块**（`app/`）：server HTTP 路由、storage SQLite、page 展示页、build 静态 fallback、gates 内容校验。接收发布结果并展示。
- **能力层**（`.agents/skills/` + `AGENTS.md`）：给 codeagent 的工作指引和 skill，新 codeagent 强入口。
- 服务器不搜索论文，只接收校验过的 research run；搜索由 agent 工具完成。

## 目录地图

两大模块解耦 + 能力层：

| 路径 | 用途 |
|---|---|
| `.agents/skills/edge-agent-research-pipeline/SKILL.md` | 【能力层】项目工作 skill，新 codeagent 优先读取 |
| `AGENTS.md` | 【能力层】agent 总指引（本文件） |
| `agent/` | 【模块1·调研 pipeline】research_run/validate/publish |
| `agent/research_run.py` | research run 校验库 |
| `agent/validate_research_run.py` | 发布前校验 CLI |
| `agent/publish_results.py` | POST 到服务器 |
| `app/` | 【模块2·网页/server】server/storage/page + 静态 fallback |
| `app/server.py` | HTTP 路由和服务器入口 |
| `app/storage.py` | SQLite 存储和 paper upsert/query |
| `app/page.py` | 服务器展示页 HTML shell |
| `app/build.py` | 静态 fallback build（生成 site/index.html） |
| `app/gates/` | content/papers frontmatter 校验 gate |
| `app/frontmatter.schema.json` | frontmatter 字段 schema |
| `tests/` | 跨模块测试（test_research_pipeline, test_build） |
| `research_runs/` | 子 agent 产出的 run JSON，默认不提交 |
| `content/papers/` | 兼容旧静态 build 的本地 Markdown |
| `site/` | 静态 fallback 产物，不提交 |
| `data/` | index.json / vendors.yaml 共享数据 |
| `docs/` | 文档（agent-guide / site / design-docs / plans / references） |
| `README.md` | 人类入口和常用命令 |
| `ARCHITECTURE.md` | 顶层架构和数据流 |

## 主 Agent 工作流

> 总览见 `docs/harness.md` 第 3 节每周调研主循环。本节是主 agent 每周硬步骤，和 harness 保持一致，不许跳步。

1. 读 `.agents/skills/edge-agent-research-pipeline/SKILL.md`、`docs/agent-guide/main-agent-workflow.md`、`docs/agent-guide/research-prompt.md`、`output-contract.md`、`validation-rules.md`。强入口，不许跳过。
2. 检查 `data/.last_run`：读上次调研时间戳，距本次 ≥7 天才跑；<7 天提示"本周已调研"并停止。防重复跑、防拿旧 run 充本周。
3. 发起调研子 agent。**prompt 必须注入 `docs/agent-guide/research-prompt.md` 全文 + 硬约束**（大厂优先、官方域名白名单、14 天窗口、三方向分类、keywords、不凑数）。**不许主 agent 自写简化版 prompt**，简化版会让子 agent 漏掉标准，编造断链。
4. 子 agent 搜索本周（过去 14 天）端侧 agent 论文 + 17 家大厂官方动态，产出易读版 `abstract`/`effects`/`mechanism` + 6 维打分 + `keywords` + `category` + `source_type` + `vendors`。子 agent 只输出结构化 JSON，不改代码、网页、服务器。
5. 主 agent 保存为 `research_runs/run-YYYYMMDD-HHMMSS.json`。
6. 运行 `python agent/validate_research_run.py research_runs/<run_id>.json`：结构 + 14 天窗口 + 6 维加总 = score + HTTP 死链检查。校验失败自动拦。
7. validate 失败：修正或丢弃不合格条目，**不许凑数**。找不到官方 URL 就丢，大厂不足就少收。
8. publish 前主 agent 抽检 `is_major_vendor_official=true` 条目：fetch 每个 URL，对比页面内容 vs 标题摘要。URL 能开 ≠ 内容对题，对不上就丢。
9. 运行 `python agent/publish_results.py research_runs/<run_id>.json --server <SERVER_URL>`。
10. 服务器 upsert，`GET /api/papers` 刷新最新 run。
11. （可选）起整理 agent，**prompt 必须注入 `docs/agent-guide/detail-prompt.md` 全文**，**逐篇整理 + 即时 POST `/api/paper-detail`**（动态增量推送）：每整理完一篇的 6 段 detail（研究背景与问题 / 贡献点 / 实现方法 / 实验与结果 / 对端侧 agent 的意义 / 局限与未来），立即 POST，不等全部整理完。publish 后详情页先显示「整理中」，每篇 POST 完页面实时从「整理中」变成 6 段内容。
12. 更新 `data/.last_run` 时间戳为本次调研时间（ISO 8601，如 `2026-06-26T15:00:00+08:00`）。
13. 本周错误沉淀：进 AGENTS 已知教训 + `docs/agent-guide/validation-rules.md` 规则 + `docs/agent-guide/research-prompt.md` 强化。不靠对话记忆，靠 repo。
14. 跑 `python tests/test_research_pipeline.py`、`python tests/test_build.py`、`python app/gates/gate_all.py` 确认 harness 健康。

## 调研策略（核心）

这是让调研子 agent 在搜索时必须注意的策略：

- **优先级（高→低）**：
  1. 大厂官方动态（Apple/Google/Microsoft/OpenAI/Anthropic/Meta/Samsung/Huawei/Qualcomm/MediaTek/小米/OPPO/vivo/荣耀/Alibaba-Qwen/Mistral/面壁，官方博客/产品发布，`is_major_vendor_official: true`，排序最前）
  2. **公司项目**（快手/字节/腾讯/百度/美团/京东/拼多多/网易等公司独立或主导的研究，arXiv 或顶会，affiliation 命中公司）。优先级非常高，排序仅低于大厂官方。
  3. **公司+学校合作顶会项目**（公司联合高校发表顶会）
  4. **学校顶会项目**（高校独立发表顶会顶刊）
- **至少顶会门槛**：学校项目（无公司 affiliation）必须发表在顶会顶刊（NeurIPS / ICML / ICLR / MobiSys / SenSys / ASPLOS / ACL / CVPR / ICCV / EMNLP / AAAI / IJCAI / TPAMI / TNNLS / ToN）。学校项目的纯 arXiv 预印本（非顶会）不收。公司项目 arXiv 或顶会均可。
- **排除常见方法无明显创新**：纯前缀缓存+投机解码堆砌、普通量化/剪枝、常规 benchmark，除非有显著新意，否则不收。即使中了顶会也不要，或给低分。
- **评分口径**（6 维，质量判断由调研 agent 给分，不是代码硬排）：
  - `score_vendor`（0-25）：大厂官方 20-25；公司项目 15-20；公司+学校合作顶会 10-15；学校顶会 5-10；纯学术无公司 3-8
  - `score_contribution`（0-15）：创新度高 12-15；常见方法/工程整合 5-10
  - `score_open`（0-10）：有开源仓库/数据集/模型开源 5-10；不开源 0
  - 6 维上限：`score_relevance`(30) + `score_vendor`(25) + `score_contribution`(15) + `score_quality`(15) + `score_recency`(5) + `score_open`(10) = 100，`score` = 6 维加总
- **vendors 字段**：公司项目必填公司名（如 `Kuaishou` / `ByteDance` / `Tencent` / `Baidu` / `Meituan` / `JD` / `Pinduoduo` / `Netease`）。
- **官方域名硬约束**：非论文条目必须命中官方域名（见 `docs/references/vendor-whitelist.md`），非官方博客、新闻、GitHub release、社媒、二手解读一律排除。
- **三方向分类**：每条必须归 `应用` / `框架` / `算法` 之一，页面按这三个 tab 分组展示。
- **首页字段人类可读**：`abstract`/`effects`/`mechanism` 用中文短句给人看（这是什么/有什么结果/怎么做到的），详细技术分解放 wiki，不塞首页。
- **keywords 必填**：每条 1-8 个中文优先关键词（如 `GUI智能体`/`记忆`/`工具调用`），页面用小框标签展示。
- **arXiv MCP 搜索**：调研 agent 搜索论文优先用 arXiv MCP 工具（`search_papers`/`download_paper`/`read_paper`），比 websearch 更精准。配置见 `~/.config/opencode/opencode.json` 的 `mcp.arxiv`。websearch 作为补充搜大厂官网。
- **HuggingFace Daily Papers MCP**：调研 agent 用 HF Daily Papers MCP（`get_today_papers`/`get_papers_by_date`）获取社区精选热门论文，和 arXiv MCP 互补。配置见 `~/.config/opencode/opencode.json` 的 `mcp.huggingface`。

## 不可违反

- 服务器不负责搜索论文；搜索由 agent 使用自己的搜索、浏览、阅读工具完成。
- 大厂官方技术博客 / 官方产品发布可收录且排序最前，但必须命中官方域名且 `is_major_vendor_official: true`；非官方博客、新闻、GitHub release、社媒、二手解读一律排除。
- 时间窗口是当前日期过去 14 天，不允许用旧 `.last_run` 放行过期样例。
- 没有本周合格论文时显示空状态，不拿旧数据撑数量。
- 凑数禁令：本周大厂官方不足就少收，不拿学术充大厂，不拿不确定链接凑数。
- `paper_url` 必须和论文标题、摘要匹配。
- `effects` 必须来自论文原文；没有报告写 `未报告`。
- 发布前必须跑 `validate_research_run.py`。
- 修改完成前至少跑 `python tests/test_research_pipeline.py`、`python tests/test_build.py`、`python app/gates/gate_all.py`。

## 已知教训

- [2026-06-25] 非官方博客/产品发布冒充论文会污染页面 → 只允许大厂官方技术博客/官方产品发布（官方域名 + `is_major_vendor_official: true`），其余非论文一律排除；普通论文仍要求 `source_type: 学术论文` + 权威论文链接。
- [2026-06-25] 2025 年旧样例被展示成当前周报 → 时间窗口必须按当前日期过去 14 天硬校验，不能靠旧 `.last_run` 放行。
- [2026-06-25] GitHub 静态页不是最终形态 → 最终展示由服务器 `GET /api/papers` 刷新；GitHub Pages 只保留 fallback。
- [2026-06-25] 子 agent 和页面职责混淆 → 子 agent 只产出 research run JSON，主 agent 校验并发布，服务器只接收和展示。
- [2026-06-25] 新 codeagent 只读散落文档容易漏流程 → 项目内 `.agents/skills/edge-agent-research-pipeline/SKILL.md` 是强入口，AGENTS 必须指向它。
- [2026-06-26] 主 agent 绕过 research-prompt.md 自写简化 prompt → 子 agent 没守标准 → 编造 404 链接。修复：发起子 agent 时 prompt 必须注入 research-prompt.md 全文，不许自写简化版。
- [2026-06-26] 本周大厂官方内容稀疏时凑数，拿不确定链接充数。修复：找不到官方 URL 就丢弃，大厂不足就少收，不凑数。
- [2026-06-26] 整理 agent 产出的 detail 含英文双引号会破坏 JSON 编码 → `docs/agent-guide/detail-prompt.md` 硬约束第 5 条：整段 detail 不许出现 `"` 字符，用「」或不加引号。
- [2026-06-26] 调研 agent 标注 vendors/affiliation 只凭作者名推测，没附证据来源 → 用户质疑。修复：vendors/affiliation 标注必须有证据来源（OpenReview profile / Google Scholar / 论文 PDF 作者机构页），score_reason 里写明 affiliation 依据（如「Zhixiang Chi OpenReview profile 显示 Huawei Technologies Ltd，huawei.com 邮箱确认」），不许只凭名字猜。
- [2026-06-26] 整理 agent 等全部整理完才统一推送 → 页面长时间停在「整理中」。修复：改成逐篇整理 + 即时 POST `/api/paper-detail`（动态增量推送），每篇整理完立即推送，页面实时刷新，不用等全部完成。`docs/agent-guide/detail-prompt.md` 输出方式已改。
