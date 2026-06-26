# edge_agent 持续调研 Harness

> 本文件是项目持续运作的总览。新 codeagent 先读 `AGENTS.md` → 本文件 → `SKILL.md`。

## 1. 目标

端侧 AI Agent 论文雷达：**每周调研一次**本周（过去 7 天）端侧 agent 论文 + 17 家大厂官方动态，校验后发布，网页持久展示最新结果。Harness 保证循环持续正确运作 + 自进化（错误沉淀，下次自动拦），不靠对话记忆。

## 2. 整体架构

```
调度(data/.last_run时间戳 + AGENTS节奏)
  → 主agent读AGENTS/SKILL/research-prompt(强入口)
  → 发起调研子agent(prompt必须注入research-prompt.md全文+硬约束)
  → 子agent产出 research_runs/run-<week>.json
  → validate: 结构+死链(自动拦)+7天窗口+5维加总
  → 主agent抽检大厂条目内容匹配(fetch URL对比标题摘要)
  → publish → 服务器upsert → 展示最新run(论文/博客tab)
  → (可选)起整理agent(注入detail-prompt.md)产6段detail → POST /api/paper-detail → 详情页刷新
  → 错误沉淀: AGENTS教训+validate规则+research-prompt强化
  → 跑测试套件确认harness健康
```

## 3. 每周调研主循环

| 步 | 动作 | 自动/人工 |
|---|---|---|
| 1 | 主 agent 读 AGENTS/SKILL/research-prompt/output-contract/validation-rules | 强入口 |
| 2 | 检查 `data/.last_run`，距上次 ≥7 天才跑 | 自动 gate |
| 3 | 发起调研子 agent，**prompt 必须注入 research-prompt.md 全文 + 硬约束**（不许自写简化版） | 流程强制 |
| 4 | 子 agent 搜索本周论文+大厂官方，产出易读版 abstract/effects/mechanism + 5维 + keywords + category + source_type + vendors | agent |
| 5 | 保存 `research_runs/run-YYYYMMDD-HHMMSS.json` | 主 agent |
| 6 | `python agent/validate_research_run.py`：结构 + 7天窗口 + 5维加总=score + **HTTP 死链检查** | **自动拦** |
| 7 | validate 失败：修正或丢弃，**不许凑数** | 流程 |
| 8 | 主 agent 抽检 `is_major_vendor_official=true` 条目：fetch URL 对比页面内容 vs 标题摘要 | 半自动 |
| 9 | `python agent/publish_results.py --server <URL>` | 主 agent |
| 10 | 服务器 upsert，`GET /api/papers` 刷新最新 run | 自动 |
| 11 | （可选）起整理 agent，**prompt 必须注入 `docs/agent-guide/detail-prompt.md` 全文**，为每篇论文产 6 段 detail（研究背景与问题 / 贡献点 / 实现方法 / 实验与结果 / 对端侧 agent 的意义 / 局限与未来），逐条 `POST /api/paper-detail` 写入 DB | 主 agent |
| 12 | 异步说明：publish 后列表页立即可见，详情页先显示「整理中」；整理 agent 完成后详情页刷新出 6 段内容 | 自动 |
| 13 | 更新 `data/.last_run` 时间戳 | 主 agent |
| 14 | 本周错误 → AGENTS 教训 + validate 规则 + research-prompt 强化 | 自进化 |
| 15 | 跑 `tests/` + `app/gates/gate_all.py` 确认 harness 健康 | 自动 |

## 4. 持久展示层

- 服务器持续跑 `app/server.py`（本地 systemd/PM2 或远端部署）
- `GET /api/papers` 只返回最新 run（`storage.list_papers` 按 `received_at DESC` 取最新 run_id）
- **论文/博客 tab**：`app/page.py` 按 `source_type` 分两 tab——学术论文 / 官方动态（官方技术博客+官方产品发布合并）。tab 内大厂官方按 `is_major_vendor_official DESC` 排前
- **详情页** `/paper/<id>`：展示深度整理 `detail` + 原文链接
- **静态 fallback** `app/build.py` 生成 `site/index.html`，服务器挂时兜底
- **空状态**：本周无合格内容显示空，不拿旧数据撑

## 5. 自进化闭环

错误不靠记忆，三层沉淀 + 闭环验证：

| 层 | 沉淀点 | 生效方式 |
|---|---|---|
| 代码层 | `agent/research_run.py` validate 规则 | 下次 validate 自动跑 |
| 流程层 | AGENTS.md 工作流硬步骤 + 不可违反 + 教训段 | codeagent 读到必须做 |
| 策略层 | research-prompt.md / output-contract.md / validation-rules.md | 子 agent 用，约束产出 |

**闭环验证（分层）**：
- **快验证**（每次改 harness 后）：跑 `tests/test_research_pipeline.py` + `test_build` + `app/gates/gate_all.py`，确认代码层规则生效
- **慢验证**（新策略上线时）：跑一次真调研，确认死链拦、research-prompt 用、易读版产出、不凑数

## 6. 调度

agent 项目现实：调研要 LLM agent 搜索，cron/CI 跑 agent runtime 复杂。不强承诺全自动。

- **主触发**：人/主 agent 每周启动一次跑主循环。AGENTS.md 写明节奏
- **防重复/过期**：`data/.last_run` 记上次调研时间。启动时检查 ≥7 天才跑；<7 天提示"本周已调研"
- **CI 接口（未来）**：留 `agent/research_run.py` 可被脚本调用的接口，未来 GitHub Actions 定时触发（需配 LLM API）。当前不实现，文档留接口

## 7. 角色边界（不可违反）

- **主 agent（codeagent）**：读文档、发起子 agent、validate、抽检、publish、沉淀错误。不自己写调研 prompt（必须用 research-prompt.md）
- **调研子 agent**：用 research-prompt 搜索，只产出 run JSON。不改代码/服务器/页面
- **整理子 agent（可选）**：为 paper 产 `detail` 6 段深度整理。prompt 必须注入 `docs/agent-guide/detail-prompt.md` 全文。可选，非每周必跑
- **服务器**：只接收校验过的 run，存储展示。**不搜索论文**
- **凑数禁令**：本周大厂官方不足就少收，不拿学术充大厂，不拿不确定链接凑数

## 8. 校验规则

**自动校验**（`agent/research_run.py`，发布前必跑）：
- 必填字段、source_type/category 枚举、date 7 天窗口、score=5维之和、官方源必须 is_major_vendor_official=true + 官方域名白名单、keywords 1-8 中文
- **死链检查**：每个 paper_url 发 HTTP HEAD，404/不可达 fail；HEAD 不支持 fallback GET 取状态码；每 URL 超时 5s；**离线/断网 warning 跳过**（不 fail，标记"死链未检"）

**半自动抽检**（主 agent publish 前对大厂条目）：
- fetch 每个 `is_major_vendor_official=true` 的 URL，核验页面内容与标题摘要对应（URL 能开 ≠ 内容对题）
- 可用 `agent/verify_links.py` 辅助（fetch 大厂 URL 返回页面摘要供核验）

## 9. 数据管理

- `research_runs/run-<YYYYMMDD-HHMMSS>.json`：每周一个，累积审计（git 不提交）
- `app/papers.sqlite`：papers 表累积（id 为 PK，upsert 覆盖）；research_runs 表记 run 元数据
- `list_papers` 只取最新 run
- `data/.last_run`：上次调研时间戳（调度 gate）
- `data/index.json` / `data/vendors.yaml`：共享数据

## 10. 已知局限（诚实承认）

1. 调度非全自动：靠人每周触发 + 时间戳防重复。CI 自动化留接口未来做
2. "大白话整理""不凑数"是软约束：没法 100% 自动校验。死链拦假 URL，拦不住"真 URL 弱相关充大厂"——靠 research-prompt + 教训 + 内容抽检兜
3. 内容匹配抽检半自动：URL 能开 ≠ 内容对题，靠主 agent fetch 抽检
4. 死链检查误判风险：某些站对 bot 返 403。HEAD fallback GET + 官方域名白名单降低误判，离线时 warning 跳过
