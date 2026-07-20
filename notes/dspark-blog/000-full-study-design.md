# DSpark 三实现完整调研设计

## 目标

在同一台本机上，以可复现证据学习并对照 DeepSpec、llama.cpp 和 SGLang 的 DSpark 实现。每一阶段都必须留下：固定源码版本、实际执行命令、原始结果、关键调用链和硬件边界。

## 当前环境

- Windows 11，WSL2 Ubuntu 22.04
- 25 GiB 可用内存、32 GiB swap、D 盘约 431 GiB 可用
- Intel Arc Graphics；没有 NVIDIA GPU/CUDA
- Windows 已有 Git 与 uv；CMake/GCC/Ninja 位于 WSL

## 上游版本基线（2026-07-17）

- DeepSpec：第一阶段已在独立仓库完成，Qwen3-4B + DSpark block-7 已在 CPU 真实生成 32 tokens。
- llama.cpp：研究 PR `ggml-org/llama.cpp#25173`，PR 尚未合并，固定头提交 `27cc3bae61b1d00db07e8fa0f02b23c5fee30ab9`。
- SGLang：研究已合并 PR `sgl-project/sglang#30261`，固定 PR 头提交 `dd694b43dac56355f9f9192eca47d9a899e03a93`，并对照当前合并后的主线。

## 实验策略

### 1. llama.cpp

用 WSL CPU 编译 PR 头，先运行上游相关测试，再复用本机已经下载的 Qwen3-4B/DSpark 权重完成格式转换与最小生成。若权重转换或 PR 本身存在明确缺口，保留失败命令和最小复现，并继续完成源码调用链验证。

重点解读：命令行参数进入点、DSpark drafter 的装载、候选块生成、置信度裁剪、target verification、accept/reject 与 KV cache 更新。

### 2. SGLang

固定已合并实现，执行不依赖 CUDA 的导入、配置、静态/单元测试；同时实际触发并记录 CUDA 能力边界。由于本机没有 NVIDIA GPU，不伪造吞吐实验。

重点解读：server arguments、draft worker、每请求动态 verify 长度、ragged CUDA graph、overlap scheduler、在线 cost model 与 metrics。

### 3. 三方对照

按“算法语义—运行时映射—调度与工程优化—硬件要求—适合学习的入口”比较三者，并给出本机最快复现路径和后续迁移到 NVIDIA 机器的命令。

## 验收标准

1. 每个上游仓库记录精确 commit 和 dirty 状态。
2. 每项成功/失败结论都有实际命令及输出文件。
3. 关键代码解读引用具体文件、符号和调用顺序。
4. 总结明确区分“本机实跑”“源码验证”“官方数据”，不把三者混写。
5. 所有自建文档与辅助脚本提交到 `research` 仓库。
