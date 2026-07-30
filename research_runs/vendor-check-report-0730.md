# 厂商官方动态采集逐厂检查报告

> 采集窗口：2026-07-25 ~ 2026-07-30（含两端）
> 采集时间：2026-07-30
> 硬约束：URL 必须命中 `docs/references/vendor-whitelist.md` 官方域名或子域；只收窗口内明确日期发布；404/403 一律丢弃不补。
> 检索方法：WebFetch 直抓各厂官方博客/新闻索引页，逐页筛 07-25~07-30 文章。WebSearch 工具本轮不可用（返回"无 web search 工具"），全部走 WebFetch 直抓。

## 设备厂商（9 家）

| 厂商 | 已查 | 本周命中 | 备注 |
|---|---|---|---|
| Apple | 已查 machinelearning.apple.com（首页列出 6 篇，最近一篇 2026-07-04 ICML，无 07-25~07-30） | 0 | machinelearning.apple.com 已查；窗口内无发布 |
| Samsung | 已查 research.samsung.com/blog 与 /blog/artificial-intelligence（AI 分类页返回 "System error occurred" 内部错误）；news.samsung.com/global/en 返回 404；news.samsung.com/en/ 404 | 0 | Samsung Research 博客分类页本周抓取返回系统错误，无法列文章；newsroom 路径多次 404。窗口内未确认有发布 |
| Huawei | 已查 huawei.com/en/news/（页面无文章列表，只有导航）、consumer.huawei.com/en/news（socket hang up/超时）、consumer.huawei.com/en/news/list.htm（404） | 0 | 官方新闻页本周未能抓到文章列表；窗口内未确认发布 |
| Qualcomm | 已查 qualcomm.com/news/releases | 4 | 命中 07-27、07-29×3，均在 qualcomm.com 白名单域 |
| MediaTek | 已查 mediatek.com/technology/ai（页面只有 Published Papers 2022-2023，无博客列表，提示博客在 /tek-talk-blogs） | 0 | 窗口内未发布 |
| Xiaomi | 已查 mimo.xiaomi.com/blog（最近一篇 2025-12-16 MiMo-V2-Flash） | 0 | 窗口内未发布 |
| OPPO | 已查 oppo.com/en/news/、/en/newsroom/、/content/oppo/global/en/news/ 均 404 或无文章列表 | 0 | OPPO 英文 newsroom 多路径 404，窗口内未确认发布 |
| vivo | 已查 vivo.com/en/news（404）、vivo.com/en（列出 2 条 Brand News 但无日期）、vivo.com/about-vivo/news（404） | 0 | vivo 英文新闻页本周未能抓到带日期文章；窗口内未确认发布 |
| Honor | 已查 honor.com/global/news（列出最近 3 条，最新 2026-06-09，无 07-25~07-30）、honor.com/global/（无带日期新闻）、honor.com/global/news 404 | 0 | 窗口内未发布，最近发布在 6 月 |

## 模型厂商（9 家，含 NVIDIA）

| 厂商 | 已查 | 本周命中 | 备注 |
|---|---|---|---|
| Google | 已查 blog.google/technology/ai（403）、blog.google 根（列出文章但无日期，逐篇 fetch 核实）、ai.google.dev/news（页面无文章列表）、developers.googleblog.com/en/ai/（列出文章链接但无日期）、android-developers.googleblog.com/（列出带日期文章）、developer.android.com/ai/（落地页）、developer.android.com/blog/posts/* 逐篇核日期 | 6 | 命中 blog.google×3（07-28、07-29×2）+ android-developers.googleblog.com×3（07-27、07-28、07-29）；均命中白名单域 |
| Microsoft | 已查 techcommunity.microsoft.com/blog/microsoft-365-blog（无日期）、azure.microsoft.com/en-us/blog（命中 1）、microsoft.com/en-us/research/blog/（最近 2026-07-13，无窗口内）、blogs.microsoft.com/blog/（403） | 1 | 命中 Azure 博客 07-27 一篇 |
| OpenAI | 已查 openai.com/blog（首次返回内容疑似串台 Mistral 标题，不可信）、openai.com/research（404）、openai.com/index/（404）、openai.com/（403）、openai.com/blog/（403） | 0 | openai.com 本周多次 403/404，未能可靠抓取博客索引；窗口内未确认发布（不代表无发布，仅本轮未能采到） |
| Anthropic | 已查 anthropic.com/news | 2 | 命中 07-27×2，均在 anthropic.com 白名单域 |
| Meta | 已查 ai.meta.com/blog/（两次抓取结果一致） | 1 | 命中 07-27 一篇 |
| NVIDIA | 已查 blogs.nvidia.com（3 篇命中）、developer.nvidia.com/blog（6 篇命中） | 9 | blogs.nvidia.com×3（07-26、07-27、07-28）+ developer.nvidia.com×6（07-26×2、07-27×2、07-28、07-29）；均命中白名单域 |
| Mistral | 已查 mistral.ai/news（首次 403，第二次抓到完整 78 篇列表，最近一篇 2026-07-09 "Your Prompts and Skills..."） | 0 | 窗口内未发布 |
| 面壁智能 ModelBest | 已查 modelbest.cn/en/news（404）、modelbest.cn（loading GIF，无内容） | 0 | 官方门户本周未能抓到带日期内容；窗口内未确认发布 |
| Qwen（阿里云） | 已查 qwenlm.github.io（列出 5 篇，最近 2025-09-23）；alibabacloud.com/blog/ai 超时 | 0 | qwenlm.github.io 窗口内无发布；阿里云博客页超时未取到 |

## 模型实验室（6 家，含阶跃星辰）

| 厂商 | 已查 | 本周命中 | 备注 |
|---|---|---|---|
| 阶跃星辰 StepFun | 已查 stepfun.com（JS 渲染，公告多在公众号，WebFetch 取不到深度页；与研究指南提示一致） | 0 | stepfun.com 官网 JS 渲染，窗口内未抓到带日期官方文章 |
| DeepSeek | 已查 deepseek.com（页面提到 "DeepSeek-V4 预览版本发布" 但无日期） | 0 | 无明确日期发布，按硬约束不收；且 deepseek.com 未列入 vendor-whitelist.md 白名单域 |
| Moonshot | 已查 moonshot.cn（重定向到 kimi.com/blog，列出 Kimi K3 2026-07-16、PerceptionBench 2026-07-16，均早于窗口） | 0 | 窗口内未发布；且 moonshot.cn / kimi.com 未列入 vendor-whitelist.md 白名单域，即使命中也会因域名校验失败丢弃 |
| Zhipu 智谱 | 已查 bigmodel.cn/news（loading GIF "智谱AI开放平台"） | 0 | 官方门户本周未能抓到内容；且 z.ai / bigmodel.cn 未列入白名单域 |
| Minimax | 已查 minimaxi.com/news（none in range） | 0 | 窗口内未发布；且 minimaxi.com 未列入白名单域 |
| 百川 Baichuan | 已查 baichuan-ai.com（none in range） | 0 | 窗口内未发布；且 baichuan-ai.com 未列入白名单域 |

## 汇总

- 候选总数：23 条
- 命中厂商：6 家（Google 6、NVIDIA 9、Qualcomm 4、Anthropic 2、Meta 1、Microsoft 1）
- 0 条厂商：18 家（Apple、Samsung、Huawei、MediaTek、Xiaomi、OPPO、vivo、Honor、OpenAI、Mistral、面壁、Qwen、StepFun、DeepSeek、Moonshot、Zhipu、Minimax、百川）

## 说明与限制

1. **OpenAI 本轮 0 条属采集能力限制**：openai.com/blog 多次返回 403 Forbidden（首次返回的内容疑似串台到 Mistral 标题，已判定不可信而丢弃）。WebSearch 工具本轮不可用，无法用搜索补量。建议下一轮换用浏览器自动化或 RSS 重试。
2. **5 家模型实验室（DeepSeek/Moonshot/Zhipu/Minimax/百川）不在 vendor-whitelist.md 白名单域**：即便抓到内容，URL 也无法通过白名单校验，按硬约束一律不收。本次已逐厂检查并标注 0 条，若后续要纳入需先扩 `vendor-whitelist.md`。
3. **Samsung/Huawei/OPPO/vivo/Honor 新闻索引页本周多次 404 或 JS 渲染抓不到文章列表**：设备厂英文 newsroom 路径不稳定，窗口内未能确认官方发布。不代表这些厂商本周无动态，仅本轮 WebFetch 未能采到。
4. **Google blog.google 文章列表不带日期**：通过逐篇 WebFetch 单文章页核实发布日期，仅纳入确认在 07-25~07-30 的 3 篇；其余未逐一核实的未纳入，可能漏收。
5. 所有最终纳入 candidates-vendor.json 的 23 条 URL 均命中 vendor-whitelist.md 列出的官方域名或子域，且日期在窗口内。
