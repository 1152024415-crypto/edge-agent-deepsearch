# 厂商官方动态采集逐厂检查报告

- 采集窗口：2026-07-17 ~ 2026-07-24（含两端）
- 采集方式：WebFetch 直抓各厂官方博客/新闻索引页；WebSearch 工具本周不可用（返回拒答），全程未用。
- 域名硬约束：所有候选 URL 均命中 `docs/references/vendor-whitelist.md` 官方域名或子域。
- 总候选数：32 条

## 设备厂商（9 家）

| 厂商 | 已查 | 本周命中 | 说明 |
|---|---|---|---|
| Apple | 已查 machinelearning.apple.com | 0 | 索引页最新可见为 2026-07-04「Apple at ICML 2026」，窗口内无新帖。 |
| Samsung | 已查 news.samsung.com/global（news.samsung.com 子域，白名单内） | 11 | Galaxy Unpacked July 2026 集中发布（07-20~07-23）：Z Fold8 Ultra/Fold8/Flip8、Watch Ultra2/Watch9、智能眼镜、Health Assistant Beta AI、Galaxy Card、Art Store 卢浮宫、Samsung Account。 |
| Huawei | 已查 consumer.huawei.com/cn/press/ | 0 | 新闻中心 JS 动态加载，静态抓取取不到文章列表；consumer 首页无日期新闻。本周未取得可验证官方动态。 |
| Qualcomm | 已查 qualcomm.com/developer/blog + qualcomm.com/news | 2 | developer 博客最新 07-07（窗口外）；newsroom 命中 07-22 与三星扩展合作、07-17 季度股息（财务，相关度低）。 |
| MediaTek | 已查 mediatek.com/technology/ai | 0 | 仅见 2022-2023 学术论文链接，无本周官方博客/发布。 |
| Xiaomi | 已查 mimo.xiaomi.com/blog | 0 | 最新可见为 2025-12-16 MiMo-V2-Flash，窗口内无新帖。 |
| OPPO | 已查 oppo.com/cn/newsroom/ | 0 | 新闻中心 JS 动态加载，静态抓取取不到文章列表。 |
| vivo | 已查 developers.vivo.com/product/ai/bluelm、vivo.com/cn/news（404） | 0 | 开发者页仅页头无内容；/cn/news 返回 404。 |
| Honor | 已查 honor.com/global/news/ | 0 | 新闻室最新为 2026-06-09，窗口内无新帖。注：本周 WAIC 2026（07-17~20）荣耀有机器人手机相关动态（见 git log "WAIC周Honor机器人手机"），但未落在 honor.com 官方新闻室可抓取页面，按硬约束不计。 |

## 模型厂商（9 家）

| 厂商 | 已查 | 本周命中 | 说明 |
|---|---|---|---|
| Google | 已查 blog.google、blog.google/technology/ai/、developers.googleblog.com/en/ | 3 | blog.google 首页 Top Story（如 "Introducing three new Gemini models"、"3 Google updates from Galaxy Unpacked 2026"）无可见日期/URL（WebFetch 转 markdown 丢失 href），无法确认是否落在窗口内，未收录；developers.googleblog.com（googleblog.com 子域，白名单内）命中 3 条：Run Ray on TPU Part1(07-20)/Part2(07-24)、Scaling Agentic RL with Tunix(07-21)。 |
| Microsoft | 已查 microsoft.com/en-us/research/blog/ | 0 | 索引页最新 2026-07-13，窗口内无新帖。 |
| OpenAI | 已查 openai.com/research、openai.com/blog、openai.com/index、openai.com/news | 0 | 全部返回 HTTP 403（反爬），WebSearch 不可用，本周无法从官方域名取到可验证动态。建议后续用浏览器或 MCP 抓取。 |
| Anthropic | 已查 anthropic.com/news | 5 | Claude Opus 5(07-24)、Economic Futures 研究议程(07-22)、Economic Index 连接器(07-22)、Public First Action 捐赠(07-21)、罕见病研究资助(07-20)。 |
| Meta | 已查 ai.meta.com/blog/ | 1 | Genesis Mission 项目(07-21)，与伯克利国家实验室合作，使用 SAM/DINO。 |
| NVIDIA | 已查 blogs.nvidia.com | 10 | Vera Rubin 系列（07-17 后训练、07-21 性能/瓦+token 成本、07-21 Spectrum-6、07-20 BMS AI 工厂）、Build in America(07-21)、Wistron 德州工厂(07-21)、海军研究生院超算(07-22)、医学物理开源(07-22)、AI Summit Korea(07-23)、GeForce NOW(07-23)。 |
| Mistral | 已查 mistral.ai/news | 0 | 最新 07-09（窗口前），窗口内无新帖。 |
| 面壁智能 ModelBest | 已查 modelbest.cn、modelbest.cn/en、modelbest.cn/blog(404) | 0 | 官网为产品落地页+公众号/飞书外链，无独立可抓取博客索引。 |
| Qwen | 已查 qwenlm.github.io | 0 | 最新可见为 2025-09-23 Qwen3Guard，窗口内无新帖。 |

## 模型实验室 + 阶跃星辰

> 注：DeepSeek/Moonshot/Zhipu/Minimax/百川 的官方域名（deepseek.com、moonshot.cn/kimi.com、zhipuai.cn/bigmodel.cn、minimax.io、baichuan-ai.com）**未列入 `vendor-whitelist.md`**。本次均命中 0 条，不影响结果；但建议白名单补登这些实验室域名，避免未来有动态时被硬约束误弃。阶跃星辰 stepfun.com 已在白名单。

| 厂商 | 已查 | 本周命中 | 说明 |
|---|---|---|---|
| DeepSeek | 已查 deepseek.com、platform.deepseek.com | 0 | 官网仅显示 DeepSeek-V4 预览公告，无日期；无独立博客索引。 |
| Moonshot | 已查 moonshot.cn、kimi.com/blog | 0 | kimi.com/blog 最新 Kimi K3 与 PerceptionBench 均为 07-16，窗口前 1 天，未命中。 |
| Zhipu | 已查 bigmodel.cn、zhipuai.cn、zhipuai.cn/news | 0 | 开放平台 JS loading 占位，news 页无日期无链接，无法取到窗口内可验证动态。 |
| Minimax | 已查 minimax.io/blog | 0 | 最新 2026-06-09 MaxProof，窗口内无新帖。 |
| 百川 | 已查 baichuan-ai.com、baichuan-ai.com/news(404) | 0 | 官网仅标题无文章列表。 |
| 阶跃星辰 StepFun | 已查 stepfun.com、stepfun.com/news(404) | 0 | 官网 JS 渲染，深度页 WebFetch 取不到（与 research-guide 记录一致）；WAIC 期间 STEPX Neo 智能体手机等发布多在微信公众号，按硬约束不计。 |

## 命中数一览

- Anthropic: 5
- NVIDIA: 10
- Samsung: 11
- Google: 3
- Meta: 1
- Qualcomm: 2
- 其余 18 家（Apple/Huawei/MediaTek/Xiaomi/OPPO/vivo/Honor/Microsoft/OpenAI/Mistral/面壁/Qwen/DeepSeek/Moonshot/Zhipu/Minimax/百川/阶跃星辰）: 0

合计 32 条。
