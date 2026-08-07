# 厂商官方动态采集报告 — 窗口 2026-08-01 ~ 2026-08-07

> 采集方式：WebFetch 直抓 `vendor-whitelist.md` 官方域名索引页。
> 硬约束：URL 必须命中白名单官方域名；只收窗口内；非 AI/模型/研究相关的纯企业新闻/任命/营销认可/游戏动态予以排除（已在逐厂条目注明）。
> 总候选数：**16 条**（分布于 5 家厂商：Samsung 2、Google 3、Anthropic 1、Mistral 1、NVIDIA 9）。

## 设备厂商（9 家）

### 1. Apple — 0 命中
- 抓取：`machinelearning.apple.com`（域名被网络策略阻断，无法验证安全）、`apple.com/newsroom`、`developer.apple.com/machine-learning`。
- 结果：newsroom 与 developer 页窗口内无发布；machinelearning 域名受阻未取到。0 候选。

### 2. Samsung — 2 命中 ✅
- 抓取：`research.samsung.com/artificial-intelligence`、`news.samsung.com/global`。
- 候选：
  - 2026-08-04 LittleBit-2: Maximizing the Spectral Energy Gain in Sub-1-Bit LLMs via Latent Geometry Alignment — https://research.samsung.com/blog/LittleBit-2-Maximizing-the-Spectral-Energy-Gain-in-Sub-1-Bit-LLMs-via-Latent-Geometry-Alignment
  - 2026-08-03 NanoQuant: Efficient Sub-1-Bit Quantization of Large Language Models — https://research.samsung.com/blog/NanoQuant-Efficient-Sub-1-Bit-Quantization-of-Large-Language-Models
- news.samsung.com 窗口内无发布。

### 3. Huawei — 0 命中
- 抓取：`developer.huawei.com/consumer/cn/hiai/`。
- 结果：窗口内无发布。0 候选。

### 4. Qualcomm — 0 命中（1 条企业新闻已排除）
- 抓取：`qualcomm.com/news`。
- 窗口内仅 1 条：2026-08-04 "Qualcomm Appoints Wassim Chourbaji as SVP and President, Qualcomm EMEA"（https://www.qualcomm.com/news/releases/2026/08/...）。属高管任命企业新闻，非 AI/模型/研究动态，按规则排除。0 候选。

### 5. MediaTek — 0 命中
- 抓取：`mediatek.com/technology/ai`（域名被网络策略阻断）、`neuropilot.mediatek.com`。
- 结果：可访问页面窗口内无发布；主域受阻。0 候选。

### 6. Xiaomi — 0 命中
- 抓取：`mimo.xiaomi.com`。
- 结果：窗口内无发布。0 候选。

### 7. OPPO — 0 命中
- 抓取：`oppo.com/cn/`。
- 结果：页面无带日期的发布项，窗口内无可确认条目。0 候选。

### 8. vivo — 0 命中
- 抓取：`vivo.com.cn`、`developers.vivo.com/product/ai/bluelm`。
- 结果：两处窗口内均无发布。0 候选。

### 9. Honor — 0 命中
- 抓取：`honor.com`。
- 结果：窗口内无发布。0 候选。

## 模型厂商（10 家）

### 10. Google — 3 命中 ✅
- 抓取：`blog.google/technology/ai/`（列表无显式日期）、`ai.google.dev/blog`（404）、`developers.googleblog.com/en/`（命中）。
- 候选（均来自 developers.googleblog.com，命中 `googleblog.com` 白名单子域 `developers.googleblog.com`）：
  - 2026-08-06 Agent Plugins package your skills, tools, and more — https://developers.googleblog.com/en/agent-plugins-package-your-skills-tools-and-more/
  - 2026-08-05 Scaling AI Agent Infrastructure with the MCP Stateless updates — https://developers.googleblog.com/en/scaling-ai-agent-infrastructure-with-the-mcp-stateless-updates/
  - 2026-08-04 A unified API for AI model routing — https://developers.googleblog.com/en/a-unified-api-for-ai-model-routing/

### 11. Microsoft — 0 命中（1 条营销认可已排除）
- 抓取：`techcommunity.microsoft.com/blog`（窗口内无）、`azure.microsoft.com/blog`。
- azure 博客窗口内仅 1 条：2026-08-06 "Microsoft named a Leader in the 2026 Gartner Magic Quadrant for AI-Augmented Code Modernization Tools"（https://azure.microsoft.com/en-us/blog/...）。属市场认可营销公告，非技术/模型/研究动态，按规则排除。0 候选。

### 12. OpenAI — 0 命中
- 抓取：`openai.com/blog`、`openai.com/research`。
- 结果：两处窗口内均无发布。0 候选。

### 13. Anthropic — 1 命中 ✅（1 条任命已排除）
- 抓取：`anthropic.com/news`。
- 候选：
  - 2026-08-07 Improving Fable 5's biology safeguards — https://www.anthropic.com/news/improving-fable-5-s-biology-safeguards
- 排除：2026-08-04 "Tino Cuéllar to join Anthropic as Chief Global Affairs Officer"（高管任命企业新闻，非技术动态）。

### 14. Meta — 0 命中（访问受限）
- 抓取：`ai.meta.com/blog/`（403 Forbidden）、`ai.meta.com/`（无列表）、`about.fb.com`（301 重定向至 about.facebook.com，超出白名单）。
- 结果：官方博客域名被服务端阻断，无法取到窗口内条目。0 候选（访问受限，非确认无发布）。

### 15. NVIDIA — 9 命中 ✅
- 抓取：`blogs.nvidia.com`（7 条）、`developer.nvidia.com/blog`（4 条）。
- 候选：
  - 2026-08-04 AI Leaders Propose SAFE Guidelines for Cybersecurity Transparency — https://blogs.nvidia.com/blog/open-secure-ai-alliance-contributions/
  - 2026-08-04 NVIDIA Alpamayo 2 Super... Robotaxis and Autonomous Vehicles — https://blogs.nvidia.com/blog/alpamayo-2-super-open-model-now-available/
  - 2026-08-04 As AI Increases Demands on Memory, Storage Steps Up — https://blogs.nvidia.com/blog/ai-storage-fms/
  - 2026-08-06 Into the Omniverse: How Open World Models Push the Frontier of Physical AI — https://blogs.nvidia.com/blog/open-world-models-physical-ai/
  - 2026-08-04 NVIDIA Joins NSF State and Regional AI Hubs Program — https://blogs.nvidia.com/blog/nsf-state-regional-ai-hub-program/
  - 2026-08-03 How to Run Isolated Tenant Kubernetes Clusters on Shared GPU Infrastructure — https://developer.nvidia.com/blog/how-to-run-isolated-tenant-kubernetes-clusters-on-shared-gpu-infrastructure/
  - 2026-08-03 NVIDIA Vera Storage Benchmarks — https://developer.nvidia.com/blog/nvidia-vera-storage-benchmarks-faster-encryption-compression-integrity-checking-and-recovery-for-ai-native-storage/
  - 2026-08-04 Beyond VLAs: How World Action Models Reshape Robot Manipulation — https://developer.nvidia.com/blog/beyond-vlas-how-world-action-models-reshape-robot-manipulation/
  - 2026-08-04 Generate Trajectories, Reasoning Traces, and Auto-Labels with NVIDIA Alpamayo 2 Super — https://developer.nvidia.com/blog/generate-trajectories-reasoning-traces-and-auto-labels-with-nvidia-alpamayo-2-super/
- 排除（非 AI 动态）：2026-08-05 "NVIDIA and Partners Build in America, for America"（制造/商业）、2026-08-06 "GeForce NOW Shakes Up August With 26 New Games"（游戏）。

### 16. Mistral — 1 命中 ✅
- 抓取：`mistral.ai/news`。
- 候选：
  - 2026-08-04 Introducing Shieldstral — https://mistral.ai/news/shieldstral/ （3B 开放权重多模态安全分类器，Apache 2.0，端侧适配）

### 17. 面壁智能 ModelBest — 0 命中
- 抓取：`modelbest.cn`。
- 结果：窗口内无发布。0 候选。

### 18. Qwen（阿里云）— 0 命中
- 抓取：`qwenlm.github.io`。
- 结果：窗口内无发布。0 候选。

### 19. 阶跃星辰 StepFun — 0 命中
- 抓取：`stepfun.com`。
- 结果：官网 JS 渲染，窗口内可抓条目无；按调研记忆其公告多在微信公众号（非白名单域名，不收）。0 候选。

## 模型实验室（5 家，强制检查）

### 20. DeepSeek — 0 命中
- 抓取：`deepseek.com`。
- 结果：窗口内无发布。0 候选（已检查，结果为 0）。

### 21. Moonshot/Kimi — 0 命中
- 抓取：`moonshot.cn`、`kimi.com`（404）。
- 结果：窗口内无发布。0 候选（已检查，结果为 0）。

### 22. Zhipu — 0 命中
- 抓取：`zhipuai.cn`。
- 结果：窗口内无发布（最近一条为 07-31，恰在窗口外）。0 候选（已检查，结果为 0）。

### 23. MiniMax — 0 命中
- 抓取：`minimax.io`。
- 结果：窗口内无发布。0 候选（已检查，结果为 0）。

### 24. Baichuan — 0 命中
- 抓取：`baichuan-ai.com`。
- 结果：窗口内无发布。0 候选（已检查，结果为 0）。

---

## 汇总

| 厂商 | 命中数 | 备注 |
|---|---|---|
| Apple | 0 | machinelearning 域名被阻断 |
| Samsung | 2 | research.samsung.com 亚 1 比特量化两篇 |
| Huawei | 0 | — |
| Qualcomm | 0 | 1 条任命企业新闻已排除 |
| MediaTek | 0 | 主域被阻断 |
| Xiaomi | 0 | — |
| OPPO | 0 | 页面无带日期条目 |
| vivo | 0 | — |
| Honor | 0 | — |
| Google | 3 | developers.googleblog 三篇 agent/MCP/路由 |
| Microsoft | 0 | 1 条 Gartner 营销认可已排除 |
| OpenAI | 0 | — |
| Anthropic | 1 | Fable 5 生物学安全护栏 |
| Meta | 0 | ai.meta.com 403，访问受限 |
| NVIDIA | 9 | blogs 5 + developer 4，排除 2 条非 AI |
| Mistral | 1 | Shieldstral 3B 安全分类器 |
| 面壁 | 0 | — |
| Qwen | 0 | — |
| StepFun | 0 | 官网 JS 渲染，公告在公众号 |
| DeepSeek | 0 | 已检查 |
| Moonshot | 0 | 已检查 |
| Zhipu | 0 | 已检查（最近 07-31） |
| MiniMax | 0 | 已检查 |
| Baichuan | 0 | 已检查 |
| **合计** | **16** | |

## 候选逐条索引

1. Samsung — 2026-08-03 NanoQuant — https://research.samsung.com/blog/NanoQuant-Efficient-Sub-1-Bit-Quantization-of-Large-Language-Models
2. Samsung — 2026-08-04 LittleBit-2 — https://research.samsung.com/blog/LittleBit-2-Maximizing-the-Spectral-Energy-Gain-in-Sub-1-Bit-LLMs-via-Latent-Geometry-Alignment
3. Google — 2026-08-04 A unified API for AI model routing — https://developers.googleblog.com/en/a-unified-api-for-ai-model-routing/
4. Google — 2026-08-05 Scaling AI Agent Infrastructure with MCP Stateless — https://developers.googleblog.com/en/scaling-ai-agent-infrastructure-with-the-mcp-stateless-updates/
5. Google — 2026-08-06 Agent Plugins — https://developers.googleblog.com/en/agent-plugins-package-your-skills-tools-and-more/
6. Anthropic — 2026-08-07 Improving Fable 5's biology safeguards — https://www.anthropic.com/news/improving-fable-5-s-biology-safeguards
7. Mistral — 2026-08-04 Introducing Shieldstral — https://mistral.ai/news/shieldstral/
8. NVIDIA — 2026-08-03 Isolated Tenant K8s on Shared GPU — https://developer.nvidia.com/blog/how-to-run-isolated-tenant-kubernetes-clusters-on-shared-gpu-infrastructure/
9. NVIDIA — 2026-08-03 Vera Storage Benchmarks — https://developer.nvidia.com/blog/nvidia-vera-storage-benchmarks-faster-encryption-compression-integrity-checking-and-recovery-for-ai-native-storage/
10. NVIDIA — 2026-08-04 SAFE Guidelines for Cybersecurity Transparency — https://blogs.nvidia.com/blog/open-secure-ai-alliance-contributions/
11. NVIDIA — 2026-08-04 Alpamayo 2 Super for Robotaxis — https://blogs.nvidia.com/blog/alpamayo-2-super-open-model-now-available/
12. NVIDIA — 2026-08-04 As AI Increases Demands on Memory, Storage Steps Up — https://blogs.nvidia.com/blog/ai-storage-fms/
13. NVIDIA — 2026-08-04 NSF State and Regional AI Hubs — https://blogs.nvidia.com/blog/nsf-state-regional-ai-hub-program/
14. NVIDIA — 2026-08-04 Beyond VLAs: World Action Models — https://developer.nvidia.com/blog/beyond-vlas-how-world-action-models-reshape-robot-manipulation/
15. NVIDIA — 2026-08-04 Generate Trajectories with Alpamayo 2 Super — https://developer.nvidia.com/blog/generate-trajectories-reasoning-traces-and-auto-labels-with-nvidia-alpamayo-2-super/
16. NVIDIA — 2026-08-06 Into the Omniverse: Open World Models Physical AI — https://blogs.nvidia.com/blog/open-world-models-physical-ai/
