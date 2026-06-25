# AGENTS.md — edge_agent 项目工作指引

> 本文件是 agent 在此项目干活的"目录表 + 免疫系统"。
> ~100 行，渐进式披露：深层规则见 `docs/` 下各文档，按需加载，不一次性塞满上下文。
> **免疫系统**：每次 agent 犯错，在"已知教训"加一条防再犯（随错误增长，非写一次就忘）。
> **仓库是唯一记录系统**：决策/spec/计划全在此 repo，不在对话/Slack/人脑。

## 项目一句话
端侧 AI Agent 周报雷达：runtime agent 每周搜集端侧 agent / 推理最新动态（过去一周、大厂优先），本地 build，push 成品到 GitHub 纯展示。

## 两层架构（详见 ARCHITECTURE.md）
- **Runtime 层**（本地 `D:\proj\edge_agent`）：搜集 / 过滤 / 去重 / frontmatter 校验 / 状态 / build —— 动态运行时
- **展示层**（GitHub 仓库）：纯看板，只放 build 好的静态成品，零逻辑

## 目录地图
| 路径 | 用途 |
|---|---|
| `README.md` | 项目入口 + 搜集提示词（agent 运行读） |
| `AGENTS.md` | 本文件，根指引 |
| `ARCHITECTURE.md` | 顶层领域地图 + 数据流 |
| `docs/product-specs/SPEC.md` | 需求规格（source of truth） |
| `docs/design-docs/DESIGN.md` | 技术设计：搜集工作流 / 状态管理 |
| `docs/exec-plans/` | 实现计划（active / completed / tech-debt-tracker.md） |
| `docs/references/` | 外部资料（vendor-whitelist.md 人读版） |
| `content/posts/` | 调研条目 Markdown（frontmatter 规范见 `scripts/frontmatter.schema.json`） |
| `data/index.json` | 去重索引（已收录条目，id/slug 与 post 一致） |
| `data/vendors.yaml` | 大厂白名单（机器可读，gate_vendors 读取） |
| `data/.last_run` | 上次搜集时间戳（滚动窗口起点） |
| `scripts/` | 机械化强制：`frontmatter.schema.json` + gate_frontmatter/dedup/window/vendors/all.py |
| `site/` | build 出的静态成品（push 到 GitHub） |

## 核心约束（不可违反）
- **时间窗口**：仅过去一周（读 `data/.last_run` 算 cutoff）
- **增量去重**：搜集前先查 `data/index.json`，跳过已收录
- **大厂优先**：评分加权（见 SPEC 第六节），非硬排除学生
- **不分语言**：英文为质量软信号，不排除中文
- **数据可信**：实际效果必须来自原文，摘不到写"未报告"，禁止补编
- **范围**：端侧 agent 优先，端侧推理引擎次之纳入
- **gate 必过**：产出 post + 更新 index 后、build/push 前，必须 `python scripts/gate_all.py` EXIT 0

## 信息源（四类，缺一则雷达跑空）
学术论文 / 厂商技术博客 / GitHub releases / 产品大会发布（详见 SPEC 第一节）

## 工作流（runtime agent 每次跑）
1. 读 `data/.last_run` 算一周 cutoff
2. 读 `data/index.json` 取已收录集
3. 四类信息源检索窗口内新增
4. 按 SPEC 评分体系评估每条
5. 纳入的写 `content/posts/<slug>.md`（frontmatter 必须符合 `scripts/frontmatter.schema.json`）
6. 更新 `data/index.json`（加 entry，id/slug 与 post 文件一致）
7. **跑 `python scripts/gate_all.py`，必须 EXIT 0 才继续**；不过则修 post/index 后重跑
8. gate 过 → 写 `data/.last_run` = now（ISO）→ 本地 build → push 成品到 GitHub

## 已知教训（免疫系统，每次 agent 出错在此加一条）
<!-- 格式：[日期] 现象 → 规则。随运行积累。 -->
- [2026-06-25] frontmatter schema / gate 校验被误耦合到"网站选型" → 内容层 gate 不依赖渲染层，应先做，不捆绑等待
- [2026-06-25] pyyaml 把 frontmatter `date: 2026-06-24` 解析成 datetime.date 对象 → jsonschema format 校验前需 normalize 回 ISO 字符串
- [2026-06-25] Windows 环境 terminal 跑 `python` 会被 block → gate 脚本用 execute_code（subprocess）跑

## 待补（避免过度设计，按需推进）
- 熵管理 agent：定期扫过期 / 重复 / 死链 / frontmatter 漂移
- 网站选型（Hugo / Astro / MkDocs）→ 决定 build 与 `site/` 结构
- 各信息源检索适配器（arXiv API / 厂商博客 / GitHub releases / 大会议程）
- ADR（docs/decisions/）：评分权重 / 窗口 / 白名单等决策的理由记录
