# edge_agent 持续调研 Harness

> 本文件是项目持续运作的总览。新 codeagent 先读 `AGENTS.md` → 本文件 → `SKILL.md`。

## 1. 目标

端侧 AI Agent 论文雷达：**每周调研一次**含运行日的最近 7 个自然日端侧 AI 与相关技术栈论文 + 24 个规范厂商/模型实验室官方动态，校验后发布。完整收录尽量广，推荐层负责用户优先阅读内容。

## 2. 整体架构

```
调度(data/.last_run时间戳 + AGENTS节奏)
  → 主agent读AGENTS/SKILL/research-prompt(强入口)
  → 发起调研子agent(prompt必须注入research-prompt.md全文+硬约束)
  → 子agent产出四类候选 + research_runs/collection-manifest.json
  → 主agent广收录筛选并产出 research_runs/run-<week>.json
  → validate: 覆盖清单+结构+死链+动态7天窗口+2维加总+arXiv date+跨run去重
  → 主agent抽检来源并策展推荐(中文项目名+摘要+为什么值得看；自动脚本不得按关键词推荐)
  → publish → 服务器upsert → 展示最新run(标签筛选)
  → 详情页: 短摘要+标签+原文链接(无6段整理,整理agent已停用)
  → 错误沉淀: AGENTS教训+validate规则+research-prompt强化
  → 跑测试套件确认harness健康
```

## 3. 每周调研主循环

| 步 | 动作 | 自动/人工 |
|---|---|---|
| 1 | 主 agent 读 AGENTS/SKILL/research-prompt/output-contract/validation-rules | 强入口 |
| 2 | 检查 `data/.last_run`，距上次 ≥7 天才跑 | 自动 gate |
| 3 | 发起调研子 agent，**prompt 必须注入 research-prompt.md 全文 + 硬约束**（不许自写简化版） | 流程强制 |
| 4 | 子 agent 用 MCP+websearch 广搜本周论文+厂商官方+开源大项目。普通但相关的量化/剪枝/缓存/benchmark/serving 低分保留；完全无关才删；自动条目统一 `纳入` | agent |
| 5 | 完成 `research_runs/collection-manifest.json`：动态7日、arXiv分页自然终止、HF逐日、GitHub release/trending分离、24厂商/模型实验室逐一留下成功来源证据；运行 `agent/attest_candidates.py` 绑定四候选文件路径/条数/文件 SHA-256/逐记录指纹/稳定 title+URL+来源日期身份，并核对每条 run 的唯一 candidate_source + candidate_ref | **自动拦** |
| 6 | 主 agent 完成最终筛选、评分、标签、中文整理和 affiliation 证据核实，保存 `research_runs/run-YYYYMMDD-HHMMSS.json` | 主 agent |
| 7 | 主 agent 逐条完成`edge_agent_scope`分类；真正端侧 Agent 必须补设备端闭环证据并全部推荐（手机 > PC > 其他端侧），再从其余完整收录中挑普通推荐 | 主 agent + 自动拦 |
| 8 | `python agent/validate_research_run.py`：先验覆盖清单，再验内容、动态7日、评分、标签、链接、arXiv date 和去重 | **自动拦** |
| 9 | validate 失败：修正或丢弃，**不许凑数** | 流程 |
| 10 | 主 agent 抽检 `source_tier=官方动态` 和 `开源大项目` 条目：fetch URL 对比页面内容 vs 标题摘要 | 半自动 |
| 11 | 独立检索 X / Bluesky / Reddit / Hacker News / Mastodon / GitHub Discussions / Hugging Face / YouTube-Bilibili / 厂商论坛，写 `data/community_radar.json`；九来源逐项留覆盖状态，社媒链接不进入正式 run | 主 agent + 自动拦 |
| 12 | `python agent/publish_results.py --server <URL>` | 主 agent |
| 13 | 服务器 upsert，`GET /api/papers` 刷新最新 run；`GET /api/community` 返回独立社区层 | 自动 |
| 14 | 详情页展示短摘要 + tags + 原文链接（整理 agent 已停用，无 6 段 detail，无「整理中」状态） | 自动 |
| 15 | publish 后列表页、社区雷达和详情页立即可见；推荐区按手机端 Agent > PC 端 Agent > 其他端侧 Agent > 普通推荐，再按 source_tier + score 排序 | 自动 |
| 16 | 更新 `data/.last_run` 时间戳 | 主 agent |
| 17 | 本周错误 → AGENTS 教训 + validate 规则 + research-prompt 强化 | 自进化 |
| 18 | 跑 `tests/` + `app/gates/gate_all.py` 确认 harness 健康 | 自动 |

## 4. 持久展示层

- 服务器持续跑 `app/server.py`（本地 systemd/PM2 或远端部署）
- `GET /api/papers` 只返回最新 run（`storage.list_papers` 按 `received_at DESC` 取最新 run_id）
- **标签筛选**：`app/page.py` 按标签 chip 多选筛选展示。`方向:端侧agent`只表示经原文核实的真正设备端 Agent 闭环；推荐排序先按`edge_agent_scope`（手机>PC>其他端侧>非端侧Agent），再按 source_tier + score。
- **详情页** `/paper/<id>`：展示短摘要（abstract/effects/mechanism）+ tags + 原文链接，无 6 段深度整理（整理 agent 已停用）
- **静态 fallback** `app/build.py` 生成 `site/index.html`，服务器挂时兜底
- **社区雷达**：`data/community_radar.json` 独立于 research run；页面顺序为完整资料库 → 社区雷达 → GitHub 待核验线索。社区按手机 > PC > 其他端侧 > 通用技术排序，并随周归档冻结。
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
- **渲染验证**（每次 publish/deploy 后必做，不只 curl+tests）：用 chrome-devtools 加载线上页（profile 被锁就 `taskkill //F //IM chrome.exe` 杀掉重连），`ignoreCache` 硬刷新，三查：(1) DOM 渲染对——`#recommendations .rec-item`、`#papers .signal-row`、`#community-list .community-item` 数、band 折叠态、标签栏、weekly/trending 渲染条数；(2) 读内容质量——推荐卡严格按中文项目名 → 介绍 → 关键词 → 为什么值得看 → 小号英文原标题展示，不能把介绍冒充项目名；社区来源覆盖、X 受限状态、中文总结/判断与核验状态可读，社区筛选不改变正式列表；weekly 的 topic/why、论文中文摘要真的看内容不是数条数；(3) `list_console_messages` 查 error/404。curl 对 ≠ 渲染对，tests 过 ≠ 页面好。

## 6. 调度

agent 项目现实：调研要 LLM agent 搜索，cron/CI 跑 agent runtime 复杂。不强承诺全自动。

- **主触发**：人/主 agent 每周启动一次跑主循环。AGENTS.md 写明节奏
- **防重复/过期**：`data/.last_run` 记上次调研时间。启动时检查 ≥7 天才跑；<7 天提示"本周已调研"
- **CI 接口（未来）**：留 `agent/research_run.py` 可被脚本调用的接口，未来 GitHub Actions 定时触发（需配 LLM API）。当前不实现，文档留接口

## 7. 角色边界（不可违反）

- **主 agent（codeagent）**：读文档、发起子 agent、validate、抽检、publish、沉淀错误。不自己写调研 prompt（必须用 research-prompt.md）
- **调研子 agent**：用 research-prompt 搜索，只产出 run JSON。不改代码/服务器/页面
- **整理子 agent**：已停用（方案 B）。详情页改短摘要+tags+原文链接，不再产 6 段 detail
- **服务器**：只接收校验过的 run，存储展示。**不搜索论文**
- **凑数禁令**：本周大厂官方不足就少收，不拿学术充大厂，不拿不确定链接凑数

## 8. 校验规则

**自动校验**（`agent/research_run.py`，发布前必跑）：
- 必填字段、source_tier 枚举、tags 词表（data/tags.yaml）、date 7 天窗口、score=2维之和、候选记录血缘、`source_tier=官方动态` 必须官方域名、`source_tier=开源大项目` 必须 github.com URL、`source_tier=公司项目` 必须有 vendors + 权威 affiliation_evidence_url（GitHub 不算）
- **死链检查**：每个 paper_url 发 HTTP HEAD，HEAD 失败 fallback GET；超时/网络不可达记 alive + warning 不 fail；只有 404 才 fail；每 URL 超时 5s
- **arXiv date 与更新稿核对**：按 `arxiv_date_basis` 查真实提交日/更新日；旧稿走 `updated` 时还必须有主 agent 版本对比后的中文 `arxiv_revision_note`，无实质变化即丢，防止排版修订冒充本周动态
- **跨 run 去重**：读 data/.last_run_papers.json，命中上次 run 的 id 给 warning（不 fail，相邻两周窗口有合法重叠）
- **推荐可读性**：每条 abstract 至少 8 个中文字符；推荐条目必须有 2 个以上中文字符且不超过 40 字的 `title_zh`（不得等于 abstract）以及至少 8 个中文字符的 recommendation_reason；读者字段含 auto-converted/votes=/待核实/精修待补等内部占位词直接 fail
- **构建发布门**：当前周非空时至少 1 条人工精选，自动汇集不能按关键词晋升推荐；gate_release 在真实 `site/index.html` 上复核
- **端侧 Agent 发布门**：自动汇集写`待核实`且不能自动加`方向:端侧agent`；发布前逐条分类。手机/PC/其他端侧必须有中文闭环证据、相关分≥8并全部推荐；字段、标签、推荐任一不一致即 fail。

**半自动抽检**（主 agent publish 前对官方动态/开源大项目条目）：
- fetch 每个 `source_tier=官方动态` 和 `source_tier=开源大项目` 的 URL，核验页面内容与标题摘要对应（URL 能开 ≠ 内容对题）
- 可用 `agent/verify_links.py` 辅助（fetch 大厂 URL 返回页面摘要供核验）

## 9. 数据管理

- `research_runs/run-<YYYYMMDD-HHMMSS>.json`：每周一个，累积审计（git 不提交）
- `app/papers.sqlite`：papers 表累积（id 为 PK，upsert 覆盖）；research_runs 表记 run 元数据
- `list_papers` 只取最新 run
- `data/.last_run`：上次调研时间戳（调度 gate）
- `data/index.json` / `data/vendors.yaml`：共享数据

## 10. 已知局限（诚实承认）

1. 调度非全自动：靠人每周触发 + 时间戳防重复。CI 自动化留接口未来做
2. 中文字符数、推荐理由存在性和内部占位词已能机械拦截；「摘要是否真正说清楚」「推荐是否真的值得看」「不凑数」仍需主 agent 阅读来源和页面抽检
3. 内容匹配抽检半自动：URL 能开 ≠ 内容对题，靠主 agent fetch 抽检
4. 死链检查误判风险：某些站对 bot 返 403。HEAD fallback GET + 官方域名白名单降低误判，离线时 warning 跳过

## 11. 分层调研系统设计

调研不是一次性全交给子 agent，而是分 4 层：大量搜集 → 主 agent 筛选 → 主 agent 评分 → 自动发布。

### 流程总览

```
第一层 子agent(广搜+覆盖证据) 第二层 主agent(硬边界筛选)   第三层 主agent(评分推荐)   第四层 自动(发布)
┌─────────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ arXiv 大类+关键词分页│     │ 1.动态7日窗口    │     │ 2维最终评分       │     │ validate(覆盖+   │
│ HF Daily 7天×20    │ ─→ │ 2.关键词粗筛      │ ─→ │ vendors附证据     │ ─→ │ arXiv date+      │
│ GitHub trending+    │     │ 3.过滤GUI agent   │     │ abstract/effects  │     │ 7天+2维+tags)   │
│ release + trending  │     │ 4.相关低贡献保留  │     │ /mechanism重写    │     │ publish          │
│ 24厂/实验室逐一检查 │     │ 5.affiliation证据 │     │ 推荐人工策展      │     │ hook自动gh-pages │
└─────────────────────┘     │ 6.死链检查        │     │ tags+source_tier  │     │ 列表+详情        │
                            │ 7.去重            │     └──────────────────┘     └──────────────────┘
        尽量广搜集          └──────────────────┘              全量发布
                                    筛后候选
```

### 第一层：大量搜集（子 agent，用 MCP 工具，尽量广搜集，不设硬目标）

**三个 MCP 数据源**：

#### arXiv MCP（`arxiv-mcp-server`，工具 `search_papers`）
- 全量结构化搜索 arXiv，比 websearch 搜 arXiv 精准 10 倍
- 9 个大类全扫 + 多轮关键词搜索；每轮按 100 条分页，直到越过窗口下界或无下一页：
  1. `"on-device agent"` — 核心词
  2. `"edge computing agent"` — 边缘计算
  3. `"mobile LLM inference"` — 端侧推理
  4. `"NPU agent"` — NPU 加速
  5. `"agent memory edge"` — 端侧记忆
  6. `"tool use edge device"` — 工具调用
  7. `"federated agent"` — 联邦 agent
  8. `"quantization agent mobile"` — 量化+agent
- 大类至少覆盖 `cs.AI/cs.LG/cs.CL/cs.RO/cs.AR/cs.DC/cs.ET/cs.SY/cs.NE`；窗口由 `research_collection.py` 动态计算为含运行日的 7 个自然日
- **自适应**：某 query 返回过少就放宽/换词（去引号、换同义词、扩 category），不死守固定 query
- 结果：去重后约 200-300（视窗口内实际产出，不设硬目标）

#### HuggingFace Daily Papers MCP（`huggingface-daily-paper-mcp`，工具 `get_papers_by_date`）
- 社区投票精选热门论文，质量比 arXiv 全量高
- 过去 7 天每天调一次 `get_papers_by_date(date=YYYY-MM-DD)`
- 每天 ~20 篇，7 天 = ~140 候选
- votes 只影响候选浏览顺序，不作为删除门槛；7 个日期必须全部写入 coverage manifest
- 和 arXiv MCP 互补：HF 精选（质量高覆盖窄）+ arXiv 全量（覆盖广噪音多）

#### GitHub MCP（搜 trending repos + 最新 release，端侧优先）
- 搜 trending：`edge agent / on-device LLM / mobile AI / NPU` 相关 repos
- 搜 release：**端侧优先** ExecuTorch / llama.cpp / MLC-LLM / Google ADK / nanoagent；vLLM / SGLang / TensorRT 等通用框架次要（有端侧相关更新才收）
- 筛选：在 `big-projects-whitelist.md` 白名单内 + 最近 7 天有 release + 主题相关
- 结果：5-10 个开源框架/项目更新

**厂商与模型实验室官方来源（24 个规范来源）**
- 规范集合由 `agent/research_collection.py::REQUIRED_VENDOR_SOURCES` 定义，具体官方 URL 和查法见 `vendor-research-guide.md`
- 逐一 fetch/websearch/browser 检查动态；JS/403 站点必须换浏览器或搜索兜底，不能因静态抓取失败就当成已无更新
- 结果：10-20 条大厂官方动态

**第一层汇总**：arXiv + HF + GitHub + 大厂 blog 去重后视窗口内实际产出，不设硬数量目标（列表轻量罗列，可以多收）。

### 第二层：主 agent 筛选（不交给子 agent）

主 agent 拿到候选后，亲自筛选：
1. **日期过滤**：保留过去 7 天
2. **主题粗筛**：明确端侧必收；与 AI 推理/部署有直接迁移价值的相邻工作保留并低分；完全无关才删
3. **过滤 GUI agent**：纯 GUI 操作类（屏幕点击/GUI自动化）→ 删，除非非 GUI 创新
4. **相关低贡献内容保留**：普通量化/剪枝/缓存/benchmark/serving 只要与 AI 推理部署相关就低分保留，完全无关才删
5. **affiliation 粗筛**：
   - 论文明确 affiliation/机构字段及一手证据命中快手/字节/腾讯/百度等 → 标记公司项目
   - 任何正规大学（清华/北大/上交/浙大/MIT/Stanford/CMU/Berkeley 等，不限中美名校）→ 标记学校项目（顶会→学校顶会，arXiv预印本→学校预印本）
   - 标题、摘要或模型名命中公司不算 affiliation；无证据先标学校预印本
6. **死链检查**：HTTP HEAD/GET 验证 URL 可访问
7. **去重**（含跨 run）

结果：筛后候选（不设硬目标，合格都留）

### 第三层：主 agent 评分（不交给子 agent）

主 agent 对筛后候选逐篇评分：
- 2 维评分（relevance 0-10 + contribution 0-10 = score 0-20）
- source_tier（官方动态/开源大项目/公司项目/学校顶会/学校预印本）+ open_source bool
- tags 1-8 个（取自 data/tags.yaml 词表，多标签）
- vendors 附证据（OpenReview/Google Scholar/arXiv PDF 机构页）
- abstract/effects/mechanism 用大白话中文重写（轻量，1-2 句，不写详细分析）
- 自动汇集的 recommendation 一律为纳入且 `title_zh` 留空；逐篇读来源后再选推荐，并写简短中文项目名和中文 recommendation_reason
- 2 维加总 = score

结果：全量发布为 research run JSON（有多少收多少，不凑数也不设上限）

### 第四层：自动发布（无整理 agent）

1. validate（2维+死链+arXiv date+7天窗口+tags）+ publish（hook 自动 gh-pages 列表+详情）
2. 整理 agent 已停用（方案 B）：详情页展示短摘要+tags+原文链接，无 6 段 detail

### 关键设计原则

- **主 agent 参与筛选+评分**：不全交给子 agent，质量可控
- **子 agent 做广搜和覆盖留痕**：搜集追求召回率；最终筛选、评分、打标和推荐由主 agent 亲自做
- **三个 MCP 互补**：arXiv 全量 + HF 精选 + GitHub 开源动态（配置见 `docs/references/mcp-setup.md`，项目级 `.mcp.json`）
- **量大**：尽量广搜集 → 筛后全量发布（不设硬目标，可以多收），不是从 6-9 篇里选
