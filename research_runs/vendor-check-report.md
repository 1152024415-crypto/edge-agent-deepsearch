# 厂商官方动态逐厂检查报告

窗口：2026-07-09 ~ 2026-07-15（含两端）
方法：WebFetch 直抓官方博客/新闻索引页（WebSearch 在本环境不可用）。每厂均实际请求过官方域名索引页。

## 设备厂商（9 家）

| 厂商 | 已查索引页 URL | 本周找到 N 条 | 候选标题列表 |
|---|---|---|---|
| Apple | https://machinelearning.apple.com/ | 0 | 0（mlr.apple.com 最新为 2026-06-08 "Introducing Third Gen Foundation Models"，ICML 帖 2026-07-04，均不在窗口内） |
| Samsung | https://research.samsung.com/blog | 0 | 0（research.samsung.com/blog 抓取成功但 JS 渲染无内容；news.samsung.com/global 反复 timeout；samsung.com/global/newsroom 403 — WebFetch 无法穿透） |
| Huawei | https://developer.huawei.com/consumer/cn/hiai/ | 0 | 0（HiAI 页为产品页无博客；consumer.huawei.com/en/news socket hang up/JS 渲染无内容） |
| Qualcomm | https://www.qualcomm.com/developer/blog | 0 | 0（最新帖 2026-07-07 "GenieX developer preview"，早于窗口；qualcomm.com/news 404） |
| MediaTek | https://neuropilot.mediatek.com/ | 0 | 0（NeuroPilot 为产品落地页无博客；mediatek.com/news 无窗口内条目） |
| Xiaomi | https://mimo.xiaomi.com/blog | 0 | 0（MiMo 博客仅显示 2025-12-16 "Introducing MiMo-V2-Flash"） |
| OPPO | https://www.oppo.com/en/newsroom/ | 0 | 0（新闻室 JS 渲染，无可提取文章） |
| vivo | https://developers.vivo.com/product/ai/bluelm | 0 | 0（BlueLM 文档页无窗口内动态） |
| Honor | https://www.honor.com/news/ | 0 | 0（最新动态 2026-03-31，早于窗口） |

## 模型厂商（9 家，含 NVIDIA）

| 厂商 | 已查索引页 URL | 本周找到 N 条 | 候选标题列表 |
|---|---|---|---|
| Google | https://blog.google/ + https://developers.googleblog.com/ | 6 | (1) LiteRT.js high performance Web AI Inference [07-09] (2) Waze Gemini updates [07-13] (3) On-Device AI with Google Tensor and Pixel [07-13] (4) Systems Engineering Playbook: Qwen 3.5-397B MoE on Ironwood TPU7x [07-14] (5) Celebrating 25 years of visual search [07-14] (6) Reconstructing Pelé's lost goal (DeepMind) [07-14] |
| Microsoft | https://www.microsoft.com/en-us/research/blog/ | 0 | 0（research blog 403；techcommunity.microsoft.com 需登录重定向；azure.microsoft.com/blog 404；research.microsoft.com/blog 301→403 — WebFetch 无法穿透） |
| OpenAI | https://openai.com/blog | 0 | 0（blog 页 JS 渲染无法提取日期；/research 404；/index 404 — 无法确认窗口内有可提取条目） |
| Anthropic | https://www.anthropic.com/news | 6 | (1) UST bringing Claude to physical AI [07-09] (2) Inviting hard questions [07-09] (3) Ben Bernanke to Long-Term Benefit Trust [07-09] (4) Reflect on how you use Claude [07-09] (5) Claude for Teachers [07-14] (6) $10M to Canadian AI research [07-14] |
| Meta | https://ai.meta.com/blog/ | 1 | Introducing Muse Spark 1.1 [07-09] |
| NVIDIA | https://blogs.nvidia.com/ + https://developer.nvidia.com/blog | 14 | blogs.nvidia.com: (1) Nemotron Labs open models [07-14] (2) Performance per Watt [07-14]. developer.nvidia.com: (3) Lessons From the Leaderboard AI Reasoning [07-14] (4) Autoresearch Workflow with RL Agent Skills and NeMo [07-14] (5) Post-Train Cosmos 3 with Agent Skills [07-14] (6) Ising Decoding Color Code [07-13] (7) Extreme Event Likelihoods Guided Generative Models [07-13] (8) Evaluate General-Purpose Robot Policies [07-11] (9) Reducing HBM Bottlenecks JAX LLM Training [07-10] (10) Kernel Fusion in CUDA [07-10] (11) AI Model Co-Design Hardware-Friendly LLM [07-10] (12) BioNeMo Agent Toolkit Co-Folding [07-10] (13) Synthetic Data for Financial AI with NeMo [07-09] (14) GPU-Initiated Communication Molecular Dynamics [07-09]. 注：另有一条 07-09 GeForce NOW Toronto 属云游戏非 AI，已排除。 |
| Mistral | https://mistral.ai/news | 1 | Your Prompts and Skills need a system of record. [07-09] |
| 面壁智能 ModelBest | https://modelbest.cn/en | 0 | 0（modelbest.cn/en 无窗口内动态；modelbest.cn 主站 timeout） |
| Qwen | https://qwenlm.github.io/ | 0 | 0（首页无窗口内博文） |

## 模型实验室（5 家，易漏必查）

| 厂商 | 已查索引页 URL | 本周找到 N 条 | 候选标题列表 |
|---|---|---|---|
| DeepSeek | https://www.deepseek.com/ | 0 | 0（首页无窗口内动态） |
| Moonshot | https://www.moonshot.cn/ | 0 | 0（首页无窗口内动态） |
| Zhipu/智谱 | https://www.zhipuai.cn/ | 0 | 0（首页无窗口内动态） |
| Minimax | https://www.minimaxi.com/ | 0 | 0（首页无窗口内动态） |
| 百川 Baichuan | https://www.baichuan-ai.com/ | 0 | 0（首页仅标题，无博客/新闻条目） |

## 汇总

- 命中厂商：6 家（Google 6、Anthropic 6、NVIDIA 14、Meta 1、Mistral 1；其余 17 家本周 0）
- 总候选数：28 条
- 所有候选 URL 均命中 vendor-whitelist.md 官方域名（blog.google / developers.googleblog.com / anthropic.com / ai.meta.com / blogs.nvidia.com / developer.nvidia.com / mistral.ai）
- WebSearch 在本环境不可用（工具返回 "no access to a web search tool"），全部依赖 WebFetch 直抓官方域名索引页
