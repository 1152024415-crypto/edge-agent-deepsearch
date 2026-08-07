# 厂商调研方法总结（调研记忆）

> 本文件是调研 agent 的厂商检索记忆，基于 `vendor-whitelist.md`（官方域名白名单）扩展。
> **端侧重点关注厂商举例**：Apple、Google、NVIDIA。这只是举例，其余厂商同样要覆盖，不许只搜这三家。
> 规范官方来源：9 家设备厂商 + 10 家模型厂商（含 NVIDIA/StepFun）+ 5 家模型实验室补充来源；另查 8 家中国互联网公司研究项目。完整集合由 `agent/research_collection.py` 机械校验。
> 不可违反规则：非论文条目必须命中 `vendor-whitelist.md` 官方域名；公司项目按 arXiv affiliation + GitHub org 搜；不拿新闻、社媒、GitHub release、二手解读冒充官方。

## 通用检索方法

### arXiv affiliation 搜法（公司项目主力路径）

arXiv 自身搜索只匹配标题和摘要，不直接按作者 affiliation 过滤。抓公司项目的实操路径：

1. **websearch 全文匹配**：`site:arxiv.org "Kuaishou"` 加主题词（如 `mobile agent`），命中 affiliation 出现在正文 / 作者列表的论文。
2. **邮箱域名反查**：很多公司论文作者邮箱是公司域名（如 `@meituan.com`、`@vivo.com`），用 `"@meituan.com" arxiv` 这类查询能定位。
3. **Semantic Scholar / Google Scholar**：按 affiliation 字段过滤更准，配合主题词 `edge agent`、`on-device LLM`。
4. **GitHub org 论文链接**：公司研究 GitHub 仓库 README 常挂论文 PDF 和 arXiv 链接，是 affiliation 之外最可靠的一手来源。

### 官方动态识别（非论文条目硬约束）

- 只认 `vendor-whitelist.md` 列出的官方域名及其子域名。
- 官方技术博客 / 官方产品发布可收录，`source_tier=官方动态`，排序最前，必须命中官方域名。
- 新闻站、社媒、第三方解读、GitHub release notes、公众号搬运一律排除。

---

## 设备厂商（9 家）

| 厂商 | 官方动态来源 | websearch 关键词 | arXiv affiliation | GitHub / 重要页面 |
|---|---|---|---|---|
| Apple | `machinelearning.apple.com`（ML 研究博客）、`developer.apple.com`（Apple Intelligence / CoreAI 文档） | `"Apple Intelligence" on-device`、`site:machinelearning.apple.com`、`CoreAI`、`Apple Foundation Models` | `Apple` / `Apple Inc`（论文极少，主要靠官方博客） | `machinelearning.apple.com`、`developer.apple.com/machine-learning` |
| Samsung | `research.samsung.com/blog`、`research.samsung.com/artificial-intelligence`、`news.samsung.com` | `"Samsung Gauss"`、`"Galaxy AI" on-device`、`site:research.samsung.com` | `Samsung Research`、`Samsung AI Center (SAIC)`、`Samsung Electronics` | `research.samsung.com/blog`（AI 主题筛选） |
| Huawei | `developer.huawei.com/consumer/cn/hiai/`（HiAI Foundation）、`huaweicloud.com` Pangu 产品页、`huawei.com` | `"Huawei Pangu"`、`"HiAI"`、`"HarmonyOS AI"`、`site:developer.huawei.com` | `Huawei`、`Huawei Noah's Ark Lab`、`HiSilicon`、`海思` | `developer.huawei.com` HiAI、`huaweicloud.com` Pangu |
| Qualcomm | `aihub.qualcomm.com`（AI Hub 模型库）、`qualcomm.com/developer`、`developer.qualcomm.com`（技术博客） | `"Qualcomm AI Hub"`、`"Hexagon NPU"`、`site:aihub.qualcomm.com` | `Qualcomm AI Research`、`Qualcomm` | `github.com/qualcomm/ai-hub-models`、`aihub.qualcomm.com/models` |
| MediaTek | `neuropilot.mediatek.com`、`neuropilot-developer.mediatek.com`、`mediatek.com/technology/ai` | `"MediaTek NeuroPilot"`、`"MediaTek edge AI"`、`site:mediatek.com` | `MediaTek`（论文少，主要靠官方门户） | `neuropilot.mediatek.com`、`mediatek.com/technology/ai` |
| Xiaomi | `mimo.xiaomi.com`（MiMo 模型博客）、`mi.com/global/brand/ai/xiaomi-hyperai`（HyperAI） | `"Xiaomi MiMo"`、`"Xiaomi HyperAI"`、`"HyperVL"`、`site:mimo.xiaomi.com` | `Xiaomi`、`HyperAI Team, Xiaomi Corporation`、`Xiaomi AI Lab`、`小米` | `mimo.xiaomi.com/blog`（HyperVL 等端侧多模态论文挂此） |
| OPPO | `oppo.com`（AndesGPT 产品）、OPPO 开发者社区、`coloros.com` AI 板块 | `"OPPO AndesGPT"`、`"OPPO AI Center"`、`"ColorOS AI"`、`"安第斯大模型"` | `OPPO`、`OPPO Research Institute`、`OPPO AI Lab` | `oppo.com` AndesGPT、OPPO 开发者平台 |
| vivo | `developers.vivo.com/product/ai/bluelm`（蓝心大模型文档）、`vivo.com` | `"vivo BlueLM"`、`"蓝心大模型"`、`site:developers.vivo.com` | `vivo`、`vivo AI Lab`、`vivo AI 全球研究院` | `github.com/vivo-ai-lab/BlueLM`、`developers.vivo.com` BlueLM |
| Honor | `honor.com`（MagicOS AI、YOYO 智能体） | `"Honor MagicOS AI"`、`"Honor YOYO"`、`"荣耀端侧大模型"` | `Honor`、`荣耀`（论文极少，主要靠官方发布） | `honor.com` MagicOS、YOYO 智能体 |

> 设备厂商研究产出偏工程和官方发布，arXiv affiliation 命中率低于模型厂商。优先抓官方博客和产品发布，再补 affiliation 论文。

---

## 模型厂商（10 家，含 NVIDIA）

| 厂商 | 官方动态来源 | websearch 关键词 | arXiv affiliation | GitHub / 重要页面 |
|---|---|---|---|---|
| Google | `blog.google`、`ai.google.dev`、`developers.googleblog.com`（android-developers）、`developer.android.com/ai` | `"Gemini Nano"`、`"Google MediaPipe"`、`"Android AICore"`、`site:ai.google.dev on-device` | `Google`、`Google Research`、`Google DeepMind` | `ai.google.dev`、`developer.android.com/ai` |
| Microsoft | `techcommunity.microsoft.com`（Phi 博客）、`azure.microsoft.com/blog`、`microsoft.com/research` | `"Microsoft Phi-4"`、`"Phi-3-mini"`、`"Windows Copilot Runtime"`、`site:techcommunity.microsoft.com` | `Microsoft Research`、`Microsoft` | `techcommunity.microsoft.com`、`microsoft.com/research` |
| OpenAI | `openai.com/research`、`openai.com/blog` | `site:openai.com`、`"OpenAI" edge on-device`、`"OpenAI" function calling mobile` | `OpenAI` | `openai.com/research` |
| Anthropic | `anthropic.com/research`、`anthropic.com/news` | `site:anthropic.com`、`"Anthropic Haiku"`、`"Claude" edge deployment` | `Anthropic` | `anthropic.com/research` |
| Meta | `ai.meta.com`（博客 + 研究）、`about.fb.com` | `"Meta Llama" on-device`、`"Llama 3.2 1B 3B"`、`"Llama 4 Scout"`、`site:ai.meta.com` | `Meta AI`、`Meta FAIR`、`Fundamental AI Research` | `ai.meta.com/blog`、`github.com/meta-llama` |
| NVIDIA | `developer.nvidia.com/nim`、`blogs.nvidia.com`、`developer.nvidia.com/blog`（技术博客）、`build.nvidia.com` | `"NVIDIA NIM" on-device`、`"Project DIGITS"`、`"NVIDIA ACE"`、`site:blogs.nvidia.com` | `NVIDIA`、`NVIDIA Research` | `developer.nvidia.com/nim`、`build.nvidia.com`、`github.com/NVIDIA` |
| Mistral | `mistral.ai`（news / research）、`docs.mistral.ai` | `"Mistral Ministral"`、`"Ministral 3B 8B"`、`site:mistral.ai` | `Mistral AI` | `mistral.ai/news`、`github.com/mistralai` |
| 面壁智能 ModelBest | `modelbest.cn`、`modelbest.cn/en` | `"MiniCPM"`、`"面壁智能"`、`"MiniCPM-V"`、`site:modelbest.cn` | `ModelBest`、`面壁智能`、`OpenBMB` | `github.com/OpenBMB/MiniCPM`、`modelbest.cn` |
| 阶跃星辰 StepFun | `stepfun.com`（官网 JS 渲染，公告多在微信公众号，WebFetch 取不到深度页） | `"阶跃星辰"`、`"STEPX"`、`"Step 系列"`、`"印奇"`、`site:stepfun.com` | `StepFun`、`阶跃星辰` | `stepfun.com`、官方公众号（2026-07 发布全球首个 AI 智能体手机 STEPX Neo+智能体 OS） |
| Qwen（阿里云） | `qwenlm.github.io`、`alibabacloud.com` 博客 | `"Qwen2.5" on-device`、`"Qwen Mobile-Agent"`、`site:qwenlm.github.io` | `Alibaba`、`Alibaba Cloud`、`Qwen Team`、`阿里云` | `github.com/QwenLM`、`qwenlm.github.io` |

> 模型厂商 arXiv affiliation 命中率高，论文和官方技术报告都多。端侧关注小参数量变体（MiniCPM、Qwen 0.5B/1.5B/3B、Llama 1B/3B、Ministral 3B/8B、Phi-3-mini、Gemini Nano）。

## 模型实验室补充来源（5 家，强制检查）

| 厂商 | 官方来源 | 补查重点 |
|---|---|---|
| DeepSeek | `deepseek.com`、`api-docs.deepseek.com`、GitHub `deepseek-ai` | 新仓、重大 commit、推理内核、HF checkpoints；不能只查 arXiv |
| Moonshot/Kimi | `kimi.com`、`moonshot.cn` | 官方博客、模型发布、长上下文与本地部署动态 |
| Zhipu | `zhipuai.cn`、`bigmodel.cn` | GLM 小模型、Agent、端侧/工具调用更新 |
| MiniMax | `minimax.io` | 新模型、语音/多模态、小模型和推理部署 |
| Baichuan | `baichuan-ai.com` | 新模型、医疗以外的通用推理与端侧部署动态 |

这 5 家即使窗口内 0 命中也必须写入 `collection-manifest.json` 的 `vendors_checked`；0 是结果，不是跳过检查。

---

## 中国互联网公司研究项目（8 家）

> 这 8 家优先级仅低于大厂官方，`source_tier=公司项目`（排序低于官方动态和开源大项目）。多数没有独立官方研究门户，**主力靠 arXiv affiliation + GitHub org 搜法**。`vendors` 字段必填公司英文名，并在 `score_reason` 附 affiliation 证据来源。

| 公司 | 官方动态来源 | websearch 关键词 | arXiv affiliation | GitHub org / 重要项目 |
|---|---|---|---|---|
| 快手 Kuaishou | `kuaishou.com`（无独立研究门户，靠 arXiv + GitHub） | `"Kuaishou" arxiv`、`"快手" agent`、`"KwaiYii"` | `Kuaishou`、`Kuaishou Technology`、`Kwai`、`快手` | `github.com/kwai`（通用开源）、`github.com/Kwai-Kolors`（视觉生成 Kolors）、`github.com/KwaiKEG`（KwaiAgents、KwaiYii） |
| 字节 ByteDance | `seed.bytedance.com`（Seed 团队论文 + 研究）、`se-research.bytedance.com`（SE Lab） | `"ByteDance" arxiv`、`site:seed.bytedance.com`、`"字节跳动" agent` | `ByteDance`、`ByteDance Seed`、`字节跳动` | `github.com/bytedance`、`github.com/ByteDance-AI`；项目：Seed2.1、Trae Agent、MarsCode Agent |
| 腾讯 Tencent | `ailab.tencent.com`（AI Lab）、`ai.tencent.com` | `"Tencent AI Lab" arxiv`、`site:ailab.tencent.com`、`"腾讯" agent` | `Tencent`、`Tencent AI Lab`、`Tencent ARC Lab` | `github.com/tencent-ailab`、`github.com/TencentARC`、`github.com/Tencent`；项目：IP-Adapter、persona-hub、Hunyuan |
| 百度 Baidu | `ai.baidu.com`、`research.baidu.com`（Baidu Research） | `"Baidu" arxiv`、`site:ai.baidu.com`、`"百度" ERNIE agent` | `Baidu`、`Baidu Research`、`Institute of Deep Learning (IDL)` | `github.com/baidu`；项目：ERNIE、文心一言、PaddlePaddle |
| 美团 Meituan | 无独立研究门户，靠 arXiv affiliation + 邮箱域名 `@meituan.com` | `"Meituan" arxiv`、`"美团" agent 推荐` | `Meituan`（邮箱 `@meituan.com`） | `github.com/meituan`（工程为主，无突出研究 org）。研究多在推荐 / 检索 / 广告，端侧 agent 较少，按 affiliation 抓 |
| 京东 JD | 无独立研究门户，靠 arXiv affiliation | `"JD.com" arxiv`、`"京东" agent` | `JD.com`、`Jingdong`、`京东` | `github.com/jd-opensource`。研究多在推荐 / 供应链 / NLP |
| 拼多多 Pinduoduo | 无独立研究门户，靠 arXiv affiliation | `"Pinduoduo" arxiv`、`"PDD" arxiv`、`"拼多多" agent` | `Pinduoduo`、`PDD`、`拼多多` | 公开论文较少，搜索时放宽到 `PDD` / `Pinduoduo` 全文匹配 |
| 网易 Netease | 无独立研究门户，靠 arXiv affiliation | `"NetEase" arxiv`、`"网易" agent` | `NetEase`、`NetEase Games`、`网易` | `github.com/netease`、`github.com/netease-community`。研究多在游戏 AI / NLP / 音乐推荐 |

> 中国互联网公司公开论文未必聚焦端侧，但 affiliation 命中即算公司项目，优先级高于学校项目。抓到的论文若涉及 agent / 多模态 / 轻量化，即使不是手机端，也按公司项目收录并标 `vendors`。

---

## 与其他文档的关系

- `vendor-whitelist.md`：官方域名白名单和 affiliation 关键标识，是评分和收录的硬约束来源。本文件只补充检索方法，不重复定义白名单，不改它。
- `docs/agent-guide/research-prompt.md`：调研子 agent 的搜索提示词，发起子 agent 时注入全文。本文件被它引用，作为厂商检索方法展开。
- `docs/agent-guide/validation-rules.md`：收录和打分规则。本文件的优先级区间和 `vendors` 字段要求与它一致。
