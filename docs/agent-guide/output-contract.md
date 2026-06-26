# Research Agent Output Contract

调研子 agent 不改网页、不改服务器，只输出一个 JSON 文件。主 agent 保存到：

```text
research_runs/<run_id>.json
```

## 顶层结构

```json
{
  "run_id": "run-20260625-120000",
  "generated_at": "2026-06-25T12:00:00+08:00",
  "papers": []
}
```

## 单篇论文字段

每个 `papers[]` 必须包含：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 稳定唯一 id，建议小写 kebab-case |
| `title` | string | 论文标题 |
| `abstract` | string | agent 大白话整理版，给人看。回答「这是什么」，用中文短句重写，不搬论文摘要原文 |
| `effects` | string | agent 大白话整理版，给人看。回答「有什么结果」，只写最关键结果；必须来自原文，没有报告写 `未报告` |
| `mechanism` | string | agent 大白话整理版，给人看。回答「怎么做到的」，用普通话解释核心方法，不写论文式长句 |
| `paper_url` | string | 论文原文或权威论文页 URL |
| `date` | string | `YYYY-MM-DD`，必须在当前日期过去 7 天内 |
| `score` | integer | 0 到 100，必须等于 5 维之和 |
| `score_relevance` | integer | 0-35，主题契合度 |
| `score_vendor` | integer | 0-25，大厂关联度。参考口径：大厂官方 20-25；公司项目 15-20；公司+学校合作顶会 10-15；学校顶会 5-10；纯学术无公司 3-8 |
| `score_contribution` | integer | 0-20，技术贡献度。参考口径：创新度高 15-20；常见方法/工程整合 5-10 |
| `score_quality` | integer | 0-15，信息质量 |
| `score_recency` | integer | 0-5，时效新鲜度 |
| `score_reason` | string | 分数依据，说明高分/低分来自哪些维度 |
| `source_type` | string | `学术论文` / `官方技术博客` / `官方产品发布` |
| `is_major_vendor_official` | boolean | 大厂官方来源置为 `true`，会排序优先 |
| `category` | string | 三个方向之一：`应用` / `框架` / `算法` |
| `keywords` | string[] | 1-8 个中文优先关键词，例如 `GUI智能体`、`记忆`、`工具调用` |
| `insight_person` | string | 可为空 |
| `wiki_url` | string | 可为空 |

可选字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `detail` | string | 整理 agent 产出的 6 段深度整理（研究背景与问题 / 贡献点 / 实现方法 / 实验与结果 / 对端侧 agent 的意义 / 局限与未来），markdown 纯文本。列表页不显示，详情页主体。整理规则见 `docs/agent-guide/detail-prompt.md` |
| `authors` | string | 作者 |
| `vendors` | string | 机构/厂商。公司项目必填公司名（如 `Kuaishou` / `ByteDance` / `Tencent` / `Baidu` / `Meituan` / `JD` / `Pinduoduo` / `Netease`） |
| `venue` | string | arXiv / OpenReview / ACL / CVF 等 |
| `recommendation` | string | 默认 `纳入` |

## 示例

```json
{
  "run_id": "run-20260625-120000",
  "generated_at": "2026-06-25T12:00:00+08:00",
  "papers": [
    {
      "id": "fresh-edge-agent-paper",
      "title": "Fresh Edge Agent Paper",
      "abstract": "A real paper abstract about edge-side agent execution.",
      "effects": "Reports 23% latency reduction on an on-device benchmark.",
      "mechanism": "Uses a planner-executor loop with compressed local memory.",
      "paper_url": "https://arxiv.org/abs/2606.12345",
      "date": "2026-06-24",
      "score": 92,
      "score_reason": "主题直接命中端侧 agent，报告了明确 benchmark 提升。",
      "source_type": "学术论文",
      "is_major_vendor_official": false,
      "category": "应用",
      "keywords": ["GUI智能体", "端侧部署", "评测基准"],
      "insight_person": "",
      "wiki_url": "",
      "authors": "Author A; Author B",
      "vendors": "Example Lab",
      "venue": "arXiv",
      "recommendation": "纳入"
    }
  ]
}
```

## 首页可读性要求

`abstract`、`effects`、`mechanism` 是首页展示字段，必须由 agent 用大白话中文整理，写给人看，不复制论文原文：

- `abstract` 页面显示为「这是什么」：一句话说明这条内容解决什么问题，用普通话重写，不搬摘要原文。
- `effects` 页面显示为「有什么结果」：只写最关键结果；必须来自原文，没有量化结果写 `未报告`，不许编造或推测。
- `mechanism` 页面显示为「怎么做到的」：用普通话解释核心方法，不写论文式长句，不堆术语。
- 详细技术分解、公式、长段对比放到 wiki，不塞进首页字段。
- `score_reason` 必须中文优先，解释为什么高分或为什么待复审。
- 三字段都禁止粘贴论文 abstract 原文或官方通稿原文；首页是给人读的，不是给搜索引擎抓的。

## detail 字段（详情页深度整理）

`detail` 是可选字段，由主 agent 在 publish 后起整理 agent 单独产出，不进入 research run JSON，而是通过 `POST /api/paper-detail` 写入 DB。

- **内容**：6 段 markdown 纯文本，段落用 `## ` 标题分隔：研究背景与问题 / 贡献点 / 实现方法 / 实验与结果 / 对端侧 agent 的意义 / 局限与未来。
- **定位**：列表页展示 `abstract`/`effects`/`mechanism` 短句，详情页主体是 `detail` 6 段。两者不重复，detail 是更深一层整理。
- **产出规则**：整理 agent 的 prompt 模板和硬约束见 `docs/agent-guide/detail-prompt.md`。主 agent 起整理 agent 时必须注入该文件全文，不许自写简化版。
- **异步**：publish 后列表页立即可见，详情页先显示「整理中」；整理 agent 完成 `POST /api/paper-detail` 后，详情页刷新出 6 段内容。

## 校验

主 agent 发布前必须运行：

```powershell
python agent/validate_research_run.py research_runs/<run_id>.json
```

校验失败时不能发布。
