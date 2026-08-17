# Research Prompt — 端侧 AI Agent 论文检索

> 本文给调研 agent 参考。项目入口是根目录 `README.md`。
> agent 产出前还必须阅读 `output-contract.md` 和 `validation-rules.md`。
> 本文只约束搜集层和整理打分层的 agent 行为；主 agent 亲自筛选+评分，不全交给子 agent。

# 硬约束（不可违反）

1. **广搜集**：用 arXiv MCP + HuggingFace Daily Papers MCP + GitHub MCP + websearch 尽量多收。不限论文，技术动态/官方博客/开源大项目重大更新都要。MCP 配置和工具用法见 `docs/references/mcp-setup.md`。
2. **主题边界（广检索、少硬删）**：围绕端侧 AI，明确端侧/移动/嵌入式/边缘/NPU/MCU/端侧 Agent 必收；属于 AI 推理与部署技术栈、对资源受限设备有直接迁移价值的量化、KV cache、投机解码、小模型、稀疏注意力、高效推理、运行时、serving、agent memory、工具调用等也收，不要求原文必须出现 `on-device`。通用云端 serving 可收但标 `方向:云端serving` 并给较低相关度，通常不推荐。只剔除完全无关、关键词歧义碰撞、越窗、来源不可信、链接不匹配和重复项。
3. **过滤 GUI agent**：纯 GUI 自动化（手机/桌面 GUI 操作、屏幕点击、屏幕解析）不收，除非有显著非 GUI 创新（CLI 范式、系统架构、推理优化、部署能力、安全）。端侧 GUI 自动化方向已饱和，过滤掉。
4. **常见方法保留但低分**：纯前缀缓存+投机解码组合、普通量化/剪枝、常规 benchmark 只要仍属于 AI 推理/部署或端侧技术栈就进入完整收录，`score_contribution` 给 1-5，通常不推荐。不得用“创新一般”当成搜集删除条件；推荐层负责让用户优先看真正重要的内容。
5. **找不到官方 URL 就丢弃**：不许拼凑、推测或编造 URL。`source_tier=官方动态` 必须命中官方域名白名单；`source_tier=开源大项目` 必须是 github.com 白名单大项目仓；论文必须命中允许的论文链接域名。拿不准的条目直接丢弃。
6. **date 必须取自元数据**：arXiv 新稿写 `arxiv_date_basis=submitted` 并取提交日；更新扫描召回的旧稿写 `updated`，但只有主 agent 对比旧版、确认实验/方法/数据/代码/结论有实质变化并填写中文 `arxiv_revision_note` 后才能进入 run。仅改排版或摘要无实质变化必须丢弃。HF 条目取 HF 发布日；不许为塞进窗口改日期。
7. **优先级（高→低，对应 source_tier）**：
   1. `官方动态`：24 个规范厂商/模型实验室官方来源（Apple/Samsung/Huawei/Qualcomm/MediaTek/Xiaomi/OPPO/vivo/Honor/Google/Microsoft/OpenAI/Anthropic/Meta/NVIDIA/Mistral/ModelBest/Qwen/StepFun/DeepSeek/Moonshot/Zhipu/MiniMax/Baichuan）
   2. `开源大项目`：业界认可大项目重大 release（见 `docs/references/big-projects-whitelist.md`，如 vLLM/SGLang/llama.cpp/ExecuTorch/MLC-LLM/ADK/TensorRT/MediaPipe 等）
   3. `公司项目`：快手/字节/腾讯/百度/美团/京东/拼多多/网易等公司独立或主导的研究（arXiv 或顶会，affiliation 命中公司，`vendors` + 权威 `affiliation_evidence_url` 必填）；只接受 arXiv PDF、OpenReview/Scholar 或认可论文出版页，GitHub repo/release 不是机构证据。证据未核实前先按 `学校预印本` 收录，不删除
   4. `学校顶会`：任何高校独立发表顶会顶刊
   5. `学校预印本`：任何大学作者发的 arXiv 预印本（非顶会但主题强相关），排序最低。新鲜端侧工作多先上 arXiv，这一档保证雷达不漏最新真东西。
8. **学校项目门槛（不限名校）**：`学校顶会` = 任何大学发表在顶会顶刊（NeurIPS/ICML/ICLR/MobiSys/SenSys/ASPLOS/ACL/CVPR/ICCV/EMNLP/AAAI/IJCAI/TPAMI/TNNLS/ToN）。`学校预印本` = 任何大学的 arXiv 预印本（非顶会但强相关）。**不再卡中美名校**——任何正规大学都收，只挡纯无机构署名和垃圾。公司项目 arXiv 或顶会均可。
9. **vendors/affiliation 必须有证据来源**：标注公司 affiliation 必须附证据（OpenReview author profile / Google Scholar / 论文 PDF 机构署名），`score_reason` 写明依据。不许只凭作者名、标题、摘要中的模型名或平台名推测；自动脚本只能读取明确 affiliation/机构字段。未确认的一律先标 `学校预印本`。
10. **2 维评分**：搜集 agent 可给结构化初值，最终分数必须由主 agent 阅读来源后确认。
    - `score_relevance`（0-10）：明确端侧部署 8-10 / 端侧技术栈或直接可迁移工作 4-7 / 仅宽泛云端关联 1-3 / 完全无关排除
    - `score_contribution`（0-10）：创新度高 7-10 / 常见方法或工程整合 1-6。低分不等于删除
    - `score` = 两维之和（0-20），排序靠 `source_tier` 优先级 + `score`
11. **open_source**：bool，有开源仓库/数据集/模型开源 true，否则 false。同等条件下开源优先。
12. **多标签 tags**：每条 1-8 个标签，格式 `维度:值`（如 `方向:量化`/`硬件:NPU`/`模型:Llama`），取自 `data/tags.yaml` 词表（人读版 `docs/references/tag-taxonomy.md`，4 维：方向/应用/硬件/模型）。`方向:端侧agent`是经原文核实的语义标签，不能因标题含 agent/mobile/edge 自动添加；普通端侧 VLM 量化部署应标`方向:多模态`+`方向:量化`+`方向:编译部署`，只有设备端确实运行规划、记忆、工具调用或行动闭环时才加`方向:端侧agent`。方向/应用/硬件为受控词表，模型为半自由。
13. **首页字段人类可读**：`abstract`/`effects`/`mechanism` 用中文短句给人看（这是什么/有什么结果/怎么做到的），每段 1-2 句，避免论文腔。`abstract` 不得保留英文原文；`effects` 必须来自原文，没有报告写 `未报告`，不许编造。读者字段禁止出现 `auto-converted`、`votes=`、`待核实`、`精修待补` 等内部流程文字。
14. **推荐必须由主 agent 策展**：搜集子 agent 和自动脚本对所有条目一律写 `title_zh=""`、`recommendation="纳入"`、`recommendation_reason=""`、`edge_agent_scope="待核实"`、`edge_agent_evidence=""`，不许仅因标题命中关键词自动推荐。主 agent 读过来源后再选值得优先看的条目并完成端侧 Agent 分类。
15. **官方发布日期必须来自正文**：sitemap 的 `lastmod`、搜索引擎抓取时间和页面底部更新时间只能用于发现，不得直接当候选发布日期。正式候选必须在具体官方直达页正文核到发布日期；旧页面模板更新、地区/语言镜像和同文重复页不进本周。
16. **相邻技术必须是工作主贡献**：`multi-agent system`、`distillation`、`serving` 等词只在摘要深处作为基线或背景出现时，不足以入库；标题或核心方法必须明确贡献于 AI 推理、部署、Agent 运行时或资源受限技术栈。真正端侧 Agent 还要同时出现设备语境和规划/记忆/工具/行动闭环证据。
17. **Trending 新仓先审计再晋升**：未知小仓先作为线索保留，不得自动伪装成开源大项目。只有主 agent 核对创建时间、活跃度/影响力、代码与设备执行闭环后，才能把极少数新项目加入白名单；白名单变更必须配回归测试。
15. **真正端侧 Agent 是最高优先级**：必须同时有 Agent 闭环（规划/记忆/工具/环境交互/行动之一）和设备端执行证据。关键闭环至少部分实际运行在手机、PC、机器人、汽车或 IoT 上；端云协同时终端必须承担时延敏感闭环。手机优先、PC 次之、其他端侧设备仍完整收录并全部推荐。分类为`手机`/`PC`/`其他端侧`时，必须填写中文`edge_agent_evidence`、加`方向:端侧agent`、给`score_relevance` 8-10并设置`推荐`。普通端侧推理/量化/缓存/检测、手机仅作云端入口、纯云端 Agent 训练基础设施均写`非端侧Agent`。
16. **不凑数**：本周合格内容不足就少收，不拿学术充大厂，不拿不确定链接凑数。

# 搜集（分层，详见 `docs/harness.md` 第 11 节 + `docs/references/mcp-setup.md`）

三个 MCP + websearch 互补。**不定硬数量目标或上限**——检索层尽量多收，只有硬边界失败才删除；“是否值得优先看”由主 agent 推荐决定。四类来源必须同时更新 `research_runs/collection-manifest.json`，覆盖不完整时不得组装或发布。

## arXiv MCP（`search_papers`，全量结构化搜索，主力）
多轮 query，`sort_by="submittedDate"`，窗口由运行日动态计算为含当日的最近 7 个自然日。大类扫描必须覆盖 `cs.AI/cs.LG/cs.CL/cs.RO/cs.AR/cs.DC/cs.ET/cs.SY/cs.NE` 并分页，不能只取每个 query 前 100 条。建议 query：
1. `"on-device agent"` 2. `"edge computing agent"` 3. `"mobile LLM inference"` 4. `"NPU agent"` 5. `"agent memory edge"` 6. `"tool use edge device"` 7. `"federated agent"` 8. `"quantization agent mobile"` 9. `"spiking neural network"`（SNN/脉冲网络/neuromorphic，端侧低功耗相邻方向）
**自适应**：某 query 返回过少就自行放宽/换词（去掉引号精确匹配、换同义词、扩 category、放宽到 `cs.ET/cs.DC` 等），不必死守固定 query。正常返回多就继续。
取每篇的 submittedDate 作为 `date`（不许自填）。

## HuggingFace Daily Papers MCP（`get_papers_by_date`，社区精选）
窗口内 7 个日期每天调一次 `get_papers_by_date(date=YYYY-MM-DD)`；votes 只用于排序参考，不能作为删除门槛。把 `dates_checked` 全量写入 collection manifest；某天 0 条也必须记录为已检查。

## GitHub MCP（开源大项目 release，端侧优先）
搜 `docs/references/big-projects-whitelist.md` 内每个有明确仓址的大项目最近 7 天 release/重大 commit。GitHub Trending 与白名单 release 是两项独立任务，分别在 manifest 写 `trending_checked` 和 `release_projects_checked`，不能用 Trending 刷新冒充 release 已检查。

### 模型厂博客优先发布（易漏，必查）
DeepSeek / Moonshot / Zhipu / Minimax / 百川 等**模型实验室经常先发博客 + GitHub 仓 + HF checkpoints，不上 arXiv**（典型：DeepSeek 的 DeepGEMM/FlashMLA/DeepEP/DSpark）。这类工作 arXiv MCP 搜不到，必须额外查：
- 该厂 GitHub org 的**近期新建仓 / 重大 commit**（不只看 release tag——DSpark 就无 release tag，只有 commit + 仓内 PDF）。
- 该厂官方博客域名（DeepSeek `deepseek.com` / `api-docs.deepseek.com` 已加进官方域名白名单）。
- HF 上该厂 org（`deepseek-ai` 等）近期上传的模型/数据集。
- websearch 补查该厂名 + 投机解码/量化/serving 等技术词（别只搜端侧关键词，会漏 DSpark 这种通用推理加速）。

## websearch（大厂官方博客）
逐一检查 24 个规范厂商/模型实验室官方来源，命中官方域名才算；即使 0 命中也把厂商写入 manifest 的 `vendors_checked` 并保留逐厂证据。各厂商方法见 `vendor-research-guide.md`。

## 社区雷达（独立编辑产物，不进入正式 run）

正式候选完成后，主 agent 另行检索最近 7 个自然日的 X、Bluesky、Reddit、Hacker News、Mastodon、GitHub Discussions、Hugging Face（Discussions/Models/Spaces）、YouTube / Bilibili 和厂商论坛，写入 `data/community_radar.json`。目标是补充真实设备反馈、新项目苗头和社区争议，不降低正式周报的来源标准：

- 九类来源必须逐一留下 `found` / `no_match` / `limited` / `unavailable` 与中文说明，0 条也不能静默跳过。视频只收官方频道或可回链一手项目的演示。
- X 只接受无需登录即可打开、可核验发布时间的公开原帖；搜索索引不足时标 `limited`，不得把 Reddit 转述或搜索摘要改写成 X 原帖。
- 每条线索必须有讨论直达 URL、`published_at`、中文 `title_zh` / `summary_zh` / `why_it_matters`、`device_scope`（手机 / PC / 其他端侧 / 通用技术）、topic 和 verification（仅线索 / 已回链原始材料 / 已进入正式周报）。
- 排序手机 > PC > 其他端侧 > 通用技术；相关但价值一般的线索仍可列出，价值判断负责用户注意力。
- 社区链接不得写进正式 run 的 `paper_url`。只有找到一手论文、官方发布或通过审计的大项目来源，并重新满足正式来源、日期和内容契约后，才可单独生成正式条目。

# 检索式参考

- **大厂官方优先检索式**：`(site:apple.com OR site:google.com OR site:microsoft.com OR site:openai.com OR site:anthropic.com OR site:meta.com OR site:samsung.com OR site:huawei.com OR site:qualcomm.com OR site:mediatek.com OR site:mi.com OR site:oppo.com OR site:vivo.com OR site:honor.com OR site:mistral.ai OR site:qwenlm.github.io) AND ("on-device" OR "edge" OR "mobile" OR "NPU" OR "local") AND ("agent" OR "assistant")`
- **基础检索式**：`("mobile agent" OR "edge agent" OR "embedded agent" OR "agentic AI") AND ("on-device" OR "edge computing" OR "resource-constrained")`
- **技术深化检索式**：`("LLM" OR "VLM") AND ("mobile" OR "edge") AND ("quantization" OR "pruning" OR "distillation" OR "efficient inference") AND ("agent" OR "autonomous")`
- **厂商特定**：`("Apple Intelligence" OR "Gemini Nano" OR "Phi-3" OR "Llama 3.2" OR "MiniCPM" OR "Qwen2.5") AND ("on-device" OR "edge" OR "mobile")`
- **评测基准**：`("AndroidWorld" OR "Mobile-Env" OR "AIoTBench" OR "MLPerf Tiny") AND ("agent")`

# 输出

按 `docs/agent-guide/output-contract.md` 的 JSON 结构输出，不要输出 markdown 表格、不要 1-5 分评分。每条含：`id`/`title`/`title_zh`/`abstract`/`effects`/`mechanism`/`paper_url`/`date`/`score`+`score_relevance`+`score_contribution`/`source_tier`/`open_source`/`tags`/`edge_agent_scope`/`edge_agent_evidence`/`score_reason`/`authors`/`vendors`/`venue`/`recommendation`/`recommendation_reason`。搜集子 agent 对新字段统一输出`待核实`和空证据，只产 JSON，不改代码、网页、服务器。

同时更新 `research_runs/collection-manifest.json`。结构至少包含：

```json
{
  "window_start": "YYYY-MM-DD",
  "window_end": "YYYY-MM-DD",
  "sources": {
    "arxiv": {"status": "complete", "candidate_count": 0, "artifact_path": "...", "artifact_sha256": "...", "candidate_refs": [], "candidate_identity_refs": [], "candidate_lineage": {}, "queries_completed": [], "pages_fetched": 1},
    "huggingface": {"status": "complete", "candidate_count": 0, "artifact_path": "...", "artifact_sha256": "...", "candidate_refs": [], "candidate_identity_refs": [], "candidate_lineage": {}, "dates_checked": []},
    "github": {"status": "complete", "candidate_count": 0, "artifact_path": "...", "artifact_sha256": "...", "candidate_refs": [], "candidate_identity_refs": [], "candidate_lineage": {}, "release_projects_checked": [], "trending_checked": true},
    "vendors": {"status": "complete", "candidate_count": 0, "artifact_path": "...", "artifact_sha256": "...", "candidate_refs": [], "candidate_identity_refs": [], "candidate_lineage": {}, "vendors_checked": [], "vendor_checks": {"Apple": {"status": "found", "sources_succeeded": ["https://..."]}}}
  }
}
```

数组必须覆盖 `agent/research_collection.py` 中的规范集合。不能仅写 `status=complete`：arXiv 命中分页上限、某厂没有成功访问的官方来源、缺少具体日期/query/项目/厂商都会被拦截。四个最终候选 JSON 写完后运行 `python agent/attest_candidates.py`，由脚本填写并绑定 `candidate_count`、`artifact_path`、`artifact_sha256`、逐记录 `candidate_refs` 与稳定 title+URL+来源日期身份映射；转换器必须把唯一的 `candidate_source` + `candidate_ref` 带入 run，同一候选不能复用，之后再改候选文件必须重新证明。GitHub 候选只允许白名单大项目，固定写为 `source_tier=开源大项目`，不能把未知小仓改标成学校或公司项目。

# 关键技术分支（搜词与打标参考）

- **核心架构**：Agentic AI / Mobile-Embedded Agent / Cognitive Edge / Multi-Agent on Edge
- **轻量化**：量化(GPTQ/AWQ/KV量化) / 剪枝稀疏(SparseGPT/Wanda) / 蒸馏 / 高效注意力 / 投机解码(Medusa/EAGLE)
- **脉冲/神经形态**：SNN(脉冲神经网络) / neuromorphic / 事件驱动低功耗推理（Loihi/SpiNNaker/TrueNorth/天机），与端侧低功耗相邻
- **运行时自适应**：测试时自适应 / 动态多模态融合 / 能耗感知 / 端云协同卸载
- **感知记忆规划**：VLM 端侧部署 / 记忆压缩 / 任务分解 / 工具调用
- **评测硬件**：AndroidWorld/Mobile-Env/AIoTBench/MLPerf Tiny / NPU-DSP-GPU 编译(MLC-LLM/llama.cpp/ONNX Runtime)
- **厂商技术**：Apple Intelligence/CoreAI / Samsung Gauss/Galaxy AI / Huawei HarmonyOS AI/Pangu/HiAI/Ascend / Qualcomm AI Hub/Hexagon / MediaTek NeuroPilot / 小米 HyperAI/MiLM/AISP / OPPO AndesGPT / vivo BlueLM / 荣耀 YOYO / Google Gemini Nano/MediaPipe / Microsoft Phi/Copilot Runtime / Meta Llama / Mistral Ministral / 面壁 MiniCPM / Qwen 端侧

打标时对照 `data/tags.yaml`（4 维 dim:val 格式：`方向:值` / `应用:值` / `硬件:值` / `模型:值`），上述分支对应 `方向:端侧agent`/`方向:量化`/`方向:剪枝稀疏`/`方向:蒸馏`/`方向:投机解码`/`方向:KV cache`/`方向:推理框架`/`方向:调度服务`/`方向:云端serving`/`方向:多模态`/`方向:记忆`/`方向:工具调用`/`方向:规划推理`/`方向:模型架构`/`方向:MoE`/`方向:高效推理`/`方向:稀疏注意力`/`方向:高效注意力`/`方向:测试时自适应`/`方向:端侧训练`/`方向:端云协同`/`方向:能耗功耗`/`方向:编译部署`/`方向:评测基准`/`方向:安全隐私`/`方向:联邦学习`/`方向:SNN`；硬件维 `硬件:NPU`/`硬件:GPU`/`硬件:Jetson`/`硬件:神经形态` 等；应用维 `应用:OCR`/`应用:语音`/`应用:RAG` 等；模型维 `模型:Llama`/`模型:Qwen` 等。
