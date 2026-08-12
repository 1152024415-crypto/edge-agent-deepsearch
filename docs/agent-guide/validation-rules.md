# Agent Validation Rules

这些规则给主 agent 和调研子 agent 使用。任何违反规则的内容都不能发布到服务器。

## 硬规则

1. `source_tier` 必须是 `官方动态` / `公司项目` / `学校顶会` / `学校预印本` / `开源大项目` 之一。
2. `官方动态` 条目 `paper_url` 必须命中官方域名白名单（见 `docs/references/vendor-whitelist.md`）。非官方博客、新闻、社媒、GitHub release、二手解读一律排除。
3. `开源大项目` 条目 `paper_url` 必须是 `github.com` 仓地址，且项目在 `docs/references/big-projects-whitelist.md` 白名单内（业界认可大项目）。非白名单小仓不收。
4. `公司项目` 条目 `vendors` 必填公司英文名，`affiliation_evidence_url` 必填一手证据 URL（只接受 arXiv PDF / OpenReview / Google Scholar / 认可论文出版页），并在 `score_reason` 明确解释该证据如何支持每一个声明的 vendor；GitHub repo/release 不能作为机构证据。不许只凭作者名、标题或模型名推测，证据未核实的一律先标 `学校预印本`。
5. `学校顶会` 条目作者须来自任何正规大学（不再卡中美名校，见 `research-prompt.md` 硬约束），且发表在顶会顶刊。`学校预印本` 是任何大学作者的 arXiv 预印本（非顶会但强相关）。
6. `paper_url` 必须指向论文原文、权威论文页、官方来源页或 github 仓。
7. 标题、摘要、链接必须对应同一篇论文或同一条官方动态。
8. `date` 必须在以运行日为末日、包含当日的最近 7 个自然日内。窗口由 `research_collection.collection_window` 动态计算，不允许采集脚本写死。**arXiv 条目 date 必须取自 arXiv 元数据提交日**。
9. `effects` 必须来自论文原文或官方来源；没有报告就写 `未报告`。
10. `tags` 必须是 1 到 8 个，取自 `data/tags.yaml` 词表，多标签。词表外的标签先加进 `data/tags.yaml` 再用。
11. `score` = `score_relevance`(0-10) + `score_contribution`(0-10)，上限 20。validate 校验加总。
12. `score_relevance` 口径：明确端侧部署 8-10 / 端侧技术栈或直接可迁移工作 4-7 / 仅宽泛云端关联 1-3 / 完全无关排除。
13. `score_contribution` 口径：创新度高 7-10 / 常见方法或工程整合 1-6。低贡献不等于删除，只影响排序和推荐判断。
14. 首页展示字段必须易读：`abstract` 写「这是什么」，`effects` 写「有什么结果」，`mechanism` 写「怎么做到的」。
15. **过滤 GUI agent**：纯 GUI 自动化（屏幕点击/GUI 操作/屏幕解析）不收，除非有显著非 GUI 创新（CLI 范式、系统架构、推理优化、部署能力、安全）。
16. **常见但相关的工作仍完整收录**：普通量化/剪枝、缓存组合、常规 benchmark、通用 serving 只要属于 AI 推理/部署或对资源受限设备有直接迁移价值就保留并低分，通常不推荐。只有完全无关或关键词误匹配才排除。
17. **死链检查**：`paper_url` 必须 HTTP 可访问。validate 对每个 URL 发 HEAD 请求，HEAD 失败 fallback GET；超时/网络不可达记 alive + warning 不 fail；只有 404 才 fail。单 URL 超时 5 秒。
18. **arXiv date 与修订核对**：`paper_url` 是 arXiv 时，validate 按 `arxiv_date_basis` 核对真实提交日或更新日。若为 `updated`，必须有主 agent 对比旧版后的中文 `arxiv_revision_note`，明确实质变化；仅改排版、作者信息、勘误或摘要无实质变化不能收。离线 date 核对 warning 跳过，但 revision note 仍是硬门。
19. **跨 run 去重**：validate 读 `data/.last_run_papers.json`（publish 时写入），命中上次 run 的 id 给 warning（不 fail，因相邻两周窗口有合法重叠），提示主 agent 核实是否真有新进展。
20. **内容匹配抽检**（主 agent publish 前）：对 `source_tier=官方动态` 和 `source_tier=开源大项目` 的条目，fetch URL 核验页面内容与标题摘要对应。URL 能打开 ≠ 内容对题，对不上就丢。（07-15 教训：阶跃星辰 AI 手机新闻用了官网首页 stepfun.com 当 URL，但首页是 JS 壳不专门讲 STEPX Neo，内容对不上题——该条改走 weekly_summary 编辑性 highlight 用真实新闻链接，run 里丢弃。）
21. **标签触发词精度**：`auto_tags` 每条方向 tag 的触发词必须是该架构/方法的特定词，不许用**伞词**当唯一触发词。`neuromorphic` 是超集（含 Ising 机/事件硬件/memristor，不全是 SNN）；`spike-based`/`spiking neuron` 可能是生物学放电（神经科学）。`方向:SNN` 必须用 `spiking neural network`/`\bsnn\b`/`spikformer`/`spiking transformer`/`spiking neuron model`。通则：新增 tag 前想「会不会匹配到别的领域」（SLM=Small/Speech、quantization 量化 BERT、neuromorphic≠SNN）。
22. **中文摘要机械门**：每条 `abstract` 必须是可直接阅读的中文「这是什么」（至少 8 个中文字符）。英文 abstract 原文不能发布；`abstract`/`effects`/`mechanism` 禁止出现 `auto-converted`、`votes=`、`待核实`、`精修待补` 等内部流程文字。
23. **推荐策展机械门**：自动汇集一律 `纳入`，不得按标题关键词自动推荐。只有主 agent 读过来源后可改为 `推荐`；每条推荐必须填写中文 `recommendation_reason`（至少 8 个中文字符、无内部占位词）。构建产物有内容时至少有 1 条合格推荐，否则 `gate_release` 阻止部署。
24. **推荐项目名机械门**：自动汇集 `title_zh` 一律留空；主 agent 晋升推荐时必须填写简短中文项目名（至少 2 个中文字符、总长不超过 40 字、无内部占位词）。`title_zh` 回答“它叫什么”，不得与回答“它做什么”的 `abstract` 完全相同。推荐卡固定按项目名 → 介绍 → 关键词 → 推荐理由 → 英文原标题展示。
25. **相关性触发词必须成对验证**：广搜不等于裸关键词入库。明确设备语境（on-device/edge device/mobile/embedded/NPU/MCU/FPGA）还必须与 AI 模型或任务语境组合；普通图的 `edge`、论文语义中的 `embedded/deployed`、energy-based model、数学“推理”、树搜索 pruning、云端 LLM 面向 mobile users 均不算端侧证据。新增或放宽触发词时，必须在 `tests/test_research_collection.py` 同时加入“应收”与“碰撞应排除”回归样例，避免只测召回或只测降噪。
26. **官方页面日期核验**：`source_tier=官方动态` 的 `date` 必须来自具体页面正文发布日期。sitemap `lastmod`、搜索抓取时间、页面模板更新时间和地区镜像不能作为发布日；同一动态的语言/地区副本只留一个规范 URL。
27. **中心贡献校验**：相邻技术触发词必须描述标题或核心方法；只在摘要背景、对比基线或应用描述中偶然提到 `multi-agent`、蒸馏、serving、低功耗，不得据此入库。真正端侧 Agent 必须额外满足设备语境 + Agent 闭环证据。
28. **新开源项目晋升校验**：非白名单 Trending 仓库只进线索审计，不进 canonical candidates。主 agent 只有在核对影响力、代码真实性、本周事件和设备闭环后，才可更新白名单；修改必须同时覆盖正例与未知小仓拒绝回归测试。
25. **检索覆盖机械门**：`research_runs/collection-manifest.json` 必须覆盖运行日向前含当日的 7 个自然日、arXiv 规范大类扫描且分页自然终止、HF 每个日期、GitHub Trending 和白名单 release 两项、24 个规范厂商/模型实验室逐厂成功来源证据。四个候选 JSON 即使 0 条也必须以空数组落盘，并由 `agent/attest_candidates.py` 写入路径、精确条数、文件 SHA-256、逐候选记录指纹和稳定 title+URL+来源日期身份绑定；每条 run 内容必须携带唯一且不可复用的 `candidate_source` + `candidate_ref`，最终英文标题、原文 URL 与日期必须匹配同一候选。`candidate_source=github` 还必须固定为 `source_tier=开源大项目` 并命中大项目白名单。缺文件、坏 JSON、条数/哈希/身份/血缘不符、某厂全不可达或 arXiv 命中页数上限均不能组装。manifest 与血缘嵌入 run，发布客户端和服务器都会复验；写 API 强制 `EDGE_PUBLISH_TOKEN`，正常周报禁止绕过。
26. **公司归属只认明确机构证据**：自动转换只能读取 affiliation/机构字段，不得从标题、摘要或模型名推测公司。Qwen/NVIDIA/Google 等被研究对象不等于作者机构。

27. **评分依据必须是读者文案**：`score_reason` 会直接显示在详情页，必须解释“为何与端侧相关、贡献在哪里”，不得出现“自动初评”“主 Agent 复核”“待复核”或抓取摘要截断等流水线状态。`build_run_week.py` 只生成面向读者的依据；validate 与 `gate_release` 对所有条目双层拦截内部流程词，不仅检查推荐条目。
28. **真正端侧 Agent 强制推荐门**：自动汇集统一`edge_agent_scope=待核实`且不得自动加`方向:端侧agent`；发布时不得残留`待核实`。只有关键 Agent 闭环至少部分运行在设备端才能分类为`手机`/`PC`/`其他端侧`，并且必须有中文`edge_agent_evidence`、`方向:端侧agent`、`score_relevance>=8`和`recommendation=推荐`。`非端侧Agent`不得使用该标签或填写证据。推荐排序固定为手机 > PC > 其他端侧 > 普通推荐，再按 source_tier + score。

## 评分口径参考

2 维，搜集 agent/脚本可给初值，最终由主 agent 阅读来源后确认。最终排序靠 `source_tier` 优先级 + `score`：

- `score_relevance`（0-10）：明确端侧 8-10 / 技术栈或直接可迁移 4-7 / 宽泛云端关联 1-3 / 完全无关排除
- `score_contribution`（0-10）：创新度高 7-10 / 常见方法工程整合 1-6
- `source_tier` 排序优先级：官方动态 > 开源大项目 > 公司项目 > 学校顶会 > 学校预印本
- `open_source`：bool facet，不打分，同等条件下开源优先

## 主 agent 发布前检查

主 agent 必须运行自动校验：

```powershell
python agent/validate_research_run.py research_runs/<run_id>.json
```

自动校验先检查 collection manifest，再覆盖必填字段、中文 `abstract`、推荐文案、`source_tier`、`tags`、精确 7 日窗口、评分加总、官方域名、github URL、vendors、死链、arXiv date 和跨 run 去重。

### 内容抽检（半自动）

自动校验只拦死链和 date 造假，拦不住「URL 能开但内容不对题」。主 agent publish 前对 `source_tier=官方动态` 和 `source_tier=开源大项目` 的条目：

1. fetch 该 URL，读页面内容。
2. 核验页面标题/正文与 run 里的 `title`、`abstract` 对应。
3. 对不上就丢弃该条，不许带病发布。

### 失败处理

- 不是论文/动态：删除该条。
- 链接不匹配 / 内容对不上题：删除或重新核验。
- 死链：删除或换权威链接。
- date 与 arXiv 不一致：改成 arXiv 真实提交日，超窗口就丢弃。
- 超出7天窗口：删除。
- 字段缺失：要求子 agent 补全。
- 效果缺失：保留时必须写 `未报告`。
- 英文摘要或内部占位词：回到原文，用中文重写后再验证。
- 推荐缺少简短中文项目名或具体中文理由：降级为 `纳入`，或由主 agent 阅读来源后补全；不能拿 abstract 冒充项目名，也不能拿 `score_reason` 顶替推荐理由。

不能为了凑数量发布不合格内容。本周合格内容不足就少收。
