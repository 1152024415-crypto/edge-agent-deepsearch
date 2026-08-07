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
| `title_zh` | string | 自动搜集时为空；主 agent 推荐时填写 40 字以内的简短中文项目名，回答「它叫什么」，不能复制 abstract |
| `abstract` | string | agent 大白话整理版。回答「这是什么」，中文短句重写，不搬原文 |
| `effects` | string | agent 大白话整理版。回答「有什么结果」，只写最关键结果；必须来自原文，没有报告写 `未报告` |
| `mechanism` | string | agent 大白话整理版。回答「怎么做到的」，普通话解释核心方法 |
| `paper_url` | string | 论文原文 / 权威论文页 / 官方来源页 / github 仓 URL |
| `date` | string | `YYYY-MM-DD`，必须在以运行日为末日、包含当日的最近 7 个自然日内。arXiv 新稿取提交日；旧稿仅在本周有实质修订时可取更新日 |
| `arxiv_date_basis` | string | `submitted` / `updated`。自动搜集保留日期来源 |
| `arxiv_revision_note` | string | `arxiv_date_basis=updated` 时必填的中文版本对比结论；必须说明实验、方法、数据、代码或结论的实质变化，排版/勘误不算 |
| `score` | integer | 0 到 20，必须等于 `score_relevance + score_contribution` |
| `score_relevance` | integer | 0-10 端侧契合度。明确端侧部署 8-10 / 技术栈或直接可迁移工作 4-7 / 宽泛云端关联 1-3 / 完全无关排除 |
| `score_contribution` | integer | 0-10 创新贡献。创新度高 7-10 / 常见方法或工程整合 1-6；低贡献仍可完整收录 |
| `score_reason` | string | 直接展示给读者的中文分数依据：解释端侧相关性与贡献；公司项目另写 affiliation 证据来源（OpenReview/Scholar/PDF 机构页）。禁止流水线状态文字 |
| `source_tier` | string | 来源 facet：`官方动态` / `公司项目` / `学校顶会` / `学校预印本` / `开源大项目` |
| `open_source` | boolean | 是否开源（仓库/数据集/模型开源）。facet，不打分 |
| `tags` | string[] | 1-8 个标签，必须取自 `data/tags.yaml` 词表（人读版 `docs/references/tag-taxonomy.md`）。多标签，一个工作可挂多个 |
| `edge_agent_scope` | string | 自动搜集统一写`待核实`；发布前主 agent 阅读来源后改为`手机` / `PC` / `其他端侧` / `非端侧Agent`。关键 Agent 闭环至少部分实际在设备端运行才算真正端侧 Agent |
| `edge_agent_evidence` | string | `手机`/`PC`/`其他端侧`时必填的中文证据，说明哪个规划、记忆、工具或行动闭环运行在什么设备上；`待核实`/`非端侧Agent`时为空 |
| `candidate_source` | string | 候选来源：`arxiv` / `huggingface` / `github` / `vendors`；由转换器写入，不面向读者 |
| `candidate_ref` | string | 原始候选 JSON 记录的规范化 SHA-256 指纹；必须唯一命中 manifest 对应来源的 `candidate_refs`，同一候选不能生成两条 run 内容，且最终英文 `title` + `paper_url` + `date` 必须匹配该记录的稳定身份；由转换器写入，不得手填 |
| `insight_person` | string | 可为空 |
| `wiki_url` | string | 可为空 |

`candidate_source=github` 只能映射为 `source_tier=开源大项目`，且 `paper_url` 必须属于 `docs/references/big-projects-whitelist.md` 的项目；不能用任意 GitHub 小仓伪装成学校或公司项目。

可选字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `authors` | string | 作者 |
| `vendors` | string | 机构/厂商。`source_tier=公司项目` 必填公司英文名（如 `Kuaishou` / `ByteDance` / `Tencent`） |
| `affiliation_evidence_url` | string | `source_tier=公司项目` 必填的一手机构证据 URL，只接受 arXiv PDF、OpenReview/Google Scholar 或认可的论文出版页；GitHub repo/release 不算机构证据。其他来源档可为空；声明多个 vendors 时，`score_reason` 必须逐家解释证据关系 |
| `venue` | string | arXiv / OpenReview / ACL / CVF 等 |
| `recommendation` | string | 默认 `纳入` |
| `recommendation_reason` | string | `recommendation=推荐` 时必填：一句中文说明「为什么值得优先看」；`纳入` 时留空 |

## source_tier 口径

- `官方动态`：24 个规范厂商/模型实验室的官方技术博客或官方产品发布。`paper_url` 必须命中官方域名白名单。排序最前。
- `开源大项目`：业界认可的开源大项目重大 release/更新（见 `docs/references/big-projects-whitelist.md`，如 vLLM/SGLang/llama.cpp/ExecuTorch/ADK/TensorRT 等）。`paper_url` 必须是 `github.com` 仓地址。非白名单小仓不收。
- `公司项目`：快手/字节/腾讯/百度/美团/京东/拼多多/网易等公司独立或主导的研究（arXiv 或顶会，affiliation 命中公司）。`vendors` 与 `affiliation_evidence_url` 均必填；未核实一手证据前先放 `学校预印本`，不丢条目。
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
      "title_zh": "端侧智能体预算记忆管理",
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
      "edge_agent_scope": "其他端侧",
      "edge_agent_evidence": "论文在 Jetson 测试床运行智能体记忆筛选、共享和信任门控闭环。",
      "insight_person": "",
      "wiki_url": "",
      "authors": "Beining Wu; Zihao Ding; Jun Huang; Yanxiao Zhao",
      "venue": "arXiv",
      "recommendation": "推荐",
      "recommendation_reason": "直接解决端侧智能体的长期记忆膨胀问题，并在 Jetson 真机上同时验证了内存、通信和安全收益。"
    }
  ]
}
```

## 首页可读性要求

`title_zh`、`abstract`、`effects`、`mechanism`、`recommendation_reason` 是读者可见字段，必须由 agent 用大白话中文整理，写给人看，不复制原文：

- `title_zh` 页面显示为中文项目名：回答「它叫什么」，至少 2 个中文字符、总长不超过 40 字；不能直接复制 abstract。自动搜集阶段留空，只有主 agent 策展推荐时填写。
- `abstract` 页面显示为「这是什么」：一句话说明这条内容解决什么问题。
- `effects` 页面显示为「有什么结果」：只写最关键结果；没有量化结果写 `未报告`，不许编造或推测。
- `mechanism` 页面显示为「怎么做到的」：普通话解释核心方法，不堆术语。
- `score_reason` 会直接显示在详情页，必须用中文解释为什么这个分 + affiliation 证据来源；禁止“自动初评”“主 Agent 复核”“待复核”等流水线状态。
- `recommendation_reason` 页面显示为「值得优先看」：只能在主 agent 读过来源并确认价值后填写，不能复述标题，不能写评分流水账。
- 六个读者字段 `title_zh`/`abstract`/`effects`/`mechanism`/`score_reason`/`recommendation_reason` 都禁止粘贴英文 abstract、官方通稿原文或内部流程文字（如 `auto-converted`、`votes=`、`待核实`、`精修待补`、`自动初评`、`主 Agent 复核`）；摘要不得以省略号截断。

## 推荐策展规则

- 自动汇集脚本和搜集子 agent 对所有条目一律输出 `title_zh: ""`、`recommendation: "纳入"`、`recommendation_reason: ""`、`edge_agent_scope: "待核实"`、`edge_agent_evidence: ""`，不得按标题关键词自动晋升或自动添加`方向:端侧agent`。
- 主 agent 完成全量筛选后，再逐条判断哪些内容值得优先看；推荐数量不设固定比例，按本周实际质量决定并排序，同时填写 `title_zh` 和 `recommendation_reason`。
- 真正端侧 Agent 要同时具备 Agent 闭环和设备端执行证据。凡分类为`手机`、`PC`或`其他端侧`，必须带`方向:端侧agent`、`score_relevance>=8`并设置为`推荐`；手机排最前、PC 第二、其他端侧第三。手机/PC只是云端 Agent入口、普通端侧模型/量化/缓存/检测、以及 Orchard 一类云端 Agent 训练基础设施都标`非端侧Agent`。
- 只要本周有可发布内容，发布产物至少应有 1 条人工精选；每条推荐都必须有中文 `title_zh`、中文 `abstract` 和中文 `recommendation_reason`。
- `title` 保留原文以便核对来源；推荐卡片固定按中文 `title_zh` 项目名 → `abstract` 介绍 → `tags` 关键词 → `recommendation_reason` → 英文原标题展示。

## 检索覆盖伴随文件

每个 run 同目录必须有 `research_runs/collection-manifest.json`。它是发布前审计证据：除动态 7 日窗口及 arXiv/HF/GitHub/厂商四类来源的完成项外，还要记录逐厂成功来源，以及四个最终候选 JSON 的绝对路径、精确条数、文件 SHA-256、逐记录 `candidate_refs` 和每个记录的稳定 title+URL+来源日期身份绑定。候选完成后运行 `python agent/attest_candidates.py`。组装器会核对实际文件，并给每条 run 内容写入唯一 `candidate_source` + `candidate_ref`；发布客户端和服务器再次核对血缘、拒绝复用，并重算最终原标题/URL/日期身份。缺来源、HF 少一天、GitHub 只刷 Trending、厂商全不可达、arXiv 分页截断、候选条数/哈希变化或 run 条目不来自已证明候选都会失败。写 API 还必须携带服务端配置的 `EDGE_PUBLISH_TOKEN`。

## 校验

主 agent 发布前必须运行：

```powershell
python agent/validate_research_run.py research_runs/<run_id>.json
```

校验内容：collection manifest、必填字段、中文 `abstract`、推荐文案、`source_tier`、`tags`、精确 7 日窗口、评分加总、官方域名、github URL、vendors、死链、arXiv 提交/更新日、更新稿实质变化说明和跨 run 去重。校验失败不能发布。
