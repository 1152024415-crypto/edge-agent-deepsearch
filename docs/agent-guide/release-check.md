# 发布前检查清单（周刷新 → 部署 GitHub Pages）

> 强制「完成前」逐项勾。机械项由 `app/gates/gate_release.py` 拦（FAIL 不许部署）；
> 体验/编辑项靠人执行——assertIn/count 测不出的功能回归全在这里。

## 机械门（gate_release，FAIL 即阻断）

- [ ] `python app/gates/gate_all.py` 通过（含 gate_release）
  - __PAPERS__ 是 `{"papers":[...]}` 字典（非裸数组）；无 `window.__WEEKS__ = [` 运行时注入泄漏
  - 每个内联 paper id 有 `site/paper/<id>.html`；每个历史周有 `site/week/<label>.html`；`site/notes.html` 在
  - weekly_summary highlights 外部 URL（厂商博客/新闻）≥5，非 paper_id 复读
  - 当前周 `官方动态` ≥1；为 0 则有 `data/weeks/<label>-no-vendor.md` 逐厂证据
  - `data/github_trending_top20.json` mtime ≤7 天（>7 天 FAIL——防止 trending 区显示过期仓）
  - `data/community_radar.json` 是截至运行日的完整 7 日窗口；X/Reddit/HN/厂商论坛/开发者论坛五类覆盖齐全；静态 `__COMMUNITY__` 与源数据一致；正式 papers 没有社媒讨论 URL

## 厂商覆盖自检（防漏大新闻，07-15 阶跃星辰 AI 手机漏掉后补）

gate 拦不住「漏一个厂商」——它只检查 官方动态 ≥1，不检查覆盖了哪些厂。发布前人工扫一眼本周 `官方动态` 的 vendors 列表，确认中国头部模型厂/终端厂**至少考虑过**：

- 模型厂：Google / Microsoft / OpenAI / Anthropic / Meta / NVIDIA / Mistral / 面壁 / Qwen / **阶跃星辰 StepFun** / DeepSeek / Moonshot / Zhipu / Minimax / 百川
- 设备厂：Apple / Samsung / Huawei / Qualcomm / MediaTek / 小米 / OPPO / vivo / 荣耀
- 漏的厂商要写「本周 X 厂官方域名索引页已查，窗口内无端侧相关动态」逐厂证据（不许只写「0」断言）。**阶跃星辰这类「模型厂亲自下场造机/造端侧硬件」是端侧雷达最对题的信号，不许因为不在固定清单里就跳过**——vendor-research-guide 的厂商清单是起步集不是穷举，遇到「等」要主动扩。

## 标签精度（防 tag 把不相关论文错标，07-15 SNN 把 Ising 神经形态错标后补）

`auto_tags` 的每条方向 tag 规则，触发词必须是**该架构/方法的特定词**，不许用**伞词**当唯一触发词：

- 反例：`方向:SNN` 用裸 `neuromorphic` → Ising 机/事件硬件/memristor 都算 neuromorphic 但不是脉冲网络，被错标；裸 `spike-based`/`spiking neuron` 可能是生物学放电（神经科学），不是 SNN 架构。
- 正例：`方向:SNN` 用 `spiking neural network` / `\bsnn\b` / `spikformer` / `spiking transformer` / `spiking neuron model`——都是 SNN 架构本身。
- 通则：新增任何方向 tag 前，先想「这个触发词会不会匹配到别的领域」（SLM=Small vs Speech-Language、quantization 量化 BERT、neuromorphic≠SNN），用架构特定词，别用伞词。

## 体验项（chrome-devtools 真点，每类链接都要 200）

- [ ] 打开 `site/index.html`（或在线 URL）硬刷新
- [ ] 论文行：点击 → overlay 弹出有内容（或跳详情页 200，非 404）
- [ ] **热点链接**：点前 3 条 → 跳详情页/外部页 200，非 404
- [ ] **周切换器**：切到上周 → 上周页 166 篇渲染、`__WEEK_LABEL__` 正确；切回本周 → 114 篇
- [ ] 返回链接（详情页 `← 返回雷达`）→ 回 index 200
- [ ] 调研笔记 nav → notes.html 200
- [ ] **社区雷达**：来源覆盖卡完整，X 受限/无匹配状态如实可见；点社区讨论和一手材料 → 外部直达页可打开；来源/设备筛选只改变社区条目，不改变正式资料库数量

### 用户视角浏览（不只点链接，验内容语义——gate 拦不住语义）

- [ ] **内容全中文**：论文/开源项目/公司项目 abstract 是中文大白话吗（不是英文原文）？trending desc 是中文吗？output-contract spec 要中文，build_run_week auto-convert 截英文——必须有翻译 subagent 步骤（refresh_trending 后翻译 trending desc，build_run_week 后翻译 run abstract）。点 2-3 篇看 abstract 是中文「这是什么」大白话，英文残留 → 补翻译 subagent
- [ ] **trending 区第一仓**：repo 名是本周新建/本周高星的吗？trending 随主 agent 每次刷新跑 `agent/refresh_trending.py`（英文 desc）+ 翻译 subagent 翻中文 desc。不是本周的/英文 desc → 主 agent 补跑 `python agent/refresh_trending.py` + 翻译
- [ ] **扫官方动态列表**：中国头部模型厂/终端厂有没有明显遗漏（如本周有模型厂发端侧硬件却没收录）→ 回采集层补
- [ ] **weekly highlights 置顶**：是本周最大动态吗？链接点开是**对应新闻/官方 blog**（不是首页壳）吗？（07-15 阶跃星辰错用官网首页当新闻链接，内容对不上题）
- [ ] **社区线索边界**：每条都有中文名称、总结、价值判断、设备和核验状态；X/论坛转述没有冒充正式一手来源；发现可晋升线索时，正式周报使用回链后的一手 URL，不复用讨论 URL

## 编辑项（跟设计/上周对比）

- [ ] 重读上周 `data/weeks/<上周>.json` 的 weekly.highlights 格式（外部新闻 URL）
- [ ] 本周 highlights 是**编辑性新闻**（厂商动态/行业事件，外部 URL），不是 run top N 论文复读
- [ ] source_tier 分布合理：`官方动态`（厂商博客）非 0；`公司项目`（公司研究论文）≠ 全博客（博客归官方动态档）
- [ ] overview 是本周动态综述，不是论文列表的拼接

## 流程顺序（编辑层 ≠ 采集层）

1. 校验 `collection-manifest.json` 四来源覆盖、逐厂成功来源证据、四候选文件路径/条数/文件 SHA-256/逐记录指纹/稳定 title+URL+来源日期身份，以及 run 条目唯一且不可复用的 candidate_source + candidate_ref（先运行 `python agent/attest_candidates.py`）；服务端和发布端确认配置同一个 `EDGE_PUBLISH_TOKEN`。再采 24 个规范厂商/模型实验室动态 → `官方动态` 条目
2. 写 `data/weekly_summary.json`（从厂商新闻 + 判断，≥5 外部 URL）
3. run 论文列表是另一层，不填进 highlights

## 沉淀

- [ ] 本周新错进 `AGENTS.md` 已知教训 + `validation-rules.md`
