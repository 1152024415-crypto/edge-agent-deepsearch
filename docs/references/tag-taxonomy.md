# 标签词表（人读版，4 维 dim:val）

> 机器可读版在 `data/tags.yaml`；两边同步以 `data/tags.yaml` 为准。
> 调研 agent 给每条工作打 **1-8 个标签**，格式 `维度:值`（如 `方向:量化`、`硬件:NPU`、`模型:Llama`），多标签，不是非此即彼。一个工作可同时挂多个标签（如一篇「端侧 VLM 量化部署」挂 `方向:端侧agent`+`方向:多模态`+`方向:量化`+`方向:编译部署`）。
> 页面按 4 维 faceted 筛选展示（方向/应用/硬件/模型），紧凑列表，不做 6 段深度分析。
> **方向 / 应用 / 硬件** 为受控词表（必须命中）；**模型** 为半自由（starter 列表，新模型可提议后加入 `data/tags.yaml`）。公司不进 tags，用 `vendors` 字段。

## 方向（受控）

- `方向:端侧agent` — 端侧/移动/嵌入式上的 agent 系统（核心标签，命中即挂）
- `方向:推理框架` — vLLM/SGLang/llama.cpp/ExecuTorch 等框架工作
- `方向:KV cache` — KV 缓存管理/压缩/offload
- `方向:量化` — 低比特量化（GPTQ/AWQ/INT4/INT8）
- `方向:剪枝稀疏` — 剪枝/稀疏化
- `方向:投机解码` — speculative decoding/Medusa/EAGLE
- `方向:蒸馏` — 知识蒸馏
- `方向:高效注意力` — 注意力变体/高效注意力
- `方向:高效推理` — 高效推理/推理加速
- `方向:稀疏注意力` — 稀疏注意力
- `方向:调度服务` — 推理调度/服务系统/批处理/连续批处理
- `方向:云端serving` — 数据中心/云端推理服务系统（多模型 serving、集群容错、大模型 server 推理）；与端侧区分，单独标注
- `方向:记忆` — agent 记忆/上下文压缩/持久化
- `方向:工具调用` — function calling/tool use
- `方向:规划推理` — planning/CoT/reasoning
- `方向:多模态` — VLM/视觉语言
- `方向:模型架构` — 新架构/注意力变体
- `方向:MoE` — Mixture-of-Experts
- `方向:端云协同` — 端云协同/弹性卸载
- `方向:能耗功耗` — 能耗/热/电池感知
- `方向:编译部署` — 部署/导出/编译优化
- `方向:评测基准` — benchmark/评测集
- `方向:安全隐私` — 安全/隐私/注入防御
- `方向:联邦学习` — federated/分布式训练
- `方向:测试时自适应` — test-time adaptation/动态多模态融合
- `方向:端侧训练` — 端侧/设备端训练

## 应用（受控）

- `应用:OCR` — 端侧 OCR/文档理解
- `应用:语音` — 语音/ASR/TTS
- `应用:RAG` — 检索增强生成
- `应用:关系抽取` — 信息抽取
- `应用:fault-detection` — 故障检测
- `应用:IoT命令` — IoT 设备控制
- `应用:代码` — 代码生成/理解
- `应用:长上下文推理` — 长上下文
- `应用:视频` — 视频/流媒体
- `应用:机器人` — 机器人/embodied
- `应用:安全` — 安全应用

## 硬件（受控）

- `硬件:NPU` — NPU 加速
- `硬件:GPU` — GPU 加速
- `硬件:CPU` — CPU 推理
- `硬件:DSP` — DSP 加速
- `硬件:Jetson` — NVIDIA Jetson
- `硬件:手机` — 手机端
- `硬件:MCU` — 微控制器
- `硬件:DGX` — NVIDIA DGX
- `硬件:H100` — H100/H 系列
- `硬件:Snapdragon` — 高通 Snapdragon
- `硬件:Apple-Silicon` — Apple Silicon
- `硬件:Ascend` — 华为 Ascend

## 模型（半自由，starter 列表）

- `模型:Llama`
- `模型:Qwen`
- `模型:DeepSeek`
- `模型:BitNet`
- `模型:Phi`
- `模型:MiniCPM`
- `模型:Gemma`
- `模型:SmolLM`
- `模型:Mistral`
- `模型:GPT`

## 规则

- 至少 1 个、至多 8 个标签。
- 标签值用 `维度:值` 格式（维度必须是 方向/应用/硬件/模型 之一；值须命中对应维度的词表，模型维可提议新值）。
- 过滤掉纯 GUI agent（屏幕点击/GUI 自动化）后再打标签；GUI 自动化方向不收。
- 新标签：agent 在 `score_reason` 写「建议新增标签 `维度:值`，理由…」，主 agent 审核后加入 `data/tags.yaml`（再同步本表），不许 agent 私自用词表外的标签。
