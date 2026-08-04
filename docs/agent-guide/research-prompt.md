# Research Prompt — 端侧 AI Agent 论文检索

> 本文给调研 agent 参考。项目入口是根目录 `README.md`。
> agent 产出前还必须阅读 `output-contract.md` 和 `validation-rules.md`。
> 本文只约束搜集层和整理打分层的 agent 行为；主 agent 亲自筛选+评分，不全交给子 agent。

# 硬约束（不可违反）

1. **广搜集**：用 arXiv MCP + HuggingFace Daily Papers MCP + GitHub MCP + websearch 尽量多收。不限论文，技术动态/官方博客/开源大项目重大更新都要。MCP 配置和工具用法见 `docs/references/mcp-setup.md`。
2. **主题边界（放宽 B 档）**：围绕端侧 AI。**属于端侧推理/部署技术栈即收，不要求论文显式写 "on-device"**——量化、KV cache、投机解码、小模型、稀疏注意力、高效推理、agent memory、工具调用、移动/IoT 部署都算。纯数据中心/云端 serving（多模型 serving、集群容错、大模型 server 推理）也收，但用 `云端serving` tag 单独标注分类，不和端侧混。**关键字过匹配要剔除**：SLM 既指 Small 也指 Speech-Language Model、quantization 会匹配任何量化 BERT 论文——看论文实际主题，丢弃完全无关的（医疗/密码学/人脸对话/训练理论/HPO 自动化等），保留小模型/高效推理应用到语音/嵌入等端侧相邻工作。
3. **过滤 GUI agent**：纯 GUI 自动化（手机/桌面 GUI 操作、屏幕点击、屏幕解析）不收，除非有显著非 GUI 创新（CLI 范式、系统架构、推理优化、部署能力、安全）。端侧 GUI 自动化方向已饱和，过滤掉。
4. **排除常见方法无明显创新**：纯前缀缓存+投机解码堆砌、普通量化/剪枝、常规 benchmark，除非有显著新意，否则不收。即使中了顶会也不要，或给低分。
5. **找不到官方 URL 就丢弃**：不许拼凑、推测或编造 URL。`source_tier=官方动态` 必须命中官方域名白名单；`source_tier=开源大项目` 必须是 github.com 白名单大项目仓；论文必须命中允许的论文链接域名。拿不准的条目直接丢弃。
6. **date 必须取自元数据**：arXiv 条目 date 取 arXiv 提交日，HF 条目取 HF 发布日。validate 会向 arXiv API 核对，不许为塞进 7 天窗口改日期。时间窗口是当前日期过去 7 天。
7. **优先级（高→低，对应 source_tier）**：
   1. `官方动态`：18 家设备/模型大厂官方博客/产品发布（Apple/Google/Microsoft/OpenAI/Anthropic/Meta/NVIDIA/Samsung/Huawei/Qualcomm/MediaTek/小米/OPPO/vivo/荣耀/Qwen/Mistral/面壁）
   2. `开源大项目`：业界认可大项目重大 release（见 `docs/references/big-projects-whitelist.md`，如 vLLM/SGLang/llama.cpp/ExecuTorch/MLC-LLM/ADK/TensorRT/MediaPipe 等）
   3. `公司项目`：快手/字节/腾讯/百度/美团/京东/拼多多/网易等公司独立或主导的研究（arXiv 或顶会，affiliation 命中公司，`vendors` 必填+证据）
   4. `学校顶会`：任何高校独立发表顶会顶刊
   5. `学校预印本`：任何大学作者发的 arXiv 预印本（非顶会但主题强相关），排序最低。新鲜端侧工作多先上 arXiv，这一档保证雷达不漏最新真东西。
8. **学校项目门槛（不限名校）**：`学校顶会` = 任何大学发表在顶会顶刊（NeurIPS/ICML/ICLR/MobiSys/SenSys/ASPLOS/ACL/CVPR/ICCV/EMNLP/AAAI/IJCAI/TPAMI/TNNLS/ToN）。`学校预印本` = 任何大学的 arXiv 预印本（非顶会但强相关）。**不再卡中美名校**——任何正规大学都收，只挡纯无机构署名和垃圾。公司项目 arXiv 或顶会均可。
9. **vendors/affiliation 必须有证据来源**：标注公司 affiliation 必须附证据（OpenReview author profile / Google Scholar / 论文 PDF 机构署名），`score_reason` 写明依据（如「Zhixiang Chi OpenReview profile 显示 Huawei Technologies Ltd」）。不许只凭作者名推测。（当前 run 的 affiliation 核实 defer：未识别公司的论文一律标 `学校预印本`，公司论文待识别——文档注明此现状。）
10. **2 维评分**（质量判断由调研 agent 给分）：
    - `score_relevance`（0-10）：明确端侧部署 8-10 / 端侧技术栈但非显式端侧 5-7 / 云端 serving 但技术可参考 3-5 / 完全无关 0-2 或排除
    - `score_contribution`（0-10）：创新度高 7-10 / 常见方法或工程整合 3-6
    - `score` = 两维之和（0-20），排序靠 `source_tier` 优先级 + `score`
11. **open_source**：bool，有开源仓库/数据集/模型开源 true，否则 false。同等条件下开源优先。
12. **多标签 tags**：每条 1-8 个标签，格式 `维度:值`（如 `方向:端侧agent`/`硬件:NPU`/`模型:Llama`），取自 `data/tags.yaml` 词表（人读版 `docs/references/tag-taxonomy.md`，4 维：方向/应用/硬件/模型），多标签，一个工作可挂多个（如「端侧 VLM 量化部署」挂 `方向:端侧agent`+`方向:多模态`+`方向:量化`+`方向:编译部署`）。方向/应用/硬件为受控词表（必须命中），模型为半自由（starter 列表，新模型可提议后加入）。词表外的标签先加进 `data/tags.yaml` 再用，不许私自用词表外的标签。
13. **首页字段人类可读**：`abstract`/`effects`/`mechanism` 用中文短句给人看（这是什么/有什么结果/怎么做到的），每段 1-2 句，避免论文腔。`abstract` 不得保留英文原文；`effects` 必须来自原文，没有报告写 `未报告`，不许编造。读者字段禁止出现 `auto-converted`、`votes=`、`待核实`、`精修待补` 等内部流程文字。
14. **推荐必须由主 agent 策展**：搜集子 agent 和自动脚本对所有条目一律写 `recommendation="纳入"`、`recommendation_reason=""`，不许仅因标题命中 on-device/KV cache/量化等关键词自动推荐。主 agent 读过来源后再选值得优先看的条目，数量按本周质量决定；每条推荐必须补一句中文 `recommendation_reason`，具体说明为什么值得优先看。
15. **不凑数**：本周合格内容不足就少收，不拿学术充大厂，不拿不确定链接凑数。

# 搜集（分层，详见 `docs/harness.md` 第 11 节 + `docs/references/mcp-setup.md`）

三个 MCP + websearch 互补。**不定硬数量目标**——有多少合格就收多少，列表只是轻量罗列（不写详细分析），可以多收一些。子 agent 尽量广搜集，主 agent 筛选+评分+打标后全量发布。

## arXiv MCP（`search_papers`，全量结构化搜索，主力）
多轮 query，`sort_by="submittedDate"`，`date_from`=7天前，`categories=[cs.AI,cs.LG,cs.CL,cs.RO]`。建议 query：
1. `"on-device agent"` 2. `"edge computing agent"` 3. `"mobile LLM inference"` 4. `"NPU agent"` 5. `"agent memory edge"` 6. `"tool use edge device"` 7. `"federated agent"` 8. `"quantization agent mobile"` 9. `"spiking neural network"`（SNN/脉冲网络/neuromorphic，端侧低功耗相邻方向）
**自适应**：某 query 返回过少就自行放宽/换词（去掉引号精确匹配、换同义词、扩 category、放宽到 `cs.ET/cs.DC` 等），不必死守固定 query。正常返回多就继续。
取每篇的 submittedDate 作为 `date`（不许自填）。

## HuggingFace Daily Papers MCP（`get_papers_by_date`，社区精选）
过去 7 天每天调一次 `get_papers_by_date(date=YYYY-MM-DD)`，筛标题/摘要含端侧关键词 + votes 高的。和 arXiv 互补（HF 精选质量高、arXiv 全量覆盖广）。

## GitHub MCP（开源大项目 release，端侧优先）
搜 `docs/references/big-projects-whitelist.md` 内大项目的最近 7 天 release/重大 commit。**优先端侧推理/端侧 agent 相关项目（Google ADK、nanoagent、ExecuTorch、MLC-LLM、llama.cpp 等端侧部署框架）；vLLM/SGLang/TensorRT 等通用云端推理框架次要，有重大端侧相关更新也可搜。** 只收白名单大项目，非白名单小仓不收。

### 模型厂博客优先发布（易漏，必查）
DeepSeek / Moonshot / Zhipu / Minimax / 百川 等**模型实验室经常先发博客 + GitHub 仓 + HF checkpoints，不上 arXiv**（典型：DeepSeek 的 DeepGEMM/FlashMLA/DeepEP/DSpark）。这类工作 arXiv MCP 搜不到，必须额外查：
- 该厂 GitHub org 的**近期新建仓 / 重大 commit**（不只看 release tag——DSpark 就无 release tag，只有 commit + 仓内 PDF）。
- 该厂官方博客域名（DeepSeek `deepseek.com` / `api-docs.deepseek.com` 已加进官方域名白名单）。
- HF 上该厂 org（`deepseek-ai` 等）近期上传的模型/数据集。
- websearch 补查该厂名 + 投机解码/量化/serving 等技术词（别只搜端侧关键词，会漏 DSpark 这种通用推理加速）。

## websearch（大厂官方博客）
fetch 18 家大厂官方博客 URL 找过去 7 天动态，命中官方域名才算。各厂商官方 URL / websearch 关键词 / arXiv affiliation 搜法见 `docs/references/vendor-research-guide.md`。

# 检索式参考

- **大厂官方优先检索式**：`(site:apple.com OR site:google.com OR site:microsoft.com OR site:openai.com OR site:anthropic.com OR site:meta.com OR site:samsung.com OR site:huawei.com OR site:qualcomm.com OR site:mediatek.com OR site:mi.com OR site:oppo.com OR site:vivo.com OR site:honor.com OR site:mistral.ai OR site:qwenlm.github.io) AND ("on-device" OR "edge" OR "mobile" OR "NPU" OR "local") AND ("agent" OR "assistant")`
- **基础检索式**：`("mobile agent" OR "edge agent" OR "embedded agent" OR "agentic AI") AND ("on-device" OR "edge computing" OR "resource-constrained")`
- **技术深化检索式**：`("LLM" OR "VLM") AND ("mobile" OR "edge") AND ("quantization" OR "pruning" OR "distillation" OR "efficient inference") AND ("agent" OR "autonomous")`
- **厂商特定**：`("Apple Intelligence" OR "Gemini Nano" OR "Phi-3" OR "Llama 3.2" OR "MiniCPM" OR "Qwen2.5") AND ("on-device" OR "edge" OR "mobile")`
- **评测基准**：`("AndroidWorld" OR "Mobile-Env" OR "AIoTBench" OR "MLPerf Tiny") AND ("agent")`

# 输出

按 `docs/agent-guide/output-contract.md` 的 JSON 结构输出，不要输出 markdown 表格、不要 1-5 分评分。每条含：`id`/`title`/`abstract`/`effects`/`mechanism`/`paper_url`/`date`/`score`+`score_relevance`+`score_contribution`/`source_tier`/`open_source`/`tags`/`score_reason`/`authors`/`vendors`/`venue`/`recommendation`/`recommendation_reason`。搜集子 agent 统一输出 `recommendation="纳入"`、`recommendation_reason=""`，只产 JSON，不改代码、网页、服务器。

# 关键技术分支（搜词与打标参考）

- **核心架构**：Agentic AI / Mobile-Embedded Agent / Cognitive Edge / Multi-Agent on Edge
- **轻量化**：量化(GPTQ/AWQ/KV量化) / 剪枝稀疏(SparseGPT/Wanda) / 蒸馏 / 高效注意力 / 投机解码(Medusa/EAGLE)
- **脉冲/神经形态**：SNN(脉冲神经网络) / neuromorphic / 事件驱动低功耗推理（Loihi/SpiNNaker/TrueNorth/天机），与端侧低功耗相邻
- **运行时自适应**：测试时自适应 / 动态多模态融合 / 能耗感知 / 端云协同卸载
- **感知记忆规划**：VLM 端侧部署 / 记忆压缩 / 任务分解 / 工具调用
- **评测硬件**：AndroidWorld/Mobile-Env/AIoTBench/MLPerf Tiny / NPU-DSP-GPU 编译(MLC-LLM/llama.cpp/ONNX Runtime)
- **厂商技术**：Apple Intelligence/CoreAI / Samsung Gauss/Galaxy AI / Huawei HarmonyOS AI/Pangu/HiAI/Ascend / Qualcomm AI Hub/Hexagon / MediaTek NeuroPilot / 小米 HyperAI/MiLM/AISP / OPPO AndesGPT / vivo BlueLM / 荣耀 YOYO / Google Gemini Nano/MediaPipe / Microsoft Phi/Copilot Runtime / Meta Llama / Mistral Ministral / 面壁 MiniCPM / Qwen 端侧

打标时对照 `data/tags.yaml`（4 维 dim:val 格式：`方向:值` / `应用:值` / `硬件:值` / `模型:值`），上述分支对应 `方向:端侧agent`/`方向:量化`/`方向:剪枝稀疏`/`方向:蒸馏`/`方向:投机解码`/`方向:KV cache`/`方向:推理框架`/`方向:调度服务`/`方向:云端serving`/`方向:多模态`/`方向:记忆`/`方向:工具调用`/`方向:规划推理`/`方向:模型架构`/`方向:MoE`/`方向:高效推理`/`方向:稀疏注意力`/`方向:高效注意力`/`方向:测试时自适应`/`方向:端侧训练`/`方向:端云协同`/`方向:能耗功耗`/`方向:编译部署`/`方向:评测基准`/`方向:安全隐私`/`方向:联邦学习`/`方向:SNN`；硬件维 `硬件:NPU`/`硬件:GPU`/`硬件:Jetson`/`硬件:神经形态` 等；应用维 `应用:OCR`/`应用:语音`/`应用:RAG` 等；模型维 `模型:Llama`/`模型:Qwen` 等。
