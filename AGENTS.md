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

端侧 AI Agent 论文雷达：主 code agent 调度调研子 agent 搜索最近一周端侧 agent 相关论文，主 agent 校验后把结构化结果发布到服务器，网页从服务器刷新最新论文列表。

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
3. 发起调研子 agent。**prompt 必须注入 `docs/agent-guide/research-prompt.md` 全文 + 硬约束**（B 档边界、官方域名白名单、7 天窗口、多标签 tags、source_tier、不凑数）。**不许主 agent 自写简化版 prompt**，简化版会让子 agent 漏掉标准，编造断链。
4. 子 agent 用 arXiv MCP + HF Daily Papers MCP + GitHub MCP + websearch 广搜集本周（过去 7 天）端侧 agent 论文 + 18 家大厂官方动态 + 开源大项目 release，产出易读版 `abstract`/`effects`/`mechanism` + 2 维打分 + `tags` + `source_tier` + `open_source` + `vendors`。arXiv date 取自元数据。子 agent 只输出结构化 JSON，不改代码、网页、服务器。
5. 主 agent 保存为 `research_runs/run-YYYYMMDD-HHMMSS.json`。自动汇集的条目必须全部保持 `title_zh=""`、`recommendation=纳入`；主 agent 读过来源后再挑选本周值得优先看的条目，填写简短中文项目名 `title_zh` 和具体中文 `recommendation_reason`，推荐数量按实际质量决定。
6. 运行 `python agent/validate_research_run.py research_runs/<run_id>.json`：中文项目名/摘要/推荐理由 + 内部占位词 + 结构 + 7 天窗口 + 2 维加总 = score + source_tier/tags 校验 + HTTP 死链检查 + arXiv date 核对 + 跨 run 去重 warning。校验失败自动拦。
7. validate 失败：修正或丢弃不合格条目，**不许凑数**。找不到官方 URL 就丢，大厂不足就少收。
8. publish 前主 agent 抽检 `source_tier=官方动态` 和 `source_tier=开源大项目` 条目：fetch 每个 URL，对比页面内容 vs 标题摘要。URL 能开 ≠ 内容对题，对不上就丢。
9. 运行 `python agent/publish_results.py research_runs/<run_id>.json --server <SERVER_URL>`。
10. 服务器 upsert，`GET /api/papers` 刷新最新 run。
11. 详情页展示短摘要 + tags + 原文链接（不再有 6 段深度整理；整理 agent 已停用，`detail-prompt.md` 已删）。publish 后列表页和详情页立即可见。
12. 更新 `data/.last_run` 时间戳为本次调研时间（ISO 8601，如 `2026-06-26T15:00:00+08:00`）。
13. 本周错误沉淀：进 AGENTS 已知教训 + `docs/agent-guide/validation-rules.md` 规则 + `docs/agent-guide/research-prompt.md` 强化。不靠对话记忆，靠 repo。
14. 跑 `python tests/test_research_pipeline.py`、`python tests/test_build.py`、`python app/gates/gate_all.py` 确认 harness 健康。

## 调研策略（核心）

这是让调研子 agent 在搜索时必须注意的策略：

- **分层调研系统**：调研分 4 层（MCP大量搜集 → 主agent筛选 → 主agent评分 → 自动发布），详见 `docs/harness.md` 分层调研系统设计。三个 MCP 数据源：arXiv MCP（全量搜）/ HF Daily Papers MCP（社区精选）/ GitHub MCP（开源动态，端侧优先）。主 agent 亲自筛选+评分，不全交给子 agent。不设硬数量目标，有多少合格收多少。

- **优先级（高→低）**：
  1. 大厂官方动态（Apple/Google/Microsoft/OpenAI/Anthropic/Meta/NVIDIA/Samsung/Huawei/Qualcomm/MediaTek/小米/OPPO/vivo/荣耀/Alibaba-Qwen/Mistral/面壁，官方博客/产品发布，`source_tier=官方动态`，命中官方域名，排序最前）
  2. **公司项目**（快手/字节/腾讯/百度/美团/京东/拼多多/网易等公司独立或主导的研究，arXiv 或顶会，affiliation 命中公司）。优先级非常高，排序仅低于大厂官方。
  3. **公司+学校合作顶会项目**（公司联合高校发表顶会）
  4. **学校顶会项目**（高校独立发表顶会顶刊）
- **学校项目门槛**：`学校顶会` 必须发表在顶会顶刊（NeurIPS/ICML/ICLR/MobiSys/SenSys/ASPLOS/ACL/CVPR/ICCV/EMNLP/AAAI/IJCAI/TPAMI/TNNLS/ToN）+ 任何正规大学（不再卡中美名校）。任何大学的 arXiv 预印本（非顶会但强相关）收为 `学校预印本`。公司项目 arXiv 或顶会均可。
- **排除常见方法无明显创新**：纯前缀缓存+投机解码堆砌、普通量化/剪枝、常规 benchmark，除非有显著新意，否则不收。即使中了顶会也不要，或给低分。
- **评分口径**（2 维，质量判断由调研 agent 给分，不是代码硬排）：
  - `score_relevance`（0-10）：明确端侧部署 8-10；可迁移且作者提到端侧场景 4-7；纯云端无端侧考量 0-3 或排除
  - `score_contribution`（0-10）：创新度高 7-10；常见方法/工程整合 3-6
  - `score` = 2 维之和（0-20），排序靠 `source_tier` 优先级 + `score`
- **source_tier**（来源 facet，替代旧 source_type + is_major_vendor_official）：`官方动态`（18 家大厂官方博客/产品发布，含 NVIDIA，命中官方域名，排序最前）/ `开源大项目`（白名单大项目 release，github.com URL）/ `公司项目`（affiliation 命中公司，vendors 必填）/ `学校顶会`（任何大学顶会顶刊）/ `学校预印本`（任何大学 arXiv 预印本，排序最低，保证新鲜端侧工作不漏）
- **open_source**：bool facet（有开源仓库/数据集/模型 true），不打分，同等条件开源优先
- **vendors 字段**：公司项目必填公司名（如 `Kuaishou` / `ByteDance` / `Tencent` / `Baidu` / `Meituan` / `JD` / `Pinduoduo` / `Netease`）。当前 run 的 affiliation 核实 defer：未识别公司的论文一律标 `学校预印本`，公司论文待识别。
- **官方域名硬约束**：非论文条目必须命中官方域名（见 `docs/references/vendor-whitelist.md`），非官方博客、新闻、GitHub release、社媒、二手解读一律排除。
- **多标签 tags**：每条 1-8 个标签，格式 `维度:值`（4 维：方向/应用/硬件/模型，如 `方向:端侧agent`/`硬件:NPU`/`模型:Llama`），取自 `data/tags.yaml` 词表（人读版 `docs/references/tag-taxonomy.md`），多标签，一个工作可挂多个（如「端侧 VLM 量化部署」挂 `方向:端侧agent`+`方向:多模态`+`方向:量化`+`方向:编译部署`）。页面按 4 维 faceted 筛选展示，不是非此即彼。方向/应用/硬件为受控词表，模型为半自由。词表外标签先加进 `data/tags.yaml` 再用。
- **首页字段人类可读**：`abstract`/`effects`/`mechanism` 用中文短句给人看（这是什么/有什么结果/怎么做到的），详细技术分解放 wiki，不塞首页。
- **推荐是主 agent 的编辑判断**：自动脚本和搜集子 agent 只做完整收录，一律 `title_zh=""`、`recommendation=纳入`；不得因为标题命中 on-device/KV cache/量化等关键词自动晋升。主 agent 逐条读来源后决定推荐数量和排序，每条推荐必须有 40 字以内的中文项目名 `title_zh` 和具体中文 `recommendation_reason`。推荐卡按中文项目名 → 中文 `abstract` 介绍 → tags 关键词 → 推荐理由 → 小号英文原标题展示；项目名不得直接复制 abstract。
- **keywords 已并入 tags**：原 keywords 字段取消，统一用 `tags`（受控词表）。
- **MCP 配置**：arXiv MCP / HuggingFace Daily Papers MCP / GitHub MCP 已沉淀为项目级 `.mcp.json`，配置和工具用法见 `docs/references/mcp-setup.md`。调研 agent 搜集优先用 MCP（arXiv 全量搜 / HF 社区精选 / GitHub 大项目 release），websearch 补充搜大厂官网。
- **开源大项目白名单**：GitHub MCP 只收 `docs/references/big-projects-whitelist.md` 内业界认可大项目（vLLM/SGLang/llama.cpp/ExecuTorch/ADK/TensorRT 等），非白名单小仓不收。

## 不可违反

- 服务器不负责搜索论文；搜索由 agent 使用自己的搜索、浏览、阅读工具完成。
- 大厂官方技术博客 / 官方产品发布可收录且排序最前（`source_tier=官方动态`），但必须命中官方域名；开源大项目 release 用 `source_tier=开源大项目` + github.com URL + 白名单（`docs/references/big-projects-whitelist.md`）。非官方博客、新闻、GitHub release、社媒、二手解读一律排除。
- 时间窗口是当前日期过去 7 天，不允许用旧 `.last_run` 放行过期样例。
- 没有本周合格论文时显示空状态，不拿旧数据撑数量。
- 凑数禁令：本周大厂官方不足就少收，不拿学术充大厂，不拿不确定链接凑数。
- `paper_url` 必须和论文标题、摘要匹配。
- `effects` 必须来自论文原文；没有报告写 `未报告`。
- 发布前必须跑 `validate_research_run.py`。
- **发布前必须跑 `python app/gates/gate_all.py`（含 `gate_release.py`）**。`gate_release` 是机械门，作用在构建产物 `site/` + `data/`，拦：__PAPERS__ 契约、推荐中文项目名/摘要/理由缺失或含内部占位词、项目名复用介绍、非空周报 0 推荐、内链 404、热点复读论文列表、0 官方动态静默。**它 FAIL 就不许部署**——比 assertIn 子串测试强，子串测试测不出的功能回归它都能拦。
- `data/weekly_summary.json` 是**独立编辑产物**，不是 run 的派生字段。`highlights` 必须是编辑性新闻（厂商博客/动态/行业事件，带**外部 URL**，≥5 条），不许用 run 的 paper_id 切 top N 填充——那会让热点复读下面的论文列表。流程顺序：先采厂商动态（`官方动态`）→ 再写 weekly_summary（从新闻 + 判断）→ run 论文列表是另一层。
- **0 官方动态是流程告警，不是可接受结果**。research-prompt 强制查 18 厂博客 + 模型实验室博客（DeepSeek/Moonshot/Zhipu/Minimax/百川）。run 里 `官方动态` count==0 时，必须要么去补采，要么在 `data/weeks/<label>-no-vendor.md` 写明逐厂证据（哪厂查了、在窗内是否有端侧文），不许静默接受 0。
- 修改完成前至少跑 `python tests/test_research_pipeline.py`、`python tests/test_build.py`、`python app/gates/gate_all.py`。

## 已知教训

- [2026-06-25] 非官方博客/产品发布冒充论文会污染页面 → 只允许大厂官方技术博客/官方产品发布（`source_tier=官方动态` + 官方域名），其余非论文一律排除；普通论文用 `source_tier=学校顶会/公司项目` + 权威论文链接。
- [2026-06-25] 2025 年旧样例被展示成当前周报 → 时间窗口必须按当前日期过去 7 天硬校验，不能靠旧 `.last_run` 放行。
- [2026-06-25] GitHub 静态页不是最终形态 → 最终展示由服务器 `GET /api/papers` 刷新；GitHub Pages 只保留 fallback。
- [2026-06-25] 子 agent 和页面职责混淆 → 子 agent 只产出 research run JSON，主 agent 校验并发布，服务器只接收和展示。
- [2026-06-25] 新 codeagent 只读散落文档容易漏流程 → 项目内 `.agents/skills/edge-agent-research-pipeline/SKILL.md` 是强入口，AGENTS 必须指向它。
- [2026-06-26] 主 agent 绕过 research-prompt.md 自写简化 prompt → 子 agent 没守标准 → 编造 404 链接。修复：发起子 agent 时 prompt 必须注入 research-prompt.md 全文，不许自写简化版。
- [2026-06-26] 本周大厂官方内容稀疏时凑数，拿不确定链接充数。修复：找不到官方 URL 就丢弃，大厂不足就少收，不凑数。
- [2026-06-26] 整理 agent 产出的 detail 含英文双引号会破坏 JSON 编码（方案 B 已停用整理 agent，不再产 detail，此条归档）。
- [2026-07-09] 周切换器上线后在线站点论文列表 0 篇、切换器跳错、热点链接 404、热点复读论文列表——四个功能回归全因「只验数据形状（assertIn 子串/count/测试绿）不验产品体验（不打开页面点链接、不跟上周对比）」。修复：加 `app/gates/gate_release.py` 机械门（契约/内链/编辑层/官方动态），FAIL 不许部署；发布前用 chrome-devtools 实点每类链接。
- [2026-07-09] `weekly_summary` 被当 run 派生字段（切 top N 论文填热点）→ 热点复读论文列表、无厂商新闻。根因：编辑层和采集层没分离。修复：weekly_summary 标为独立编辑产物，先采厂商动态再写热点，highlights 须 ≥5 外部 URL。
- [2026-07-09] 子 agent 报「0 官方动态」主 agent 直接信 → 厂商博客层根本没采。修复：0 官方动态必须配 `data/weeks/<label>-no-vendor.md` 逐厂证据，gate_release 拦。
- [2026-06-26] 调研 agent 标注 vendors/affiliation 只凭作者名推测，没附证据来源 → 用户质疑。修复：vendors/affiliation 标注必须有证据来源（OpenReview profile / Google Scholar / 论文 PDF 作者机构页），score_reason 里写明 affiliation 依据（如「Zhixiang Chi OpenReview profile 显示 Huawei Technologies Ltd，huawei.com 邮箱确认」），不许只凭名字猜。
- [2026-06-26] 整理 agent 等全部整理完才统一推送 → 页面长时间停在「整理中」（方案 B 已停用整理 agent，详情页改短摘要+标签+链接，无「整理中」状态，此条归档）。
- [2026-06-27] 6 维评分表演性太强（relevance 没口径、vendor 按出身加权、维度重叠、跨 run date 漂移）→ 改方案 B：2 维（relevance+contribution，0-20）+ source_tier facet + open_source bool + 多标签 tags。取消 6 段 detail 整理 agent（`detail-prompt.md` 删除）。新增 arXiv date 核对 + 跨 run 去重，根治「旧论文改日期充本周」。
- [2026-06-27] 强入口文档过时（SKILL/output-contract 写 7天/5维，代码当时是 14天/6维）→ 新 agent 照强入口跑必和 validate 冲突。修复：强入口全量同步到代码实际口径。
- [2026-06-27] MCP 配置只在用户级 opencode.json，Claude Code runtime 接不上 → 沉淀为项目级 `.mcp.json` + `docs/references/mcp-setup.md`，任何 agent 进来都能配。Windows 上 `command:"uvx"` 不走 shell PATH，用 `cmd /c uvx` 包一层。
- [2026-06-27] 14 天窗口太宽混入旧内容 → 改 7 天（一周）。硬数量目标（400-500/30-50/10-20）不切实际且诱导凑数 → 改"有多少合格收多少，列表轻量罗列可以多收"。开源大项目白名单不分主次 → 标注端侧推理/端侧agent（ADK/nanoagent）优先，vLLM/TensorRT 次要。query 写死不灵活 → 加自适应（返回少就放宽换词）。
- [2026-07-03] 部署后只 curl 解析数量 + 跑 tests 就宣布"验证通过"，结果 weekly 是自动糊的噪声（商业/传闻/药物 + 通用 why）质量回归没发现，chrome-devtools 残留标签导致只显 75 篇也没发现——是用户逼着 chromedev 验收才查出。修复：**每次 publish/deploy 后必做渲染验证**（见 harness.md §5 渲染验证）——chrome-devtools 加载线上页 ignoreCache 硬刷新，查 DOM 渲染（row 数/折叠/标签栏）+ **读内容质量**（weekly topic/why、论文摘要真的看不是数条数；weekly 手挑手写不许自动构建）+ console error。curl 对 ≠ 渲染对，tests 过 ≠ 页面好。chrome-devtools profile 锁不是借口，`taskkill //F //IM chrome.exe` 杀掉重连。
- [2026-07-03] 教训/工作流硬规则放 ~/.claude 本地记忆（换机器没了、别人看不到、不进 git）违反"仓库是唯一记录系统"原则 → 改：项目硬规则一律写进 repo（AGENTS 教训段 / harness 校验段 / SKILL），本地记忆只留个人偏好。
- [2026-07-15] 阶跃星辰发布全球首个 AI 智能体手机 STEPX Neo+智能体 OS（本周最大端侧新闻）漏掉 → 根因：把 vendor-research-guide 的厂商清单当穷举，清单只列 DeepSeek/Moonshot/Zhipu/Minimax/百川「等」，没主动扩阶跃星辰。修复：阶跃星辰补进 vendor-whitelist（stepfun.com 官方域名）+ vendor-research-guide 模型厂表 + OFFICIAL_SOURCE_DOMAINS；release-check 加厂商覆盖自检（中国头部模型厂含阶跃星辰，漏的写逐厂证据，不许只写「0」断言）。**vendor 清单是起步集不是穷举，遇到「等」要主动扩，模型厂亲自下场造端侧硬件是最对题信号。**
- [2026-07-15] github trending 区显示 07-03 旧仓（搁 12 天） → 根因：把「GitHub」当一个桶（只做了白名单 release 扫描），忘了 trending 是独立产物（`data/github_trending_top20.json` + 自己脚本 `collect_github_trending.py` + 自己 API `/api/trending`）。修复：gate_release 加 `check_trending_freshness`（mtime ≤7 天，>7 天 FAIL）；release-check 体验项加「trending 第一仓是本周的吗」人工确认。
- [2026-07-15] SNN 标签把 Ising 神经形态信道解码错标 → 根因：`auto_tags` 的 SNN 规则用裸 `neuromorphic` 当触发词，neuromorphic 是超集（Ising 机/事件硬件/memristor 不全是 SNN），裸 `spike-based`/`spiking neuron` 还可能是生物学放电。修复：SNN 规则只留 `spiking neural network`/`\bsnn\b`/`spikformer`/`spiking transformer`/`spiking neuron model`；validation-rules 加规则 21（标签触发词精度，不许伞词当唯一触发）；release-check 加「按非默认 tag 筛 2-3 篇看是否对题」人工抽检。**重蹈了 research-prompt §2 已警告的「关键字过匹配」反模式——加新方向时也要想 tag 规则精度，不只让 query 能搜到。**
- [2026-07-15] **共同根因**：执行了流程的字面（arXiv/HF/github-release/vendor 清单）没执行精神（端侧 AI 全景覆盖 + 内容语义自检）。gate_release 是结构性门（契约/内链/编辑层/官方动态≥1），拦不住语义缺口（漏厂商/trending 过期/标签太松）。修复：release-check 加「用户视角浏览」段（按 tag 筛看对题、trending 第一仓时效、官方动态扫漏大厂、highlights 链接是真实新闻非首页壳）。三次都是同一个病没真正吸收——跟 07-09「热点 404 测试不全面」同一教训：验证停在「数据形状对 + gate 绿 + 渲染 N 篇」，没像用户一样浏览内容语义。
- [2026-07-30] 论文/开源项目/公司项目 abstract 全英文——`output-contract.md` 明确要「大白话中文整理版，不搬原文」，但 `build_run_week.py` auto-convert 用 `first_sentence(summary)` 截 arxiv/HF **英文原文**首句，违反 spec（score_reason 自己写了「精修大白话待补」一直没补）。根因：auto-convert 是脚本不能翻译，LLM 翻译步骤缺失。修复：build_run_week 出 run JSON 后派 subagent 把英文 abstract 翻成中文大白话（1-2 句"这是什么"风格）写回 run JSON，再 validate/publish。**spec 要中文的，脚本做不到的，必须有 LLM 步骤兜底，不能留 TODO 不补。**
- [2026-07-30] github trending 每次要手动跑——gate_release `check_trending_freshness` 只拦过期不自动刷，`collect_github_trending.py` 靠主 agent 手动跑（gate FAIL 才补）。根因：trending 刷新不在刷新流程里。修复：`agent/refresh_trending.py`（collect + 转 top20 一步）作为**主 agent 每次周刷新的固定步骤**（build_run_week 后、翻译 subagent 前），`refresh_trending` 拿英文 desc → 翻译 subagent 把 trending desc + run abstract 翻中文。**不进 auto-deploy**（auto-deploy 的 refresh 会覆盖翻译 subagent 的中文 desc——refresh 拿英文 GitHub 描述，翻译要 LLM 在 refresh 之后）。gate 兜底（mtime>7d FAIL 提醒主 agent 补刷）。
- [2026-08-04] 推荐区把英文原标题当主信息，还把 `score_reason` 的 `auto-converted`/`votes=`/`待核实` 等流水线文字直接展示；同时 `build_run_week.py` 仅凭标题关键词自动推荐，导致弱相关内容挤进首屏。根因：完整收录和编辑推荐共用字段、页面层级反了、中文要求只有文档没有机械门。修复：推荐卡改为中文 `abstract` 主信息 + 中文 `recommendation_reason` + 小号原标题；自动汇集一律 `纳入`，只允许主 agent 阅读来源后晋升；validate 与 gate_release 双层拦英文摘要、缺失理由和内部占位词。**今后凡读者可见的内容契约，都必须同时落到 prompt、schema/存储、测试和真实构建 gate，不能只修页面或只写文档。**
- [2026-08-04] 中文摘要虽然解决了英文难读，但把“项目介绍”直接放到卡片第一视觉层，读者仍要读完一句话才知道条目叫什么。根因：数据里没有独立的中文项目名，页面只能拿 abstract 冒充标题。修复：新增 `title_zh` 全链路字段；推荐时由主 agent 编写简短中文名称，卡片固定按名称→介绍→关键词→理由→原标题展示；validate 与 gate_release 拦缺失、过长和直接复制 abstract。**名称和介绍是两个不同的内容契约，不能靠前端截句或同一字段兼任。**
