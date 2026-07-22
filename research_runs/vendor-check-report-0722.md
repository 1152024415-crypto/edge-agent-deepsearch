# 厂商官方动态逐厂检查报告

窗口：2026-07-17 ~ 2026-07-22（含两端）。WAIC 2026（07-17~20 上海）期间。
检索策略：WebFetch 对部分域名被网络阻断（openai.com/anthropic.com/mistral.ai/ai.meta.com/research.samsung.com/machinelearning.apple.com 早期被 block），改用 Bash curl + RSS/sitemap/HTML 日期解析兜底。WebSearch 工具本周不可用（返回自我否认/无结果），全程未用。

## 汇总

- 总候选数：35
- 命中厂商：7 家（NVIDIA、Apple、Samsung、Qualcomm、Meta、Honor、Qwen/Alibaba）
- 0 条厂商：其余厂商（详见下表）

## 逐厂命中

| # | 厂商 | 类型 | 状态 | 本周命中 | 备注 |
|---|---|---|---|---|---|
| 1 | Apple | 设备 | 已查 | 7 | machinelearning.apple.com RSS（rss.xml）直取，全部本周 research 博客 |
| 2 | Samsung | 设备 | 已查 | 3 | news.samsung.com/global 新闻列表，均为非 AI 产品发布（Galaxy Card/Louvre/Account） |
| 3 | Huawei | 设备 | 已查 | 0 | consumer.huawei.com、huawei.com/cn/en news、developer.huawei.com 多路径均无本周文章日期 |
| 4 | Qualcomm | 设备 | 已查 | 1 | qualcomm.com/news/releases 仅季度股息公告（07-17），相关度低 |
| 5 | MediaTek | 设备 | 已查 | 0 | mediatek.com/news、/technology/ai、/press-room 均无本周日期 |
| 6 | Xiaomi | 设备 | 已查 | 0 | mi.com 全球/中国 news 重定向或 3KB 跳转；mimo.xiaomi.com 与 /blog 无本周文章 |
| 7 | OPPO | 设备 | 已查 | 0 | oppo.com 各 cn/global/newsroom/news 路径均 404 或无本周日期 |
| 8 | vivo | 设备 | 已查 | 0 | vivo.com.cn/news、developers.vivo.com 无本周文章日期 |
| 9 | Honor | 设备 | 已查 | 1 | honor.com/cn/news 命中 WAIC 机器人手机发布（07-18，高相关） |
| 10 | Google | 模型 | 已查 | 0 | blog.google 主页有本周时间戳但无文章可解析（WebFetch/curl 均拿不到结构化文章列表）；developer.android.com/ai 无日期 |
| 11 | Microsoft | 模型 | 已查 | 0 | azure.microsoft.com/blog/feed RSS 无本周；techcommunity Azure AI Blog 是登录墙 SPA；microsoft.com/research/blog 403 |
| 12 | OpenAI | 模型 | 未确认 | 0 | openai.com/news、/blog、/sitemap.xml 均网络阻断（curl 000 / WebFetch 域名 block）|
| 13 | Anthropic | 模型 | 未确认 | 0 | anthropic.com/news、/sitemap.xml 网络阻断（curl 000 / WebFetch 域名 block）|
| 14 | Meta | 模型 | 已查 | 2 | about.fb.com/news 命中 2 条（均非 AI 模型发布：足球夏季、Threads 家长监督）；ai.meta.com/blog 域名被 block |
| 15 | NVIDIA | 模型 | 已查 | 6 | blogs.nvidia.com WebFetch 直取 6 条，Vera Rubin/SIGGRAPH/Wistron 等 |
| 16 | Mistral | 模型 | 已查 | 0 | mistral.ai/news 列表最新日期 July 9, 2026（窗口外）；本周无发布 |
| 17 | 面壁智能 ModelBest | 模型 | 已查 | 0 | modelbest.cn 主页无新闻列表/本周日期 |
| 18 | Qwen/Alibaba | 模型 | 已查 | 15 | alibabacloud.com/blog 命中本周 15 篇，含 WAIC Agent-Native、Qwen-Audio-3.0-TTS、Qwen-Coder-Qoder、AgentLoop、Wan-Streamer 等（多高相关）|
| 19 | DeepSeek | 模型实验室 | 已查 | 0 | deepseek.com 无 RSS/sitemap，主页为 SPA，本周日期仅为页面 now 时间戳非文章 |
| 20 | Moonshot | 模型实验室 | 已查 | 0 | moonshot.cn 最新 Kimi K3/PerceptionBench 发布 07-16（窗口外）；/rss.xml 与 /news 返回 nginx 默认页 |
| 21 | Zhipu 智谱 | 模型实验室 | 已查 | 0 | zhipuai.cn/zh/news 最新 updatedAt 2026-07-15（窗口外）|
| 22 | Minimax | 模型实验室 | 未确认 | 0 | minimax.chat 主域网络阻断（curl 000）|
| 23 | 百川 Baichuan | 模型实验室 | 已查 | 0 | baichuan-ai.com 主页/news 均无本周日期 |
| 24 | 阶跃星辰 StepFun | 模型实验室 | 已查 | 0 | stepfun.com 为 SPA（curl 仅 2KB 模板），公告在微信公众号，WebFetch 取不到深度页（符合 vendor-research-guide 备注）|

## 说明与限制

1. **网络阻断厂商（OpenAI / Anthropic / Minimax）**：openai.com、anthropic.com、minimax.chat 在本环境 curl 全部 000（连接失败），WebFetch 全部"Unable to verify domain"。这三家本周是否有官方发布未确认，倾向 0 条但无法证伪。建议人工补查 openai.com/news、anthropic.com/news、minimax.chat 官方渠道。
2. **SPA 限制（StepFun / DeepSeek / Moonshot / Google blog.google / Microsoft techcommunity）**：官网 JS 渲染，curl 拿不到动态文章列表；WebSearch 本周不可用无法补。
3. **Qualcomm 与 Samsung 收录相关度低**：Qualcomm 本周仅股息公告；Samsung 3 条均为非 AI 产品（Galaxy Card、卢浮宫、Account）。按"量优先、宁可相关度稍低"原则收录并标注。
4. **Qwen/Alibaba 多语言版本去重**：AgentRun、Self-Routing Multi-LLM 两篇各有韩文/日文版本，已只保留英文版本。
5. **Apple ML 7 条均为研究博客**（论文解读），非产品发布，但属 machinelearning.apple.com 官方发布，符合收录标准；其中 Environment-free Synthetic Data for API-Calling Agents 与端侧 agent 高度相关。
6. 所有候选 URL 均命中 vendor-whitelist.md 官方域名（blogs.nvidia.com、machinelearning.apple.com、news.samsung.com、qualcomm.com、about.fb.com、honor.com、alibabacloud.com）。
