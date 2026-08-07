# 开源大项目白名单

> github MCP 采集只盯本表项目 + 本周爆火新 agent 仓。非白名单小/个人仓一律不收。
> 采集规则：
> - **现有仓只提取「重大更新」**：版本号大版本发布（v1.27.0 / v0.24.0 这种）或重要 feature release。**每日 CI build（如 llama.cpp 的 b9823）、patch/小修、常规 commit 不算**，不提取。
> - **本周爆火 agent 仓**：created 在过去 7 天内 + agent 相关 + star 短时暴涨（爆火，主 agent 判断）。
> - release notes 必须从官方 release 页取，不许用二手解读。
> - github MCP 配置见 `docs/references/mcp-setup.md`（项目级 `.mcp.json`，需 `GITHUB_PERSONAL_ACCESS_TOKEN`）。

## 端侧/边缘推理引擎（13）
- llama.cpp — `github.com/ggml-org/llama.cpp`（GGUF 标准，CPU/Metal/CUDA/Vulkan）
- ExecuTorch (Meta) — `github.com/pytorch/executorch`（PyTorch 边缘部署）
- MLC-LLM — `github.com/mlc-ai/mlc-llm`（TVM 编译，跨平台含 WebGPU）
- ONNX Runtime (Microsoft) — `github.com/microsoft/onnxruntime`（工业标准，EP 最广）
- MNN (Alibaba) — `github.com/alibaba/MNN`（移动/嵌入式轻量）
- NCNN (Tencent) — `github.com/Tencent/ncnn`（移动端）
- MediaPipe (Google) — `github.com/google-ai-edge/mediapipe`（Gemma/Llama on Android/iOS）
- LiteRT (Google, ex-TF Lite) — `github.com/google-ai-edge/litert`（移动推理）
- Core ML Tools (Apple) — `github.com/apple/coremltools`（iOS 部署）
- MLX (Apple) — `github.com/ml-explore/mlx`（Apple Silicon）
- OpenVINO (Intel) — `github.com/openvinotoolkit/openvino`（边缘推理）
- PowerInfer (SJTU) — `github.com/PowerInfer/PowerInfer`（CPU+GPU 混合端侧大模型）
- RKLLM (Rockchip) — Rockchip NPU 端侧（仓址以官方为准）

## Agent 应用
- nanobot (HKUDS) — `github.com/HKUDS/nanobot`（轻量开源 AI agent，工具/聊天/工作流；港大 HKUDS 实验室）
- Orchard (Microsoft Research) — `github.com/microsoft/Orchard`（Agent 训练与 Kubernetes 环境基础设施；属于相邻 Agent 平台，不是端侧 Agent）

## 维护规则
- 增删在本文档进行，不靠记忆。新项目要"业界认可大项目"（知名实验室/公司/高 star+影响力），个人小仓不收。
- 一个仓只在「最近 7 天有重大 release」时才进本周 run。
