# 厂商官方动态采集报告（2026-07-10 ~ 2026-07-17）

> 窗口：2026-07-10 至 2026-07-17（含两端）。来源硬约束：URL 必须命中 `docs/references/vendor-whitelist.md` 官方域名或子域；非白名单域名一律丢弃；日期不明不收；不许编造 URL，404/403 丢弃。
> 检索方式：WebFetch 直抓各厂官方博客/新闻索引页；WebSearch 当前不可用（已尝试，返回"无 web search 工具"），改以 WebFetch + DuckDuckGo 站内搜索补救。
> 白名单子域命中口径：`blog.google`、`developers.googleblog.com`（视为 `googleblog.com` 子域，命中白名单）、`blogs.nvidia.com`、`developer.nvidia.com`、`microsoft.com`、`anthropic.com`、`qualcomm.com`、`mediatek.com`、`apple.com`、`samsung.com`、`huawei.com`、`mi.com`、`oppo.com`、`vivo.com`、`honor.com`、`alibabacloud.com`/`qwenlm.github.io`、`mistral.ai`、`stepfun.com`。

## 总览

- 逐厂检查厂商数：23（9 设备 + 9 模型 + 5 模型实验室，阶跃星辰在模型实验室组）
- 本周命中候选总数：**33**
- 命中分布：NVIDIA 20 / Google 9 / Anthropic 2 / Microsoft 1 / Qualcomm 1 / 其余 18 家 0

## 逐厂命中数一览

| 厂商 | 已查 | 本周找到 | 备注 |
|---|---|---|---|
| Apple | ✅ | 0 | machinelearning.apple.com 最新 2026-07-04 ICML；apple.com/newsroom JS 渲染抓不到列表 |
| Samsung | ✅ | 0 | research.samsung.com/artificial-intelligence 最新 2026-07-06 K-Merge |
| Huawei | ✅ | 0 | huawei.com/en/news JS 渲染；consumer.huawei.com/en/news 404 |
| Qualcomm | ✅ | **1** | 财报发布时间表 2026-07-15 |
| MediaTek | ✅ | 0 | mediatek.com/blog 最新 2026-07-09（窗口外 1 天，已抓文章页确认日期） |
| Xiaomi | ✅ | 0 | mimo.xiaomi.com/blog 最新 2025-12-16 |
| OPPO | ✅ | 0 | oppo.com/en/newsroom JS 渲染抓不到内容 |
| vivo | ✅ | 0 | vivo.com/en/news 最新 2026-03-04 |
| Honor | ✅ | 0 | honor.com/global/news 最新 2026-06-09 |
| Google | ✅ | **9** | blog.google 5 篇 + developers.googleblog.com 4 篇（07-10~07-16） |
| Microsoft | ✅ | **1** | microsoft.com/en-us/research/blog 2026-07-13 |
| OpenAI | ✅ | 0 | openai.com/news 403；DuckDuckGo 站内搜可见最新 2026-07-09 GPT-5.6，窗口外 |
| Anthropic | ✅ | **2** | anthropic.com/news 2026-07-14 两篇 |
| Meta | ✅ | 0 | ai.meta.com/blog 最新 2026-07-09 Muse Spark 1.1，窗口外 |
| NVIDIA | ✅ | **20** | blogs.nvidia.com 5 篇 + developer.nvidia.com 15 篇（07-10~07-16） |
| Mistral | ✅ | 0 | mistral.ai/news 最新 2026-07-09，窗口外 |
| 面壁智能 ModelBest | ✅ | 0 | modelbest.cn 为单页落地页，新闻卡片未给独立 URL，全部丢弃 |
| Qwen（阿里云） | ✅ | 0 | qwenlm.github.io 最新 2025-09-23 Qwen3Guard |
| DeepSeek | ✅ | 0 | deepseek.com 首页仅 V4 预览横幅无日期；api-docs.deepseek.com/news 无日期列表 |
| Moonshot / Kimi | ✅ | 0 | kimi.com/blog 有 2 篇窗口内文章（07-14 Kimi K3、07-16 PerceptionBench），但 kimi.com 不在 vendor-whitelist.md，按硬约束丢弃 |
| Zhipu 智谱 | ✅ | 0 | zhipuai.cn 首页最新动态轮播无独立 URL/日期；open.bigmodel.cn 跳转到 docs.bigmodel.cn 无新闻列表 |
| Minimax | ✅ | 0 | minimax.io/blog 最新 2026-06-09 MaxProof |
| 百川 Baichuan | ✅ | 0 | baichuan-ai.com 首页 JS 渲染，仅返回站点标题 |
| 阶跃星辰 StepFun | ✅ | 0 | stepfun.com 首页 JS 渲染，仅返回"阶跃星辰"字样 |

## 候选列表（每条一行：vendor | date | title | url）

1. Anthropic | 2026-07-14 | Introducing Claude for Teachers | https://www.anthropic.com/news/claude-for-teachers
2. Anthropic | 2026-07-14 | Anthropic commits $10 million to Canadian AI research | https://www.anthropic.com/news/canadian-ai-research
3. Microsoft | 2026-07-13 | Verifying Rust cryptography in SymCrypt, from standards to code | https://www.microsoft.com/en-us/research/blog/verifying-rust-cryptography-in-symcrypt-from-standards-to-code/
4. Qualcomm | 2026-07-15 | Qualcomm Schedules Third Quarter Fiscal 2026 Earnings Release and Conference Call | https://www.qualcomm.com/news/releases/2026/07/qualcomm-schedules-third-quarter-fiscal-2026-earnings-release-a
5. Google | 2026-07-10 | How to make Gemini study notebooks for any subject | https://blog.google/innovation-and-ai/products/gemini-app/how-to-make-gemini-study-notebooks/
6. Google | 2026-07-14 | Reconstructing Pelé's "lost" goal | https://blog.google/innovation-and-ai/models-and-research/google-deepmind/reconstructing-peles-lost-goal/
7. Google | 2026-07-14 | How Gemini is speaking the language of Southeast Asia | https://blog.google/innovation-and-ai/products/gemini-app/gemini-southeast-asia-report-2026/
8. Google | 2026-07-14 | Our largest solar and battery storage project ever | https://blog.google/innovation-and-ai/infrastructure-and-cloud/global-network/steel-river-arkansas/
9. Google | 2026-07-16 | NotebookLM is now Gemini Notebook | https://blog.google/innovation-and-ai/products/gemini-notebook/notebooklm-gemini-notebook/
10. Google | 2026-07-14 | Systems Engineering Playbook: Optimizing Qwen 3.5-397B MoE on Ironwood (TPU7x) | https://developers.googleblog.com/systems-engineering-playbook-optimizing-qwen-35-397b-moe-on-ironwood-tpu7x/
11. Google | 2026-07-16 | Expanding Choice in Gemini Enterprise Agent Platform: Introducing Grounding with Parallel Web Search | https://developers.googleblog.com/expanding-choice-in-gemini-enterprise-agent-platform-introducing-grounding-with-parallel-web-search/
12. Google | 2026-07-16 | Building scalable AI agents with modular prompt transpilation | https://developers.googleblog.com/building-scalable-ai-agents-with-modular-prompt-transpilation/
13. Google | 2026-07-16 | Evolving Spec-Driven Development: Conductor Now Supports Antigravity | https://developers.googleblog.com/evolving-spec-driven-development-conductor-now-supports-antigravity/
14. NVIDIA | 2026-07-10 | AI Model Co-Design: Hardware-Friendly LLM Design | https://developer.nvidia.com/blog/ai-model-co-design-hardware-friendly-llm-design/
15. NVIDIA | 2026-07-10 | Reducing High-Bandwidth Memory Bottlenecks in JAX-Based LLM Training with Host Offloading | https://developer.nvidia.com/blog/reducing-high-bandwidth-memory-bottlenecks-in-jax-based-llm-training-with-host-offloading/
16. NVIDIA | 2026-07-10 | Accelerating End-to-End Co-Folding Performance with NVIDIA BioNeMo Agent Toolkit | https://developer.nvidia.com/blog/accelerating-end-to-end-co-folding-performance-with-nvidia-bionemo-agent-toolkit/
17. NVIDIA | 2026-07-11 | How to Evaluate General-Purpose Robot Policies for Real-World Deployment | https://developer.nvidia.com/blog/how-to-evaluate-general-purpose-robot-policies-for-real-world-deployment/
18. NVIDIA | 2026-07-13 | NVIDIA Ising Decoding Cuts Color Code Logical Error Rates by Over 300X | https://developer.nvidia.com/blog/nvidia-ising-decoding-cuts-color-code-logical-error-rates-by-over-300x/
19. NVIDIA | 2026-07-13 | Extreme Event Likelihoods with Guided Generative Models | https://developer.nvidia.com/blog/extreme-event-likelihoods-with-guided-generative-models/
20. NVIDIA | 2026-07-14 | Nemotron Labs: How Open Models Give Enterprises and Nations AI They Can Trust, Control and Customize | https://blogs.nvidia.com/blog/nemotron-open-models-ai-trust-control-customize/
21. NVIDIA | 2026-07-14 | Why Performance per Watt Is the Ultimate Metric for AI Infrastructure Efficiency | https://blogs.nvidia.com/blog/performance-per-watt-ai-infrastructure-efficiency/
22. NVIDIA | 2026-07-14 | Lessons From the Leaderboard: What 5,000+ Kagglers Taught Us About Improving AI Reasoning | https://developer.nvidia.com/blog/lessons-from-the-leaderboard-what-5000-kagglers-taught-us-about-improving-ai-reasoning/
23. NVIDIA | 2026-07-14 | How to Run an Autoresearch Workflow with RL Agent Skills and NVIDIA NeMo | https://developer.nvidia.com/blog/how-to-run-an-autoresearch-workflow-with-rl-agent-skills-and-nvidia-nemo/
24. NVIDIA | 2026-07-14 | Post-Train NVIDIA Cosmos 3 in One Day Using Agent Skills | https://developer.nvidia.com/blog/post-train-nvidia-cosmos-3-in-one-day-using-agent-skills/
25. NVIDIA | 2026-07-15 | NVIDIA and Japan Bring Full-Stack AI and Robotics to Every Industry | https://blogs.nvidia.com/blog/japan-ecosystem-2026/
26. NVIDIA | 2026-07-15 | NVIDIA Introduces New Jetson Thor Computers to Advance Mainstream Robotics and Edge AI | https://blogs.nvidia.com/blog/jetson-thor-robotics-edge-ai-agent/
27. NVIDIA | 2026-07-15 | Build a Multi-Camera 3D Tracking Application with NVIDIA DeepStream 9.1 Skills | https://developer.nvidia.com/blog/build-a-multi-camera-3d-tracking-application-with-nvidia-deepstream-9-1-skills/
28. NVIDIA | 2026-07-15 | Develop Lightweight USD Runtimes Faster with AI Agents | https://developer.nvidia.com/blog/develop-lightweight-usd-runtimes-faster-with-ai-agents/
29. NVIDIA | 2026-07-15 | Building Faster Cryptography with Carryless Multiplication in NVIDIA CUDA 13.3 | https://developer.nvidia.com/blog/building-faster-cryptography-with-carryless-multiplication-in-nvidia-cuda-13-3/
30. NVIDIA | 2026-07-16 | Sharpen the Sword, Skip the Downloads — 'Onimusha: Way of the Sword' Is Coming to GeForce NOW | https://blogs.nvidia.com/blog/geforce-now-thursday-onimusha-coming/
31. NVIDIA | 2026-07-16 | Q&A: How Capcom Brought Path Tracing to RE ENGINE Across PRAGMATA and Resident Evil Requiem | https://developer.nvidia.com/blog/qa-how-capcom-brought-path-tracing-to-re-engine-across-pragmata-and-resident-evil-requiem/
32. NVIDIA | 2026-07-16 | Integrating Context-Aware Video AI Agents Into Enterprise Workflows | https://developer.nvidia.com/blog/integrating-context-aware-video-ai-agents-into-enterprise-workflows/
33. NVIDIA | 2026-07-16 | Scaling Agentic AI Factories Through Extreme Co-Design with NVIDIA BlueField | https://developer.nvidia.com/blog/scaling-agentic-ai-factories-through-extreme-co-design-with-nvidia-bluefield/

## 关键丢弃说明

- **Moonshot / Kimi**：kimi.com/blog 在窗口内有 2026-07-14 "Kimi K3" 和 2026-07-16 "PerceptionBench" 两篇官方博客，但 `vendor-whitelist.md` 中 Moonshot 域名未列入（只有阶跃星辰 stepfun.com 在白名单），按硬约束丢弃。建议后续把 `kimi.com` / `moonshot.cn` 补入白名单。
- **Google DeepMind 子站**：deepmind.google/blog 在窗口内有"Our approach to bioresilience"和"Empowering India's next generation of innovators with ATL Saathi"两篇（仅标"July 2026"无具体日期），但 deepmind.google 不在白名单（白名单只列 `google.com`/`blog.google`/`googleblog.com`/`android-developers.googleblog.com`/`ai.google.dev`），且日期不明，按硬约束丢弃。
- **面壁智能**：modelbest.cn 首页新闻列表为内联卡片，未给独立文章 URL；按"不许编造 URL"原则全部丢弃。
- **OPPO / vivo / Honor / Huawei / Samsung Research / Apple Newsroom / StepFun / 百川**：均为 JS 渲染首页，WebFetch 取不到列表数据，候选 0；不代表本周无发布，仅静态抓取失败。
- **MediaTek**：tek-talk-blogs 最新一篇"Advancing Wireless Performance for the AI Era"实际发布日期 2026-07-09（侧栏曾误显示 07-10，已抓文章页确认为 07-09），刚好在窗口外 1 天，丢弃。
- **OpenAI**：openai.com/news 直连返回 403（被反爬拦截），通过 DuckDuckGo 站内搜索间接看到最新条目为 2026-07-09 GPT-5.6，窗口内未发现命中。
- **developers.googleblog.com 域名口径**：白名单只显式列出 `googleblog.com` 与 `android-developers.googleblog.com`；本报告按"官方域名或其子域"口径，将 `developers.googleblog.com` 视为 `googleblog.com` 子域并命中白名单。若严口径只认 `android-developers.googleblog.com`，则 Google 命中数应从 9 降为 5（仅保留 blog.google 5 篇）。
- **先前版本 candidates-vendor.json 的纠错**：旧文件中"Unlocking the Next Era of On-Device AI with Google Tensor and Pixel"（自称 2026-07-13, developers.googleblog.com）URL 直连返回 404，无法验证存在，已剔除；旧文件中"Kernel Fusion in NVIDIA CUDA: Optimizing Memory Traffic and Launch Overhead"（自称 2026-07-10, developer.nvidia.com）在 developer.nvidia.com/blog 索引页窗口内 15 篇列表中未出现，无法验证，已剔除。

## 文件输出

- `research_runs/candidates-vendor.json`：33 条候选 JSON 数组。
- `research_runs/vendor-check-report-0717.md`：本报告。
