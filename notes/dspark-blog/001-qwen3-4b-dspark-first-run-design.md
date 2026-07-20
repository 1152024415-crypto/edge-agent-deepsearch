# DeepSpec Qwen3-4B DSpark 首次运行实验设计

## 1. 目标

在当前 Windows 11、Core Ultra 5 125H、32 GB 内存、Intel Arc 核显、无 NVIDIA CUDA 的机器上，使用 DeepSpec 官方代码、`Qwen/Qwen3-4B` 目标模型和 `deepseek-ai/dspark_qwen3_4b_block7` 草稿模型，完成一次真实 DSpark 生成。

本实验的重点是确认官方推理链路能够在本机实际执行，并沿真实请求解读关键代码；不审计 DeepSeek 官方实现的算法正确性，也不尝试复现论文中的 GPU 加速比。

## 2. 成功条件

实验满足以下条件即视为跑通：

1. 固定并记录 DeepSpec 上游 commit、Python、PyTorch、Transformers 与关键依赖版本。
2. 成功加载 Qwen3-4B 目标模型和对应的 DSpark block-7 checkpoint。
3. 使用一条短 prompt 完成一次端到端生成并保存输出。
4. 从运行日志或 evaluator 返回值中记录可获得的草稿长度、接受长度或接受率；若官方接口没有暴露某项指标，明确记录该接口限制，不自行伪造数据。
5. 记录总耗时、进程峰值内存以及实际使用的计算设备。
6. 根据本次执行路径，写出从入口、模型加载、草稿生成、Markov head、目标验证到结果提交的关键代码解读。

## 3. 范围

### 包含

- 官方 DeepSpec 仓库与官方发布 checkpoint。
- 一个专用于首次运行的最小脚本。
- 环境探测、依赖安装、模型下载和运行日志。
- 遇到错误后的诊断、调整与再次运行记录。
- 最终实验记录和关键代码调用链解读。

### 不包含

- 训练或微调 DSpark drafter。
- 人工对拍 attention mask、loss 或模型数值。
- 完整 benchmark 数据集评测。
- llama.cpp、SGLang 实验。
- 对论文吞吐、延迟或 60%–85% 生产加速结论的复现。

## 4. 实验组织

在 DeepSpec 仓库内新增以下内容：

```text
specs/
  001-qwen3-4b-dspark-first-run-design.md
  001-qwen3-4b-dspark-first-run-record.md
experiments/
  first_run_qwen3_4b.py
scripts/local/
  inspect_environment.ps1
results/first-run-qwen3-4b/
  environment.json
  run.json
  run.log
```

- `design.md` 固定实验目标、边界和成功条件。
- `record.md` 按时间顺序记录实际命令、错误、修复、结果和代码解读。
- `first_run_qwen3_4b.py` 只负责调用 DeepSpec 官方 evaluator 完成一条请求，并将结构化指标写到标准输出。
- `inspect_environment.ps1` 采集不会泄露凭据的硬件和软件信息。
- `results/` 保存机器可读结果；模型权重和 Hugging Face 缓存不纳入 Git。

## 5. 执行路径

### 阶段 A：环境与源码基线

1. 记录 DeepSpec commit `005e03b81cec38b7da6399833d609ee89a2587f2`。
2. 检查可用 Python 解释器、磁盘空间、内存和 PyTorch device。
3. 创建独立虚拟环境，避免污染系统 Python。
4. 安装 DeepSpec 的官方依赖并保存最终版本清单。

### 阶段 B：最小真实生成

1. 复用 `config/dspark/dspark_qwen3_4b.py` 的模型参数。
2. 加载 `Qwen/Qwen3-4B` 与 `deepseek-ai/dspark_qwen3_4b_block7`。
3. 使用短 prompt：`Explain speculative decoding in one short paragraph.`
4. 将最大新 token 数限制在 32，初始上下文保持最小，以降低本机 CPU/共享内存压力。
5. 执行一次生成，保存输出、耗时、内存和 evaluator 暴露的接受统计。

### 阶段 C：失败降级策略

真实运行优先保持官方模型和官方 evaluator 不变，只按以下顺序降低资源需求：

1. 使用 CPU，并明确禁用需要 CUDA 的可选优化。
2. 减少最大生成 token 数和上下文长度。
3. 使用官方代码支持的低内存加载选项。
4. 如果 Windows 原生环境被依赖明确阻断，则改用机器上现有的 WSL2 Ubuntu 22.04，仍复用同一实验 spec 和结果格式。

不使用未经官方支持的 checkpoint 量化来换取跑通，因为量化会引入另一套实现变量，偏离首次实验目标。

## 6. 关键代码解读范围

代码解读围绕实际执行调用链展开，重点覆盖：

1. `config/dspark/dspark_qwen3_4b.py`：目标模型、drafter 和 block 参数如何组合。
2. `eval.py` 及 evaluator 注册逻辑：配置如何构造具体 DSpark evaluator。
3. `deepspec/modeling/dspark/qwen3/modeling.py`：目标隐藏状态如何进入 DSpark drafter。
4. `deepspec/modeling/dspark/markov_head.py`：上一草稿 token 如何形成 Markov 修正。
5. evaluator 的生成与验证循环：草稿 block 如何产生、目标模型如何验证、接受统计如何累计。

只解读本次运行确实经过的代码；训练 loss 等未执行路径只标注位置，不展开验证。

## 7. 实验记录格式

`001-qwen3-4b-dspark-first-run-record.md` 依次包含：

1. 实验摘要与最终状态。
2. 环境和源码版本。
3. 模型与 checkpoint 信息。
4. 每次执行的时间、完整命令和结果。
5. 每个错误的原始信息、原因判断、采取的最小修复。
6. 成功运行的 prompt、生成文本和结构化指标。
7. 关键代码调用链解读。
8. 本机限制、尚未观察到的指标和下一阶段建议。

所有失败尝试都会保留摘要，但不把包含本机用户名、访问令牌或 Hugging Face 凭据的内容写入记录。

## 8. 验收方式

完成后同时检查：

- `run.log` 中存在一次完整生成，没有未处理异常。
- `run.json` 中存在模型标识、设备、prompt、输出、耗时和内存字段。
- record spec 中的命令与实际执行历史一致。
- 代码解读中的文件和符号均能在固定的 DeepSpec commit 中定位。
- 无法获得的指标被明确标记为“当前官方接口未暴露”，而不是留空或估算。
