# Agent Validation Rules

这些规则给主 agent 和调研子 agent 使用。任何违反规则的内容都不能发布到服务器。

## 硬规则

1. `source_tier` 必须是 `官方动态` / `公司项目` / `学校顶会` / `学校预印本` / `开源大项目` 之一。
2. `官方动态` 条目 `paper_url` 必须命中官方域名白名单（见 `docs/references/vendor-whitelist.md`）。非官方博客、新闻、社媒、GitHub release、二手解读一律排除。
3. `开源大项目` 条目 `paper_url` 必须是 `github.com` 仓地址，且项目在 `docs/references/big-projects-whitelist.md` 白名单内（业界认可大项目）。非白名单小仓不收。
4. `公司项目` 条目 `vendors` 必填公司英文名，并附 affiliation 证据来源（OpenReview profile / Google Scholar / 论文 PDF 机构署名），写在 `score_reason`，不许只凭作者名推测。当前 run 的 affiliation 核实 defer：未识别公司的论文一律标 `学校预印本`，公司论文待识别。
5. `学校顶会` 条目作者须来自任何正规大学（不再卡中美名校，见 `research-prompt.md` 硬约束），且发表在顶会顶刊。`学校预印本` 是任何大学作者的 arXiv 预印本（非顶会但强相关）。
6. `paper_url` 必须指向论文原文、权威论文页、官方来源页或 github 仓。
7. 标题、摘要、链接必须对应同一篇论文或同一条官方动态。
8. `date` 必须在当前日期过去 7 天内。**arXiv 条目 date 必须取自 arXiv 元数据提交日**，validate 会向 arXiv API 核对，不一致 fail。
9. `effects` 必须来自论文原文或官方来源；没有报告就写 `未报告`。
10. `tags` 必须是 1 到 8 个，取自 `data/tags.yaml` 词表，多标签。词表外的标签先加进 `data/tags.yaml` 再用。
11. `score` = `score_relevance`(0-10) + `score_contribution`(0-10)，上限 20。validate 校验加总。
12. `score_relevance` 口径：明确端侧部署 8-10 / 可迁移且作者提到端侧场景 4-7 / 纯云端无端侧考量 0-3 或排除。
13. `score_contribution` 口径：创新度高 7-10 / 常见方法或工程整合 3-6。
14. 首页展示字段必须易读：`abstract` 写「这是什么」，`effects` 写「有什么结果」，`mechanism` 写「怎么做到的」。
15. **过滤 GUI agent**：纯 GUI 自动化（屏幕点击/GUI 操作/屏幕解析）不收，除非有显著非 GUI 创新（CLI 范式、系统架构、推理优化、部署能力、安全）。
16. **排除常见方法无明显创新**：纯前缀缓存+投机解码堆砌、普通量化/剪枝、常规 benchmark，除非有显著新意，否则不收。即使中了顶会也不要，或给低分。
17. **死链检查**：`paper_url` 必须 HTTP 可访问。validate 对每个 URL 发 HEAD 请求，HEAD 失败 fallback GET；超时/网络不可达记 alive + warning 不 fail；只有 404 才 fail。单 URL 超时 5 秒。
18. **arXiv date 核对**：`paper_url` 是 arXiv 时，validate 查 arXiv API 取真实提交日，与 JSON `date` 不一致 fail（防旧论文改日期充本周）；离线 warning 跳过。
19. **跨 run 去重**：validate 读 `data/.last_run_papers.json`（publish 时写入），命中上次 run 的 id 给 warning（不 fail，因相邻两周窗口有合法重叠），提示主 agent 核实是否真有新进展。
20. **内容匹配抽检**（主 agent publish 前）：对 `source_tier=官方动态` 和 `source_tier=开源大项目` 的条目，fetch URL 核验页面内容与标题摘要对应。URL 能打开 ≠ 内容对题，对不上就丢。（07-15 教训：阶跃星辰 AI 手机新闻用了官网首页 stepfun.com 当 URL，但首页是 JS 壳不专门讲 STEPX Neo，内容对不上题——该条改走 weekly_summary 编辑性 highlight 用真实新闻链接，run 里丢弃。）
21. **标签触发词精度**：`auto_tags` 每条方向 tag 的触发词必须是该架构/方法的特定词，不许用**伞词**当唯一触发词。`neuromorphic` 是超集（含 Ising 机/事件硬件/memristor，不全是 SNN）；`spike-based`/`spiking neuron` 可能是生物学放电（神经科学）。`方向:SNN` 必须用 `spiking neural network`/`\bsnn\b`/`spikformer`/`spiking transformer`/`spiking neuron model`。通则：新增 tag 前想「会不会匹配到别的领域」（SLM=Small/Speech、quantization 量化 BERT、neuromorphic≠SNN）。

## 评分口径参考

2 维，质量判断由调研 agent 给分，不是代码硬排。最终排序靠 `source_tier` 优先级 + `score`：

- `score_relevance`（0-10）：明确端侧 8-10 / 可迁移提到端侧 4-7 / 纯云端 0-3 或排除
- `score_contribution`（0-10）：创新度高 7-10 / 常见方法工程整合 3-6
- `source_tier` 排序优先级：官方动态 > 开源大项目 > 公司项目 > 学校顶会 > 学校预印本
- `open_source`：bool facet，不打分，同等条件下开源优先

## 主 agent 发布前检查

主 agent 必须运行自动校验：

```powershell
python agent/validate_research_run.py research_runs/<run_id>.json
```

自动校验覆盖：必填字段、`source_tier` 枚举、`tags` 词表、`date` 7 天窗口、`score`=2 维之和、官方域名、github URL、vendors 非空、**死链检查**、**arXiv date 核对**、跨 run 去重 warning。

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

不能为了凑数量发布不合格内容。本周合格内容不足就少收。
