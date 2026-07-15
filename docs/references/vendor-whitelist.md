# 大厂白名单（affiliation 判定）

> 供 `source_tier=官方动态` 官方域名校验 + 公司 affiliation 识别使用。当前评分为 2 维（relevance + contribution，0-20），无"大厂关联度"维度。作者 affiliation 命中以下即标 `公司项目`（vendors 必填）。
> **随发现新厂商 / 机构追加**（免疫系统：漏判一次就补一条标识）。

## 设备厂商
| 厂商 | 关键标识（机构名 / 邮箱域名 / 产品线） |
|---|---|
| Apple | Apple / apple.com / Apple Intelligence / CoreAI / AX |
| Samsung | Samsung / Samsung Research / Gauss / Galaxy AI / Exynos |
| Huawei | Huawei / 海思 / HiSilicon / HarmonyOS / Pangu / HiAI / Ascend |
| Qualcomm | Qualcomm / AI Hub / Hexagon |
| MediaTek | MediaTek / NeuroPilot / APU |
| 小米 | Xiaomi / 小米 / MiLM / HyperAI / AISP / 澎湃 |
| OPPO | OPPO / AndesGPT / ColorOS AI |
| vivo | vivo / BlueLM / BlueOS / 蓝心 |
| 荣耀 | Honor / 荣耀 / MagicOS / YOYO |

## 模型厂商
| 厂商 | 关键标识 |
|---|---|
| Google | Google / Google Research / Gemini Nano / MediaPipe / AICore |
| Microsoft | Microsoft / Microsoft Research / Phi / Copilot Runtime / DirectML |
| OpenAI | OpenAI |
| Anthropic | Anthropic / Haiku |
| Meta | Meta / Meta AI / FAIR / Llama |
| NVIDIA | NVIDIA / nv / TensorRT / TensorRT-LLM / Jetson / DGX |
| Mistral | Mistral / Ministral |
| 面壁智能 | ModelBest / 面壁 / MiniCPM |
| Qwen | Alibaba / 阿里云 / Qwen / Mobile-Agent |
| 阶跃星辰 StepFun | StepFun / 阶跃星辰 / STEPX / 印奇 / Step 系列 |

## 学术顶会顶刊（信息质量维度参考）
NeurIPS / ICML / ICLR / MobiSys / SenSys / ASPLOS / CVPR / ICCV / ACL / EMNLP / AAAI / IJCAI / TPAMI / TNNLS / ToN

## 官方来源域名（非论文收录硬约束）

非论文条目只允许大厂官方技术博客或官方产品发布。候选 URL 必须命中以下官方域名或其子域名，不能使用新闻、社媒、GitHub release、论坛或二手解读。

Apple: `apple.com`, `developer.apple.com`, `machinelearning.apple.com`
Google: `google.com`, `blog.google`, `googleblog.com`, `android-developers.googleblog.com`, `ai.google.dev`
Microsoft: `microsoft.com`, `azure.microsoft.com`, `techcommunity.microsoft.com`
OpenAI: `openai.com`
Anthropic: `anthropic.com`
Meta: `meta.com`, `ai.meta.com`, `about.fb.com`
NVIDIA: `nvidia.com`, `blogs.nvidia.com`, `developer.nvidia.com`
Samsung: `samsung.com`, `research.samsung.com`
Huawei: `huawei.com`
Qualcomm: `qualcomm.com`
MediaTek: `mediatek.com`
Xiaomi: `mi.com`, `xiaomi.com`
OPPO: `oppo.com`
vivo: `vivo.com`
Honor: `honor.com`
Alibaba/Qwen: `alibabacloud.com`, `qwenlm.github.io`
Mistral: `mistral.ai`
阶跃星辰 StepFun: `stepfun.com`
