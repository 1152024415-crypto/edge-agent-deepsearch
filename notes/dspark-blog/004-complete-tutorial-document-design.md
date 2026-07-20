# DSpark 完整教程与实验记录：文档设计

日期：2026-07-20

## 1. 目标读者

读者已经理解投机解码基础和 DSpark 论文，希望通过本机实验与真实开源实现，建立从算法步骤到工程代码的对应关系。

## 2. 文档目标

形成一篇能够独立阅读的中文 Markdown 长文，同时满足三个目的：

1. 用统一符号解释 DSpark 一轮解码怎样运行。
2. 完整记录 DeepSpec、llama.cpp、SGLang 三阶段实验的环境、命令、结果和故障。
3. 精读与 DSpark 直接相关的关键代码，说明作用、输入输出、核心逻辑和实现差异。

## 3. 组织方式

采用“教程主线 + 实验证据 + 源码映射”的双主线结构，而不是简单拼接已有 spec。

1. 阅读指南与结论速览。
2. DSpark 的统一执行模型。
3. 固定环境、模型、版本和证据等级。
4. DeepSpec：参考实现实验与核心 Python 调用链。
5. llama.cpp：GGUF/GGML 实验与关键 C++ 实现。
6. SGLang：生产调度实现与 CPU 可执行验证。
7. 三实现逐阶段对照。
8. 失败记录和根因分析。
9. 本机最快复现路径。
10. NVIDIA/CUDA 后续实验设计。
11. 推荐源码阅读顺序与索引。

文档使用两幅 Mermaid 图：一幅表示单轮 DSpark 数据流，一幅表示三套实现的抽象层次。结果表明确区分本机实跑、源码/CPU 单元验证和官方外部数据。

## 4. 源码讲解边界

只讲与 DSpark 直接相关的代码：

- block draft 的构造和提案；
- Markov/RNN 半自回归顺序头；
- confidence head、STS 与 survival probability；
- target verify、连续前缀接受和状态提交；
- llama.cpp 的 DSpark GGUF tensor、GGML graph 和 confidence threshold；
- SGLang 的 DSpark worker、动态 verify budget、ragged verify、overlap confidence relay；
- DSpark draft 与 target embedding/lm-head/hidden/KV 的连接。

通用 tokenizer、HTTP server、普通模型加载、基础 attention、通用 speculative decoding 框架和无关 CLI 不展开；只有当它们是理解 DSpark 数据流的必要边界时才简述。

预计精读 12–15 个关键符号。每个符号统一回答：

1. 它处于算法哪一步。
2. 输入和输出是什么。
3. 核心代码做了什么。
4. 为什么这样实现。
5. 容易误解或当前受限的地方。

## 5. 实验内容

### DeepSpec

记录 Qwen3-4B + block-7 在 CPU 上的 32-token 正式运行、acceptance 指标、峰值内存、模型下载与环境故障，以及从 evaluator 到 Markov head、verification、update 的调用链。

### llama.cpp

记录 PR 固定、WSL 原生构建、target/draft Q8_0 转换、错误入口 `llama-speculative` 的失败根因、正确 `llama-server` 路径，以及 `conf_min=0/0.5` 两次真实生成。

### SGLang

记录合并版本、CUDA guard、最小 uv/WSL 环境、56 个 CPU 测试，以及从 `DSparkWorkerV2._forward_decode()` 到 proposal、planner、ragged verify、accept/commit 的生产调用链。明确说明本机没有执行 CUDA kernel 和真实服务吞吐。

## 6. 验收标准

1. 所有实验数字与已有 JSON/spec/日志一致。
2. 命令能够从当前目录结构复现。
3. 不把单提示结果解释为通用 benchmark。
4. 不把官方 GPU 数据写成本机实验。
5. 每个关键代码结论引用具体文件和符号。
6. 无 `TODO`、`TBD` 或未解释的关键缩写。
7. 文档入口加入 `README.md`，并在研究仓库形成独立提交。
