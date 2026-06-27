# Research Prompt — 端侧 AI Agent 论文检索参考

> 本文只给调研 agent 参考。项目入口是根目录 `README.md`。
> agent 产出前还必须阅读 `output-contract.md` 和 `validation-rules.md`。

# 硬约束（不可违反）

1. **abstract / effects / mechanism 必须用大白话中文整理版**：不搬论文摘要原文，用给人看的短句重写。`abstract` 回答「这是什么」，`effects` 回答「有什么结果」，`mechanism` 回答「怎么做到的」。每段 1-2 句，避免论文腔，详细技术分解放 wiki，不塞首页字段。
2. **找不到官方 URL 就丢弃该条**：不许拼凑、推测或编造 URL。论文必须命中允许的论文链接域名，大厂官方条目必须命中官方域名白名单。链接拿不准的条目直接丢弃，不进入 `papers[]`。
3. **大厂官方要多搜**：不只搜 17 家设备/模型厂，也要搜中国互联网公司（快手/字节/腾讯/百度/美团/京东/拼多多/网易）的官方技术博客、GitHub、arXiv affiliation。大厂官方动态是重点，要主动深搜各厂商官网博客（见 vendor-research-guide.md 全部 URL）。时间窗口放宽到**过去 14 天**（2 周），多搜源多收。
4. **优先级（高→低）**：
   1. 大厂官方动态（17 家设备/模型厂官方博客/产品发布，`is_major_vendor_official=true`）
   2. **公司项目**（快手/字节/腾讯/百度/美团/京东/拼多多/网易等公司独立或主导的研究，arXiv 或顶会，affiliation 命中公司）。优先级非常高，排序仅低于大厂官方。
   3. **公司+学校合作顶会项目**（公司联合高校发表顶会）
   4. **学校顶会项目**（高校独立发表顶会顶刊）
5. **至少顶会门槛 + 中美名校限制**：学校项目（无公司 affiliation）必须同时满足：(a) 发表在顶会顶刊（NeurIPS / ICML / ICLR / MobiSys / SenSys / ASPLOS / ACL / CVPR / ICCV / EMNLP / AAAI / IJCAI / TPAMI / TNNLS / ToN）；(b) 作者来自**中美名校**（中国：清华/北大/上交/浙大/中科大/复旦/南大/港中文/港科大/港大/中科院；美国：MIT/Stanford/CMU/Berkeley/Princeton/Yale/Cornell/UIUC/UCSD/UCLA/Georgia Tech/Columbia）。其他地区学校或非名校的纯 arXiv 预印本不收。公司项目不限学校，arXiv 或顶会均可。
6. **排除常见方法无明显创新**：纯前缀缓存+投机解码堆砌、普通量化/剪枝、常规 benchmark，除非有显著新意，否则不收。这种论文即使中了顶会也不要，或给低分。
7. **评分口径**（6 维，质量判断由调研 agent 给分，不是代码硬排）：
    - `score_vendor`（0-25）：大厂官方 20-25；公司项目 15-20；公司+学校合作顶会 10-15；学校顶会 5-10；纯学术无公司 3-8
    - `score_contribution`（0-15）：创新度高 12-15；常见方法/工程整合 5-10
    - `score_open`（0-10）：有开源仓库/数据集/模型开源 5-10；不开源 0
    - `score_relevance`(0-30) / `score_quality`(0-15) / `score_recency`(0-5) 按主题契合度/信息质量/时效给
    - 6 维加总 = score（0-100），最终排序靠 score 体现
8. **vendors 字段**：公司项目必填公司名（如 `Kuaishou` / `ByteDance` / `Tencent` / `Baidu` / `Meituan` / `JD` / `Pinduoduo` / `Netease`）。
9. **vendors/affiliation 必须有证据来源**：标注公司 affiliation 时，必须附证据（OpenReview author profile / Google Scholar 个人页 / 论文 PDF 机构署名），`score_reason` 写明依据（如「Zhixiang Chi OpenReview profile 显示 Huawei Technologies Ltd，huawei.com 邮箱确认」）。不许只凭作者名推测。
10. **过滤 GUI agent**：纯 GUI agent 操作类（手机/桌面 GUI 自动化、屏幕点击操作、屏幕解析）不收，除非有显著非 GUI 创新（如 CLI 范式、系统架构、推理优化、部署能力）。端侧 GUI 自动化方向已饱和，过滤掉。保留非 GUI 的端侧 agent（推理优化/部署/记忆/工具调用/系统架构/安全/能耗）。
11. **开源评分**：`score_open`（0-10），有开源仓库/数据集/模型开源给 5-10，不开源 0。开源是高分项，同等条件下开源论文优先。
12. **6 维分数**：`score` = `score_relevance`(30) + `score_vendor`(25) + `score_contribution`(15) + `score_quality`(15) + `score_recency`(5) + `score_open`(10) = 100。6 维加总必须等于 score。

# arXiv MCP 搜索（优先使用）

本项目配置了 arXiv MCP Server（blazickjp/arxiv-mcp-server），提供以下工具：
- `search_papers`：按关键词搜索 arXiv 论文（支持 query/category/author/max_results/sort_by）
- `download_paper`：下载论文 PDF 到本地
- `read_paper`：读取论文全文（markdown 格式）

调研 agent 搜索论文时**优先用 arXiv MCP 工具**（比 websearch 搜 arXiv 更精准，直接拿结构化 JSON），websearch 作为补充搜大厂官网/新闻。arXiv MCP 自动限速（3秒间隔）+ 缓存（24小时），符合 arXiv API 规范。

示例：搜本周端侧 agent 论文 → `search_papers(query="on-device agent", max_results=50, sort_by="submittedDate")`，再按日期窗口过滤。

# HuggingFace Daily Papers MCP（补充搜源）

本项目配置了 HuggingFace Daily Papers MCP（huggingface-daily-paper-mcp），提供以下工具：
- `get_today_papers`：获取今天 HF 社区精选论文（社区投票热门，质量比 arXiv 全量高）
- `get_yesterday_papers`：获取昨天的精选论文
- `get_papers_by_date`：按日期获取精选论文（参数 date=YYYY-MM-DD）

调研 agent 搜索论文时，**arXiv MCP 搜全量 + HuggingFace Daily Papers MCP 搜社区精选热门**，两者互补。HF Daily Papers 是社区投票筛选的热门论文，质量更高，适合优先筛选。websearch 补充搜大厂官网。

# 先使用确定性代码进行关键词过滤：

- **大厂官方优先检索式**：
  `(site:apple.com OR site:google.com OR site:microsoft.com OR site:openai.com OR site:anthropic.com OR site:meta.com OR site:samsung.com OR site:huawei.com OR site:qualcomm.com OR site:mediatek.com OR site:mi.com OR site:oppo.com OR site:vivo.com OR site:honor.com OR site:mistral.ai OR site:qwenlm.github.io) AND ("on-device" OR "edge" OR "mobile" OR "NPU" OR "local") AND ("agent" OR "assistant" OR "computer use" OR "GUI")`

  大厂官方技术博客 / 官方产品发布可以收录并排序优先，但必须是官方域名，不能用新闻、社媒、GitHub release 或二手解读替代。

- **输出语言与展示要求**：
  首页字段优先中文。`abstract` 要写成「这是什么」，`effects` 写成「有什么结果」，`mechanism` 写成「怎么做到的」。每段控制在 1-2 句，避免论文腔；详细技术分析放 wiki。

- **关键字要求**：
  每条输出 1 到 8 个 `keywords`，中文优先，例如 `GUI智能体`、`记忆`、`工具调用`、`端侧部署`、`评测基准`、`强化学习`、`安全隐私`、`手机任务`。

- **方向分类要求**：
  每条必须输出 `category`：
  - `应用`：手机、桌面、GUI 自动化、真实任务、安全隐私、产品功能。
  - `框架`：agent runtime、benchmark、训练环境、评测框架、系统架构、数据管线。
  - `算法`：强化学习、记忆、蒸馏、不确定性量化、过程奖励、规划、工具调用。

- **基础检索式**：
  `("mobile agent" OR "edge agent" OR "embedded agent" OR "agentic AI" OR "agentification") AND ("on-device" OR "edge computing" OR "resource-constrained")`

- **技术深化检索式**：
  `("LLM" OR "VLM" OR "foundation model") AND ("mobile" OR "edge") AND ("quantization" OR "pruning" OR "distillation" OR "efficient inference") AND ("agent" OR "autonomous")`

- **厂商特定检索式（示例）**：
  `("Apple Intelligence" OR "CoreAI" OR "Samsung Gauss" OR "Gemini Nano" OR "Phi-3" OR "Llama 3.2") AND ("on-device" OR "edge" OR "mobile" OR "embedded") AND ("agent" OR "optimization" OR "deployment")`

  调研时覆盖所有厂商，不只大厂官方，也要搜中国互联网公司研究项目（快手 / 字节 / 腾讯 / 百度 / 美团 / 京东 / 拼多多 / 网易等，按 arXiv affiliation + GitHub org 搜）。每家厂商的官方动态来源、websearch 关键词、arXiv affiliation 搜法和重要页面见 `docs/references/vendor-research-guide.md`。

- **厂商官方博客 URL（已验证可读，直接 fetch 这些地址找本周动态）**：
  - Apple: `machinelearning.apple.com`（ML 研究博客，AFM 系列发布在此）
  - Google: `blog.google`（官方博客，Gemma/Gemini 发布在此）、`ai.google.dev`（开发者博客）
  - NVIDIA: `blogs.nvidia.com`（官方博客，Jetson/edge AI 在此）、`developer.nvidia.com`（开发者资源）
  - Meta: `ai.meta.com/blog`（Meta AI 博客，ExecuTorch/Llama 在此）
  - Samsung: `research.samsung.com`（三星研究院博客，6G/AI agent 在此）
  - Qualcomm: `qualcomm.com/news/releases`（新闻稿）、`qualcomm.com/news/onq`（技术博客）
  - MediaTek: `mediatek.com/tek-talk-blogs`（技术博客，DGX Spark/端侧 AI 在此）
  - OpenAI: `openai.com/index`（研究博客，agent/deep research 在此）
  - Anthropic: `anthropic.com/news`（新闻博客，Claude agent 在此）
  - Microsoft: `techcommunity.microsoft.com`（技术社区，Foundry/Windows AI 在此）
  - Qwen: `qwenlm.github.io`（Qwen 官方博客，Qwen Code/模型在此）
  - Mistral: `mistral.ai/news`（新闻博客，Vibe/Ministral 在此）

  以上 URL 均经验证可访问且有 2026 年内容。调研 agent 应直接 fetch/websearch 这些地址找本周（过去 14 天）大厂官方动态。更详细的调研方法（websearch 关键词 / arXiv affiliation / GitHub org）见 `docs/references/vendor-research-guide.md`。

- **评测与基准检索式**：
  `("AndroidWorld" OR "Mobile-Env" OR "AIoTBench" OR "MLPerf Tiny") AND ("agent" OR "GUI automation")`

===========================================================

#### **一、 任务目标与定位**

**目标**：构建一个用于系统性文献综述（Systematic Literature Review）的高质量论文候选集，主题聚焦于**面向移动端与嵌入式设备的端侧AI Agent技术**。利用大语言模型（LLM）对论文摘要进行深度语义推理，以评估其技术相关性。

**核心研究问题**：
1. 当前端侧Agent的核心系统架构与认知框架是怎样的？
2. 支撑端侧Agent在资源受限设备上运行的关键使能技术有哪些？
3. **主要设备厂商（如Apple, Samsung, Huawei, Qualcomm, 小米, OPPO, vivo, 荣耀）和模型厂商（如Google, Microsoft, OpenAI, Anthropic, Meta, 面壁智能, Qwen）在该领域的技术布局、核心架构与演进趋势是什么？**
4. 学术界与工业界在端侧Agent领域的研究热点、实际效果与未来方向是什么？

#### **二、 相关性筛选标准（纳入/排除标准）**

在阅读论文标题与摘要时，请依据以下标准进行判断：

**纳入标准 (Inclusion Criteria)**：
- **核心技术对齐**：研究内容明确涉及**端侧AI Agent、Edge AI Agents、Mobile Agents、Embedded Agents**的系统设计、优化或评估。
- **技术栈覆盖**：论文主题包含但不限于**关键技术分支**（详见第三节）。
- **部署环境明确**：研究对象明确为**智能手机、IoT设备、嵌入式系统、车载终端、无人机**等资源受限的边缘计算节点。
- **厂商技术相关**：论文内容涉及或可应用于主要设备/模型厂商的端侧AI战略与技术架构。
- **论文类型**：包括但不限于**顶会论文（如NeurIPS, ICML, ICLR, CVPR, ACL, MobiSys, SenSys, ASPLOS）、顶刊论文（如TPAMI, TNNLS, ToN）、以及高质量的预印本论文（如arXiv）**。

**排除标准 (Exclusion Criteria)**：
- 纯云端Agent系统，无端侧部署与优化考量。
- 未涉及Agent技术（如仅讨论通用的联邦学习或边缘推理）。
- 非英文论文、短文（Short Paper）、Demo论文或仅进行商业产品宣传而无技术创新的内容。
- 发表于非主流学术渠道且无实质技术贡献的论文。

#### **三、 关键技术分支与关键词矩阵**

请使用以下关键词组合进行检索与相关性匹配（建议采用布尔逻辑运算符组合）。

**1. 核心概念与系统架构 (Core Concepts & Architecture)**
- **Agentic AI / Agentification**：涉及边缘通用智能、自主感知-推理-行动闭环。
- **Mobile/Embedded AI Agents**：针对手机（Phone Automation）、嵌入式设备（MCU）的GUI智能体或物理智能体（Embodied Agent）。
- **Cognitive Edge Computing**：强调认知推理与边缘计算结合，涉及LLM/AI Agent在边缘的认知保存。
- **Multi-Agent Collaboration (on Edge)**：边缘环境下的多智能体协作、分布式调度（如6G网络中的代理协作）。

**2. 模型轻量化与基础模型优化 (Model Compression & FM Optimization)**
- **Elastic Inference (弹性推理)**：应对运行时资源波动的动态结构重组（如动态深度/宽度、早期退出）。
- **Quantization (量化)**：GPTQ, AWQ, SmoothQuant, KV Cache Quantization等低比特技术。
- **Pruning & Sparsity (剪枝与稀疏化)**：SparseGPT, Wanda, N:M Sparsity等。
- **Knowledge Distillation (知识蒸馏)**：如EdgeSAM, MobileCLIP等针对特定模态的蒸馏模型。
- **Efficient Attention & Decoding**：FlashAttention, PagedAttention, Speculative Decoding (Medusa, EAGLE)用于加速推理。

**3. 运行时自适应与资源效率 (Runtime Adaptivity & Resource Efficiency)**
- **Test-time Adaptation (测试时自适应)**：在线Prompt学习、参数高效微调（PEFT, LoRA）、记忆增强，用于解决数据漂移。
- **Dynamic Multimodal Integration (动态多模态融合)**：针对异步传感器数据的自适应路由、动态注意力、Token压缩（如LLaVA-Mini的1-token视觉压缩）。
- **Energy-aware Computing (能耗感知计算)**：结合设备电池状态与热功耗的动态负载调度。
- **On-device/Edge-Cloud Collaborative Inference**：端云协同计算、弹性卸载（Elastic Offloading）策略。

**4. 感知、记忆与规划 (Perception, Memory & Planning)**
- **Multimodal Perception**：视觉语言模型（VLM）在端侧的部署，GUI理解、屏幕解析（Screen Parsing）。
- **Memory Mechanisms**：针对端侧限制的向量数据库轻量化、上下文压缩、KV Cache管理。
- **Planning & Reasoning**：基于LLM的任务分解（Task Decomposition）、思维链（CoT）、工具调用（Tool Use / Function Calling）在端侧的执行框架。

**5. 评估、基准与硬件 (Benchmarks & Hardware)**
- **Benchmarks**：AndroidWorld, Mobile-Env, AIoTBench, MLPerf Tiny等专为移动端/嵌入式设计的评估基准。
- **Hardware-Aware Compilation**：针对NPU, DSP, GPU的硬件感知编译（如MLC-LLM, llama.cpp, ONNX Runtime）。

**6. 主要厂商技术与架构 (Vendor-Specific Technologies & Architectures)**
- **设备厂商 (Device Manufacturers)**：
    - **Apple**：Apple Intelligence, CoreAI, Foundation Models on-device, Private Cloud Compute, AX 系列芯片/NPU加速。
    - **Samsung**：Samsung Gauss (Language, Code, Image), Galaxy AI, Exynos SoC NPU优化。
    - **Huawei**：HarmonyOS AI, Pangu (盘古) 轻量化模型, HiAI Foundation, Ascend NPU加速。
    - **Qualcomm**：Qualcomm AI Hub, Qualcomm Neural Processing SDK, Hexagon NPU, 终端侧AI推理优化。
    - **MediaTek**：MediaTek NeuroPilot, APU (AI Processing Unit) 加速。
    - **小米 (Xiaomi)**：Xiaomi HyperAI, MiLM (小米大模型), Xiaomi AISP (AI Subsystem Platform), 澎湃OS端侧AI能力。
    - **OPPO**：OPPO AndesGPT (安第斯大模型), ColorOS AI, OPPO AI Center, 端侧大模型部署优化。
    - **vivo**：vivo BlueLM (蓝心大模型), OriginOS AI, BlueOS (蓝河操作系统) 端侧AI能力, 蓝心小V智能体。
    - **荣耀 (Honor)**：Honor MagicOS AI, YOYO智能体, 端侧个人大模型, MagicRing 信任环多设备协同。
- **模型厂商 (Model Providers)**：
    - **Google**：Gemini Nano, MediaPipe, ML Kit, Android AICore, Pixel设备端AI。
    - **Microsoft**：Phi-3-mini / Phi-4, Windows Copilot Runtime, DirectML, NPU加速。
    - **OpenAI**：针对边缘设备的轻量化模型探索（如Distilled版本）、Function Calling for Mobile。
    - **Anthropic**：Haiku模型在边缘场景的适用性、隐私保护与端侧部署探讨。
    - **Meta**：Llama系列模型（如Llama 3.2 1B/3B, Llama 4 Scout）的端侧部署与优化。
    - **Mistral**：Mistral 7B/8x7B/Ministral系列模型（如Ministral 3B/8B）的移动端量化与部署。
    - **面壁智能 (ModelBest)**：面壁MiniCPM系列模型（如MiniCPM-1B/2B/3B端侧部署），面壁"小钢炮"系列在移动端的轻量化推理优化。
    - **Qwen (阿里云)**：Qwen系列轻量化模型（如Qwen2.5-0.5B/1.5B/3B/7B），Mobile-Agent系列研究，端侧部署与优化。

#### **四、 混合检索与相关性分析流程**

本流程采用“**LLM深度语义推理**”的筛选方法。

**LLM深度语义推理（基于摘要内容分析）**

请对每篇论文的摘要进行深度分析，并回答以下问题以评估核心相关性（输出格式见第五节）：

1. **问题1（核心对齐度）**：该论文是否明确针对**端侧/边缘设备**提出了新的Agent系统、算法或优化技术？
2. **问题2（技术分支归属）**：该论文属于第三节中哪一个或多个**关键技术分支**（如轻量化、运行时自适应、感知记忆等）？请具体说明。
3. **问题3（厂商生态关联度）**：该论文的技术方案是否与**主要设备厂商或模型厂商**的端侧AI架构（如CoreAI, Gemini Nano, Phi-3等）存在直接关联、对比或优化关系？
4. **问题4（创新性与贡献度）**：该论文的主要贡献是什么？是提出了新的架构设计、压缩算法、评估基准，还是对现有技术的系统性分析？
5. **问题5（实际效果）**：该论文报告了怎样的实验效果（如推理速度、模型大小、准确率、能耗等关键指标）？
6. **问题6（工作原理）**：该论文提出的方法的核心工作原理/技术机制是什么？
7. **问题7（潜在影响与趋势）**：该论文对于推动端侧Agent在真实设备上的部署和普及，具有怎样的潜在意义？

**综合相关性评分（1-5分，5分为最高）**：
- **5分（强烈相关）**：明确满足问题1，且与问题2-4中至少两项高度契合。
- **3-4分（中度相关）**：基本满足问题1，或在问题2-4中有一项突出贡献。
- **1-2分（弱相关）**：仅边缘性涉及端侧话题，或仅泛泛讨论Agent概念。

#### **五、 输出格式要求**

对每篇筛选后的论文，请按以下结构化格式输出分析结果：

```markdown
### 论文分析报告

| 字段 | 内容 |
|------|------|
| **论文标题** | [标题] |
| **作者与机构** | [作者列表] / [主要机构] |
| **发表信息** | [会议/期刊/arXiv] - [年份] |
| **论文链接** | [URL] |
| **摘要原文** | [摘要文本] |

**相关性分析**：
| 维度 | 分析内容 |
|------|----------|
| **核心对齐度** | [高/中/低] - [简要说明] |
| **技术分支归属** | [分支1] > [分支2] > ... (按相关性排序) |
| **厂商生态关联** | [厂商名称] / [具体架构名称] - [关联说明] |
| **创新贡献** | [核心贡献点] |
| **工作原理** | [方法的核心技术机制简述，2-3句话概括] |
| **实际效果** | [关键实验数据：模型大小、推理速度、准确率、能耗等] |

**综合评价**：
| 维度 | 内容 |
|------|------|
| **综合评分** | [1-5分] |
| **推荐意见** | [强烈推荐纳入 / 推荐纳入 / 待定 / 排除] |
| **关注建议** | [建议人工分析时重点关注的方向，如："重点关注其量化方法在端侧的实际部署效果" 或 "重点关注其多模态感知架构的设计思路" 或 "建议对比其与Gemini Nano的性能差异"] |
| **分析方向** | [建议分析侧重点：技术实现/系统架构/性能优化/隐私安全/多模态融合等] |
```
