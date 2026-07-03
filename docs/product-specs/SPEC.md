# Product Spec

## 产品目标

每周展示端侧 AI Agent 相关最新论文和大厂官方动态。主 agent 通过子 agent 调研得到候选内容（不设硬数量目标，有多少合格收多少），校验后发布到服务器，网页刷新展示。

## 用户

- 需要快速跟踪端侧 AI agent 论文的人。
- 需要给论文补洞察人和 wiki 链接的人。
- 使用 Codex/Hermes 等 agent 做周期性调研的人。

## 成功标准

- 主 agent 能把子 agent 的调研结果保存成 `research_runs/*.json`。
- 校验脚本能拦截过期、非论文、字段缺失、链接非法、重复 id。
- 发布脚本能把合格结果发到服务器。
- 服务器页面能刷新展示最新论文。
- 洞察人和 wiki 链接可写。

## 展示字段

页面必须覆盖：

- 论文标题
- 论文摘要（这是什么）
- 论文效果（有什么结果，无则 `未报告`）
- 工作原理（怎么做到）
- 论文连接
- 洞察人
- wiki连接
- 分数（0-20）
- 日期
- 标签（1-8 个 tags，多标签，取自 data/tags.yaml）
- 来源档 source_tier（官方动态/开源大项目/公司项目/学校顶会/学校预印本）
- 开源 badge（open_source）

## 收录规则

- 时间窗口：当前日期过去 7 天（arXiv date 取自元数据，validate 核对）。
- 类型（source_tier facet）：`官方动态`（大厂官方博客/产品发布，命中官方域名）/ `开源大项目`（白名单大项目 release，github.com URL）/ `公司项目`（affiliation 命中公司，vendors 必填+证据）/ `学校顶会`（任何大学顶会顶刊）/ `学校预印本`（任何大学 arXiv 预印本，排序最低）。
- 大厂官方约束：`source_tier=官方动态` 必须来自官方域名；`source_tier=开源大项目` 必须在 `docs/references/big-projects-whitelist.md` 白名单内。非官方博客/新闻/社媒/GitHub release/二手解读一律排除。
- 排序：source_tier 优先级（官方动态 > 开源大项目 > 公司项目 > 学校顶会 > 学校预印本）+ score 降序。
- 链接：必须是论文原文、权威论文页、官方来源页或 github 仓。
- 效果：必须来自原文；没有则写 `未报告`。
- 数量：不设硬目标，有多少合格收多少；列表轻量罗列（不写详细分析），可以多收。不为凑数量收垃圾条目。
- 标签：每条 1-8 个 tags，取自 `data/tags.yaml` 词表，多标签，一个工作可挂多个。
- 评分：2 维（score_relevance 0-10 + score_contribution 0-10 = score 0-20）+ open_source bool facet。

## 首页信息架构

- 页面顶部采用 signal-terminal 设计 + 4 维 faceted 筛选（方向/应用/硬件/模型，多标签多选）+ weekly 热点模块（`/api/weekly` + `data/weekly_summary.json`），并显示各筛选维度数量。
- 列表内排序：source_tier 优先级（官方动态 > 开源大项目 > 公司项目 > 学校顶会 > 学校预印本）+ score 降序；tier 分组展示；支持搜索排序。
- 首页面向快速扫读，不写论文式长段落。
- `abstract` 在页面显示为「这是什么」：一句话讲清楚这条内容是什么。
- `effects` 在页面显示为「有什么结果」：只保留关键指标或 `未报告`。
- `mechanism` 在页面显示为「怎么做到的」：用普通中文讲核心方法。
- 深入解释、推导、长引用、人工洞察放 wiki。

## 非目标

- 服务器不搜索论文。
- 不把厂商博客、产品发布、GitHub release 混进论文页。
- 不再把 GitHub Pages 作为最终部署形态。
- 不用旧样例撑页面数量。
