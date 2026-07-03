# Site Display Spec

展示层只消费结构化论文数据，不负责搜索论文。最终形态以服务器页面为准，静态 GitHub Pages 只作为 fallback。

## 数据来源

服务器页面从 API 读取：

```http
GET /api/papers
```

写入洞察人和 wiki：

```http
POST /api/insights
```

主 agent 发布调研结果：

```http
POST /api/research-runs
```

完整字段见 `docs/site/api-contract.md`。

## 默认视图

页面采用 **signal-terminal 设计**：顶部为终端式信号区，按 `source_tier` 分组（官方动态 / 开源大项目 / 公司项目 / 学校顶会 / 学校预印本，5 档 badge），每组内按 score 降序；每条卡片带**信号强度条**（依据 score 0-20 渲染强度）。

支持 **4 维 faceted 筛选**（方向 / 应用 / 硬件 / 模型，多标签多选，取自 `data/tags.yaml` 的 `维度:值` 标签）+ **搜索框排序**（按关键词过滤标题/摘要）。`source_tier` 用 5 档 badge 标注，`open_source` 用开源 badge。列表排序按 source_tier 优先级 + score 降序。

### weekly 热点模块

页面顶部含 weekly 热点模块，数据来自：

```http
GET /api/weekly
```

返回 `data/weekly_summary.json`，含 `overview`（本周综述）+ `highlights[]`（每条 `{paper_id, topic, why}`）。展示本周精选热点与一句话理由。

每张卡片字段：

| 字段 | 说明 |
|---|---|
| 分数 | 0-20，source_tier 优先级内降序 |
| source_tier | 官方动态/开源大项目/公司项目/学校顶会/学校预印本 badge |
| 开源 | open_source=true 时显示开源 badge |
| 日期 | 内容日期 |
| 标题 | 点击进详情页 |
| 标签 | 1-8 个 tags chip |
| 这是什么 | abstract 大白话 |
| 有什么结果 | effects，必须来自原文；没有则显示 `未报告` |
| 怎么做到 | mechanism 简述 |
| 评分依据 | score_reason |
| 洞察人 | 可编辑 |
| wiki连接 | 可编辑或跳转 |

## 排序

- 默认：`source_tier` 优先级（官方动态 > 开源大项目 > 公司项目 > 学校顶会 > 学校预印本）+ `score` 降序。
- 必须支持：按分数、日期排序（source_tier 优先级始终在前）。
- 排序只改变展示顺序，不改服务器数据。

## 空状态

没有本周合格内容时，页面显示空状态。禁止展示旧样例或非论文内容来填充数量。

## 静态 Fallback

`app/build.py` 可以生成 `site/index.html`。该页面用于没有服务器时预览结构，仍必须遵守：

- 当前日期过去 7 天过滤。
- 只显示真实论文/官方动态/开源大项目更新（source_tier 标注），无非官方博客/新闻/二手解读。
- 洞察人 / wiki 可降级写入 `localStorage`。
