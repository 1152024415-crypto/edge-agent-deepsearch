# 厂商官方动态采集报告

- **窗口**：2026-07-31 ~ 2026-08-03（含两端）
- **采集时间**：2026-08-03
- **方法**：WebFetch 直抓各厂官方博客/新闻索引页（WebSearch 在本环境不可用，全程 WebFetch）
- **白名单**：`docs/references/vendor-whitelist.md` 列出的官方域名
- **候选总数**：5（全部命中白名单域名，全部日期 2026-07-31）
- **被丢弃候选**：2 条（见文末"丢弃记录"）

---

## 逐厂命中数一览

| # | 厂商 | 命中数 | 说明 |
|---|---|---|---|
| 1 | Apple | 0 | machinelearning.apple.com 最近帖 2026-07-27；apple.com/newsroom 静态 HTML 未渲染列表；developer.apple.com/machine-learning 无日期 |
| 2 | Samsung | 0 | research.samsung.com/blog 仅返回筛选页骨架；news.samsung.com/global 多次 socket 关闭/超时，未能取到列表 |
| 3 | Huawei | 0 | huawei.com/cn/news 与 /en/news 均为动态加载，静态 HTML 无文章列表 |
| 4 | Qualcomm | **2** | qualcomm.com/developer/blog 两条 07-31 |
| 5 | MediaTek | 0 | neuropilot.mediatek.com 为产品落地页无博客；mediatek.com/news 404 |
| 6 | Xiaomi | 0 | mimo.xiaomi.com 最近帖 2025-12-16（MiMo-V2-Flash）；mi.com global news 404；hyper-os.mi.com/blog 404 |
| 7 | OPPO | 0 | oppo.com/en/news 与 /cn/news/ 均无文章渲染 |
| 8 | vivo | 0（白名单内）| vivo.com/en/news 仅 2024；vivo.com.cn 有 1 条 07-31 但域名不在白名单（见丢弃记录） |
| 9 | Honor | 0 | honor.com/global/news 最近帖 2026-06-09 |
| 10 | Google | **1** | blog.google Gemini Drop July 2026，07-31 |
| 11 | Microsoft | 0 | microsoft.com/research/blog 最近 07-30（Echoverse/EvoLib）；azure.microsoft.com/blog 最近 07-27；techcommunity 403 |
| 12 | OpenAI | 0 | openai.com/news、/blog、/index、/research 多次 403/404，未能取到列表 |
| 13 | Anthropic | 0 | anthropic.com/news 最近 07-30（"Investigating three real-world incidents..."）；/research 最近 07-28 |
| 14 | Meta | 0 | ai.meta.com/blog 最近 07-27；about.fb.com/news 最近 07-28 |
| 15 | NVIDIA | **2** | developer.nvidia.com/blog 两条 07-31 |
| 16 | Mistral | 0 | mistral.ai/news 最近 07-09（"Your Prompts and Skills..."） |
| 17 | 面壁智能 ModelBest | 0 | modelbest.cn 与 /en/blog 404；openbmb.github.io 仅有 MiniCPM-o 4.5 demo 页无日期 |
| 18 | Qwen (阿里云) | 0 | qwenlm.github.io 列表全为 2025 帖；alibabacloud.com/blog 超时 |
| — | 阶跃星辰 StepFun | 0 | stepfun.com 首页 JS 渲染、无文章列表；/news 404 |
| — | DeepSeek | 0 | deepseek.com 与 /news 均无日期文章列表 |
| — | Moonshot | 0 | kimi.com/blog 最近 07-16（Kimi K3、PerceptionBench） |
| — | Zhipu 智谱 | 0 | zhipuai.cn/news 停留在 2025-08/2026-03 |
| — | Minimax | 0（白名单内）| minimax.io 有 1 条 07-31（H3）但 minimax.io 不在白名单（见丢弃记录） |
| — | 百川 Baichuan | 0 | baichuan-ai.com /news 与 /research 均无 2026-07/08 帖 |

**命中合计**：5 条（Qualcomm 2 + NVIDIA 2 + Google 1）

---

## 候选清单（每行：vendor + date + title + url）

1. Google | 2026-07-31 | Find out what's new in the Gemini app in July's Gemini Drop | https://blog.google/products-and-platforms/products/gemini/gemini-drop-july-2026/
2. NVIDIA | 2026-07-31 | Co-Designing AI Model Attention for Fast, Interactive Long-Context Inference | https://developer.nvidia.com/blog/co-designing-ai-model-attention-for-fast-interactive-long-context-inference/
3. NVIDIA | 2026-07-31 | NVIDIA Video Codec SDK 13.1: Zero-Copy Transcode, AV1 B-Frames, and Frame-Accurate Seek | https://developer.nvidia.com/blog/nvidia-video-codec-sdk-13-1-zero-copy-transcode-av1-b-frames-and-frame-accurate-seek/
4. Qualcomm | 2026-07-31 | Building Vision AI Pipelines on the Qualcomm Dragonwing IQ-9075 with QIM SDK, Edge Impulse, and Qt Framework | https://www.qualcomm.com/developer/blog/2026/07/vision-ai-factorypulse-iq9075-qim-sdk
5. Qualcomm | 2026-07-31 | Running GenAI with RAG and ASR on the Qualcomm Dragonwing IQ-9075 | https://www.qualcomm.com/developer/blog/2026/07/genai-rag-iq9075-factorypulse

---

## 丢弃记录（窗口内日期但 URL 未命中白名单）

| vendor | date | title | url | 丢弃原因 |
|---|---|---|---|---|
| vivo | 2026-07-31 | 更轻量、更稳定，vivo手机助力那达慕大会移动直播 | https://www.vivo.com.cn/brand/news/detail?id=1377&type=0 | 域名 vivo.com.cn 不在白名单（白名单只列 `vivo.com`；vivo.com.cn 是中国官方站，建议补入白名单） |
| Minimax | 2026-07-31 | MiniMax H3: An Open Model Breaking the Boundaries Between Tasks and Modalities | https://www.minimax.io/blog/minimax-h3 | 域名 minimax.io 不在白名单（任务列入"模型实验室"但白名单未收，建议补入） |

---

## 备注 / 局限

1. **WebSearch 不可用**：本环境 WebFetch 之外的搜索工具返回"无网络搜索能力"，故全程靠 WebFetch 直抓官方索引页。多家厂站（Samsung newsroom、Xiaomi mimo、OPPO news、Huawei news、StepFun 首页、Qualcomm blog/blog、Microsoft techcommunity、OpenAI /news /blog /index、Apple newsroom）出现 403/404/socket 关闭/超时或 JS 动态渲染导致静态 HTML 无文章列表，可能漏掉窗口内动态。建议下一轮用带浏览器渲染的工具（Chrome DevTools MCP）复核 Samsung / OpenAI / Xiaomi / Huawei / StepFun 这几家。
2. **窗口内仅 07-31 有命中**：08-01~08-03 各厂官方博客索引页均未显示新帖（多数厂最近帖停留在 07-27~07-30）。这可能反映 8 月初发布淡季，也可能受上述抓取限制影响。
3. **白名单缺口**：vivo.com.cn、minimax.io、deepseek.com、moonshot.cn（kimi.com）、zhipuai.cn、baichuan-ai.com 均为对应厂商官方域名但未列入 `vendor-whitelist.md`，导致这批实验室/中国厂的官方动态无法按硬约束收录。建议下次刷白名单时补入。
4. **端侧关联度**：Qualcomm 两条均为 Dragonwing IQ-9075 边缘设备上的端侧 AI 实践（Hexagon HTP 跑 Llama 3.2 3B/Whisper/视觉模型），与 edge_agent 主题高度相关；NVIDIA 两条偏通用推理/编解码；Google Gemini Drop 含 Gemini 3.6 Flash 等小模型更新，端侧相关。
