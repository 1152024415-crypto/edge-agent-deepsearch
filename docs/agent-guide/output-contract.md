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

## 单篇条目字段

每个 `papers[]` 必须包含（方案 B：2 维评分 + 多标签 + source_tier）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 稳定唯一 id，建议小写 kebab-case |
| `title` | string | 论文/动态标题 |
| `abstract` | string | agent 大白话整理版。回答「这是什么」，中文短句重写，不搬原文 |
| `effects` | string | agent 大白话整理版。回答「有什么结果」，只写最关键结果；必须来自原文，没有报告写 `未报告` |
| `mechanism` | string | agent 大白话整理版。回答「怎么做到的」，普通话解释核心方法 |
| `paper_url` | string | 论文原文 / 权威论文页 / 官方来源页 / github 仓 URL |
| `date` | string | `YYYY-MM-DD`，必须在当前日期过去 7 天内。**arXiv 条目的 date 必须取自 arXiv 元数据的提交日**，validate 会核对，不许 agent 自填或为塞进窗口改日期 |
| `score` | integer | 0 到 20，必须等于 `score_relevance + score_contribution` |
| `score_relevance` | integer | 0-10 端侧契合度。口径：明确端侧部署 8-10 / 可迁移且作者提到端侧场景 4-7 / 纯云端无端侧考量 0-3 或直接排除 |
| `score_contribution` | integer | 0-10 创新贡献。口径：创新度高 7-10 / 常见方法或工程整合 3-6 |
| `score_reason` | string | 分数依据 + affiliation 证据来源（OpenReview/Scholar/PDF 机构页），中文优先 |
| `source_tier` | string | 来源 facet：`官方动态` / `公司项目` / `学校顶会` / `学校预印本` / `开源大项目` |
| `open_source` | boolean | 是否开源（仓库/数据集/模型开源）。facet，不打分 |
| `tags` | string[] | 1-8 个标签，必须取自 `data/tags.yaml` 词表（人读版 `docs/references/tag-taxonomy.md`）。多标签，一个工作可挂多个 |
| `insight_person` | string | 可为空 |
| `wiki_url` | string | 可为空 |

可选字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `authors` | string | 作者 |
| `vendors` | string | 机构/厂商。`source_tier=公司项目` 必填公司英文名（如 `Kuaishou` / `ByteDance` / `Tencent`），并附证据来源写在 `score_reason`。当前 run 的 affiliation 核实 defer：未识别公司的论文一律标 `学校预印本`，公司论文待识别 |
| `venue` | string | arXiv / OpenReview / ACL / CVF 等 |
| `recommendation` | string | 默认 `纳入` |

## source_tier 口径

- `官方动态`：18 家设备/模型大厂官方技术博客或官方产品发布。`paper_url` 必须命中官方域名白名单（见 `docs/references/vendor-whitelist.md`）。排序最前。
- `开源大项目`：业界认可的开源大项目重大 release/更新（见 `docs/references/big-projects-whitelist.md`，如 vLLM/SGLang/llama.cpp/ExecuTorch/ADK/TensorRT 等）。`paper_url` 必须是 `github.com` 仓地址。非白名单小仓不收。
- `公司项目`：快手/字节/腾讯/百度/美团/京东/拼多多/网易等公司独立或主导的研究（arXiv 或顶会，affiliation 命中公司）。`vendors` 必填。
- `学校顶会`：任何高校独立发表的顶会顶刊（NeurIPS/ICML/ICLR/MobiSys/SenSys/ASPLOS/ACL/CVPR/ICCV/EMNLP/AAAI/IJCAI/TPAMI/TNNLS/ToN）。不再卡中美名校——任何正规大学都收。
- `学校预印本`：任何大学作者发的 arXiv 预印本（非顶会但主题强相关）。新鲜端侧工作多先上 arXiv，这一档保证雷达不漏最新真东西；排序最低。

## 示例

```json
{
  "run_id": "run-20260625-120000",
  "generated_at": "2026-06-25T12:00:00+08:00",
  "papers": [
    {
      "id": "curator-on-device-memory-2026",
      "title": "Forget to Improve: On-Device LLM-Agent Continual Learning via Budget-Curated Memory",
      "abstract": "用一个「每字节净价值」分数管理端侧 agent 的经验记忆生命周期，在 RAM 和能耗预算下做裁剪、共享和信任门控。",
      "effects": "Jetson 测试床上内存减 2.7 倍、上行链路减 2.4 倍，注入攻击成功率从 0.75 降到 0，任务准确率从 0.528 升到 0.605。",
      "mechanism": "每条记忆按价值减危害的每字节净分评分，KEEP/SHARE/TRUST 三个决策分别在 RAM、上行链路、来源维度门控，实现亚线性上下文增长。",
      "paper_url": "https://arxiv.org/abs/2606.25115",
      "date": "2026-06-23",
      "score": 14,
      "score_relevance": 9,
      "score_contribution": 5,
      "score_reason": "明确端侧 LLM agent 记忆管理，Jetson 真机验证（relevance 9）。净价值每字节框架有创新但属记忆治理细分（contribution 5）。作者机构 arXiv 元数据未明确标注，vendors 空。",
      "source_tier": "学校顶会",
      "open_source": false,
      "tags": ["方向:端侧agent", "方向:记忆", "方向:能耗功耗", "方向:安全隐私"],
      "insight_person": "",
      "wiki_url": "",
      "authors": "Beining Wu; Zihao Ding; Jun Huang; Yanxiao Zhao",
      "venue": "arXiv",
      "recommendation": "纳入"
    }
  ]
}
```

## 首页可读性要求

`abstract`、`effects`、`mechanism` 是首页展示字段，必须由 agent 用大白话中文整理，写给人看，不复制原文：

- `abstract` 页面显示为「这是什么」：一句话说明这条内容解决什么问题。
- `effects` 页面显示为「有什么结果」：只写最关键结果；没有量化结果写 `未报告`，不许编造或推测。
- `mechanism` 页面显示为「怎么做到的」：普通话解释核心方法，不堆术语。
- `score_reason` 必须中文优先，解释为什么这个分 + affiliation 证据来源。
- 三字段都禁止粘贴论文 abstract 原文或官方通稿原文。

## 校验

主 agent 发布前必须运行：

```powershell
python agent/validate_research_run.py research_runs/<run_id>.json
```

校验内容：必填字段、`source_tier` 枚举、`tags` 词表、`date` 7 天窗口、`score`=2 维之和、`source_tier=官方动态` 官方域名、`source_tier=开源大项目` github URL、`source_tier=公司项目` vendors 非空、**paper_url HTTP 死链检查**、**arXiv URL 提交日核对**（防 date 漂移）、**跨 run 去重 warning**（命中上次 run 的 id 提醒，不 fail）。校验失败不能发布。
