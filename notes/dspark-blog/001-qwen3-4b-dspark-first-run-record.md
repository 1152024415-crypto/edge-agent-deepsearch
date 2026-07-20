# DeepSpec Qwen3-4B DSpark 首次运行记录

## 1. 实验结论

实验成功。2026-07-17 在 Windows 11、Intel Core Ultra 5 125H、32 GB 内存、无 CUDA 的机器上，使用 DeepSpec 上游提交 `005e03b81cec38b7da6399833d609ee89a2587f2`、官方 `Qwen/Qwen3-4B` 目标模型和 `deepseek-ai/dspark_qwen3_4b_block7` checkpoint，完成了 8-token 预检和 32-token 正式 DSpark 生成。

设计 spec 的六项成功条件全部满足：

1. 已固定 DeepSpec、Python、PyTorch、Transformers 和完整依赖版本。
2. 已加载 Qwen3-4B 与 block-7 DSpark checkpoint，并校验全部权重 SHA-256。
3. 已完成端到端生成，输出保存在 `results/first-run-qwen3-4b/run.json`。
4. 已记录每轮 proposal length、accepted draft length、acceptance length 和平均值。
5. 已记录模型执行总耗时、加载耗时、生成耗时、峰值 RSS 和实际 CPU device。
6. 已根据真实执行路径解读入口、模型加载、draft block、Markov head、目标验证和状态更新。

本实验只证明该官方推理链路能够在本机 CPU 上真实执行，不代表论文或生产 GPU 环境中的加速比。

## 2. 固定版本与环境

| 项目 | 实际值 |
| --- | --- |
| DeepSpec 上游基线 | `005e03b81cec38b7da6399833d609ee89a2587f2` |
| 实验运行时 Git commit | `aa8f716843157aa2e4366fb8b4aec51fb2e621a2` |
| 分支 | `codex/deepspec-validation` |
| 操作系统 | Windows 11 家庭版中文版，`10.0.26200`，64 位 |
| CPU | Intel Core Ultra 5 125H，14 核、18 逻辑处理器 |
| 物理内存 | 33,779,150,848 字节，约 31.46 GiB |
| GPU | Intel Arc 核显；本次未使用 |
| 环境管理 | `uv 0.11.21` |
| Python | 3.11.15 |
| PyTorch | `2.9.1+cpu` |
| Transformers | 5.10.2 |
| NumPy | 2.4.4 |
| Triton | 未安装；本次推理调用链不依赖 Triton |
| CUDA | `torch.cuda.is_available() == False` |
| 实际 device | `cpu` |

环境快照见 `results/first-run-qwen3-4b/environment.json`，完整包版本见 `results/first-run-qwen3-4b/pip-freeze.txt`。

最初检查过 WSL2 Ubuntu 22.04，但正式实验改用 Windows 原生环境。原因不是 DeepSpec 算法限制，而是 WSL 向 `/mnt/d` 安装 PyTorch 的大量小文件时 I/O 过慢；Windows 原生 `uv` 在约 62 秒内完成了环境安装。

## 3. 模型与运行参数

| 参数 | 实际值 |
| --- | --- |
| target 仓库 | `Qwen/Qwen3-4B` |
| target 本地路径 | `.cache/models/Qwen3-4B` |
| draft 仓库 | `deepseek-ai/dspark_qwen3_4b_block7` |
| draft 本地路径 | `.cache/models/dspark_qwen3_4b_block7` |
| prompt | `Explain speculative decoding in one short paragraph.` |
| `max_new_tokens` | 32；预检为 8 |
| `temperature` | 0.0 |
| `confidence_threshold` | 0.0 |
| seed | 980406 |
| batch size | 1 |
| draft block size | 7 |
| draft decoder layers | 5 |
| target hidden layers | `[1, 9, 17, 25, 33]` |
| Markov head | vanilla，rank 256 |

模型缓存未提交 Git。下载完成后，四个权重文件均通过 SHA-256 校验：

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| target shard 1 | 3,957,900,840 | `328a91d3122359d5547f9d79521205bc0a46e1f79a792dfe650e99fc2d651223` |
| target shard 2 | 3,987,450,520 | `6cd087b316306a68c562436b5492edbcf6e16c6dba3a1308279caa5a58e21ca5` |
| target shard 3 | 99,630,640 | `e4bf436957184f4eeb86a80e9db394503f1f56446b2e6b7edeac5b81470f4ca1` |
| draft checkpoint | 2,786,273,970 | `f9e31587608441f235d46410e7201f8cb1647be5cd077065c89cc02c37ae86a7` |

## 4. 执行时间线

本节时间均为 Asia/Shanghai（UTC+08:00）。模型运行时间来自 JSON；下载时间来自进程、文件和 Xet 日志；早期未落盘的 WSL 尝试只能恢复到分钟，明确标为“约”。这里只列会改变环境、下载状态或实验结果的实际命令；`Get-Process`、`Get-Item`、`rg` 等只读诊断在对应原因判断中说明。

### 4.1 环境探测与 WSL 尝试（约 16:27–16:57）

环境脚本最初运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\local\inspect_environment.ps1
```

第一次退出码为 1：WSL 的 NAT/localhost 警告写入 stderr，被 `$ErrorActionPreference = 'Stop'` 当作终止错误。检查确认 `wsl.exe` 实际退出码为 0 后，只在探针附近放宽 PowerShell 错误流处理；最终快照在 `16:57:54.707` 生成，退出码为 0。

约 `16:28`，下面的原始安装命令被双层 shell 转义破坏：

```powershell
wsl -d Ubuntu-22.04 -- bash -lc `
  'cd /mnt/d/proj/dspark-blog/deepspec && python3 -m venv .venv && .venv/bin/python -m pip install --upgrade pip setuptools wheel && .venv/bin/python -m pip install -r requirements.txt "psutil>=5.9,<8" "pytest>=8,<10"'
```

退出码为 1，原始摘要为 `/bin/bash: line 1: 8 pytest: No such file or directory`。`<` 被解释成重定向，并留下一个 0 字节命令残留；残留已删除。

约 `16:29`，去掉范围约束后的第一次重试使用了下面的完整命令：

```powershell
wsl -d Ubuntu-22.04 -- bash -lc `
  'cd /mnt/d/proj/dspark-blog/deepspec && python3 -m venv .venv && .venv/bin/python -m pip install --upgrade pip setuptools wheel && .venv/bin/python -m pip install -r requirements.txt psutil pytest'
```

外层错误地设置了短 timeout，5.046 秒后退出码为 124，并在 pip 自升级时终止。约 `16:29` 紧接着以长 timeout 原样重跑上面同一条完整命令；2.4 秒后退出码为 1，原始根因是 `ModuleNotFoundError: No module named 'pip._vendor.requests'`。两个时间只能从执行顺序恢复到分钟，因此没有写成虚假的秒级时间。虚拟环境随后用以下命令原地重建：

```powershell
wsl -d Ubuntu-22.04 -- bash -lc `
  'cd /mnt/d/proj/dspark-blog/deepspec && python3 -m venv --clear .venv && .venv/bin/python -m pip install -r requirements.txt psutil pytest'
```

这次依赖解析在约 231 秒后退出 1：Python 3.10 可见的 NumPy 最高为 2.2.6，无法满足上游固定的 `numpy==2.4.4`。之后用 WSL `uv` dry-run 验证过兼容覆盖，但实际安装在 `/mnt/d` 写入 PyTorch 大量小文件时非常慢，因此没有继续使用该运行环境。

约 `16:55` 改用 Windows 原生环境：

```powershell
uv venv --clear --python 3.11 .venv-win
uv pip install --python .venv-win\Scripts\python.exe `
  -r experiments\requirements-windows.txt
```

两个命令退出码均为 0；实际安装耗时约 62 秒。Windows 依赖清单仅从上游清单移除了无 Windows wheel、且本次推理核心未导入的 Triton，并加入 psutil 与 pytest。随后 `Qwen3DSparkEvaluator` 导入成功。环境基线于 `16:58:23` 提交。

### 4.2 runner 的红绿测试（17:00–17:07；18:01 修订）

参数和指标测试先观察到 3 个预期 `NotImplementedError`，随后最小实现转绿。CLI 测试先因 `parse_args` 不存在而收集失败，再由完整 runner 转绿：

```powershell
.venv-win\Scripts\python.exe -m pytest `
  tests\experiments\test_first_run_qwen3_4b.py -v
```

初版在 `17:06:58` 以 4 项通过提交。审查指出总耗时和 CPU shim 测试缺口后，先增加失败测试，再加入 `total_seconds`；最终同一命令为 6 项通过，修订于 `18:01:12` 提交。

runner 使用 `Qwen3DSparkEvaluator.__new__` 跳过整个 evaluator 构造函数，手工恢复单进程推理必需字段并显式禁用 confidence diagnostic recorder；模型构建、proposal、Markov、verify 和 update 核心路径仍调用上游实现。

### 4.3 模型下载故障与恢复（17:11–17:46）

`17:11:22` 首次直接执行预检：

```powershell
$env:HF_HOME = (Join-Path (Get-Location) '.cache\huggingface')
$env:HF_XET_HIGH_PERFORMANCE = '1'
.venv-win\Scripts\python.exe -m experiments.first_run_qwen3_4b `
  --max-new-tokens 8 --device cpu `
  --output results\first-run-qwen3-4b\run.tmp
```

Xet 通过本机代理建立多路连接，但约 211 秒后仍为 `Fetching 3 files: 0%`；进程被诊断性终止，退出状态为 `-1`，不是模型代码异常。

`17:15:06` 使用相同 runner 重试，但设置 `$env:HF_HUB_DISABLE_XET='1'` 并移除 `HF_XET_HIGH_PERFORMANCE`。普通 HTTPS 完成了 95 MiB 小分片，并留下约 2.08 GiB 的两个大分片断点；大文件并发流再次停止增长，约 309 秒后被终止，退出状态 `-1`。

`17:20:32` 再运行：

```powershell
$env:HF_HUB_DISABLE_XET='1'
.venv-win\Scripts\hf.exe download Qwen/Qwen3-4B `
  --cache-dir .cache\huggingface\hub --max-workers 1 --format human
```

新大分片仍停在 0 字节，约 `17:24` 被终止，退出状态 `-1`。原因判断是官方大文件长连接经当前本机代理不稳定，而非仓库权限或模型格式错误。

`17:25–17:46` 保持官方 URL 和 checkpoint 不变，改用稳定文件名与 Range 续传：

```powershell
curl.exe -L --fail --retry 50 --retry-delay 2 --retry-all-errors `
  --speed-time 60 --speed-limit 1024 -C - `
  -o .cache\models\Qwen3-4B\model-00001-of-00003.safetensors `
  https://huggingface.co/Qwen/Qwen3-4B/resolve/main/model-00001-of-00003.safetensors
```

同一完整命令只替换 `-o` 与 URL，依次用于 target shard 2 和 draft `model.safetensors`；target shard 3 已从成功缓存复制。三次 curl 退出码均为 0。tokenizer/config 小文件使用 `curl.exe -L --fail --retry 20 --retry-all-errors -o <本地文件> <官方 URL>`，均退出 0。四个权重最终按服务端长度和 SHA-256 验收通过。

### 4.4 8-token 预检（17:47:28.050）

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.venv-win\Scripts\python.exe -m experiments.first_run_qwen3_4b `
  --target-model .cache\models\Qwen3-4B `
  --draft-model .cache\models\dspark_qwen3_4b_block7 `
  --max-new-tokens 8 --device cpu `
  --output results\first-run-qwen3-4b\run.tmp
```

退出码为 0。加载耗时 0.996255400008522 秒，生成耗时 7.847558600013144 秒，峰值 RSS 10,445,393,920 字节，生成 8 token。完整尝试记录见 `preflight.log`。

### 4.5 正式 32-token 运行（18:01:26.318）

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.venv-win\Scripts\python.exe -m experiments.first_run_qwen3_4b `
  --target-model .cache\models\Qwen3-4B `
  --draft-model .cache\models\dspark_qwen3_4b_block7 `
  --max-new-tokens 32 --device cpu `
  --output results\first-run-qwen3-4b\run.json
```

退出码为 0，`run.json` 的结构化验收全部通过。模型执行总耗时口径从进入模型加载前开始，到输入编码、生成、解码和峰值监控结束为止；不包含 JSON 序列化与写盘。`run.log` 开头的 PowerShell `NativeCommandError` 是 `Tee-Object` 将 Transformers 的 stderr 进度条包装成错误记录；它后面紧跟两组 100% 权重加载进度与完整的 `status: success` JSON，不是未处理的 Python 异常。

## 5. 最终输出与指标

生成文本原样如下：

> Speculative decoding is a technique used in natural language processing where a model generates text by making educated guesses about the next word based on partial or incomplete information, allowing

| 指标 | 实际值 |
| --- | ---: |
| 输入 token | 21 |
| 输出 token | 32 |
| 模型执行总耗时 | 23.434874900005525 秒 |
| 模型加载耗时 | 0.7681678999797441 秒 |
| 生成耗时 | 22.648897900013253 秒 |
| 观察到的生成速率 | 1.413 token/s |
| 峰值 RSS | 10,449,645,568 字节（raw: `10449645568`），约 9.732 GiB |
| verify count | 13 |
| average proposal length | 7.0 |
| average accepted draft length | 1.4615384615384615 |
| average acceptance length | 2.4615384615384617 |

每轮原始数组：

```text
proposal_lengths:
[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7]

accepted_draft_lengths:
[3, 1, 1, 2, 0, 2, 0, 0, 0, 4, 2, 0, 4]

acceptance_lengths:
[4, 2, 2, 3, 1, 3, 1, 1, 1, 5, 3, 1, 5]
```

`acceptance_lengths` 的和在本次恰好为 32，与输出 token 数数值相同，但这不是逐 token 的严格守恒关系。target prefill 先产生一个初始输出 token，它不在该数组中；最后一轮循环记录了 `accepted_draft_tokens + 1`，但长度上限会截掉末尾多出的 target next token。本次二者刚好抵消。accepted draft length 始终只计算被接受的 draft token。

## 6. 关键代码调用链

### 6.1 `experiments/first_run_qwen3_4b.py::build_local_evaluator`

输入是 runner 参数对象与 `torch.device('cpu')`。该函数使用 `Qwen3DSparkEvaluator.__new__` 创建对象，因此跳过整个 `Qwen3DSparkEvaluator.__init__`：既跳过 `BaseEvaluator.__init__` 内的 CUDA/NCCL 初始化，也跳过 `_build_confidence_head_recorder()`。runner 手工设置单进程字段、调用官方 `build_models()`，并把 diagnostic recorder 显式设为 `None`。输出 evaluator 的模型、tokenizer、proposal、Markov、verify 和 update 方法仍来自上游实现；本实验没有声称复用了官方置信度诊断记录路径。

### 6.2 `deepspec/eval/dspark/evaluator.py::Qwen3DSparkEvaluator.build_models`

输入是 target/draft 路径和 evaluator device。它以 bfloat16、SDPA 加载 Qwen3-4B 与 `Qwen3DSparkModel`，检查 draft 引用的 target layer 不包含最终层，并加载 target tokenizer。输出是 `(target_model, draft_model, tokenizer)`。

本 checkpoint 的 target 层为 `[1, 9, 17, 25, 33]`，draft 有 5 层、block size 7。两个模型均在 CPU 上运行。

### 6.3 `deepspec/eval/base_evaluator.py::generate_decoding_sample`

输入是 target model、prompt `input_ids`、最大输出长度、温度、停止 token，以及 DSpark 的 init/propose/update 回调。它先对 21-token prompt 做 target prefill，建立 target `DynamicCache`，并采样第一个输出 token。

`_init_context` 从 target 的指定中间层提取 hidden states，并建立独立的 draft KV cache。随后循环执行 propose、verify、commit 和 update，最后返回 `output_ids` 与三组逐轮统计。

### 6.4 `Qwen3DSparkEvaluator._propose`

输入包含当前已提交 `output_ids`、position ids、decode 起点、draft cache 和 target hidden states。它创建长度 7 的 draft block：第一个位置放当前已提交 token，其余位置使用 `mask_token_id`，然后调用 `forward_dspark_draft_block`。

输出是 `DSparkDraftProposal`，包含目标模型需要验证的 `[当前 token, draft token 1..N]`、每个 draft token 的概率分布和可选 confidence logits。

### 6.5 `deepspec/eval/dspark/draft_ops.py::forward_dspark_draft_block`

输入是 mask/noise token embeddings、来自 target 指定层的 hidden states、位置编码和 draft KV cache。`Qwen3DSparkModel._forward_backbone` 先把 5 个 target 层的特征拼接映射回 hidden size，再让 5 层轻量 drafter 在非因果 block 结构中一次产生 7 个位置的 hidden states。

输出 `block_hidden` 的前 7 个位置交给 proposal builder。draft cache 随后 crop 到当前已提交位置，避免未接受草稿污染下一轮状态。

### 6.6 `deepspec/eval/dspark/draft_ops.py::build_dspark_proposal`

输入是 7 个 proposal hidden states。`compute_logits` 先通过 draft `lm_head` 得到并行 base logits；`sample_draft_tokens` 再调用本 checkpoint 的 Markov head，输出 7 个 sampled tokens 和 Markov 修正后的 logits。

checkpoint 启用了 confidence head，但本次 `confidence_threshold=0.0`，因此 `_confident_prefix_length` 总是保留完整 block，13 轮的 proposal length 全为 7。confidence logits 仍可被计算，但 runner 没有启用 recorder，也没有把它们写入结果。

### 6.7 `deepspec/modeling/dspark/markov_head.py::VanillaMarkov.sample_block_tokens`

本次配置明确选择 `vanilla`、rank 256。对于 block 中第 `k` 个位置，Markov head 读取前一个 token id，经 `markov_w1` 映射到 256 维低秩向量，再由 `markov_w2` 投影成词表 bias，加到该位置的并行 base logits 上。

它只在这个低成本 head 内按 7 个位置顺序采样，并把刚采到的 token 作为下一位置的条件；5 层 drafter backbone 的 block hidden 已经并行产生。这正是本次代码中“半自回归”的关键：昂贵 backbone 做 block 级并行，轻量 Markov 修正恢复相邻 draft token 依赖。

输出是 `sampled_tokens [1, 7]` 与 `corrected_logits [1, 7, vocab]`，后者转换为 draft probabilities，供目标验证的接受率计算使用。

### 6.8 `deepspec/eval/base_evaluator.py::verify_draft_tokens`

输入是 `[当前 token + draft prefix]`、draft probabilities 和 target KV cache。target model 一次 forward 给出整个候选块的 target probabilities。对每个 draft token，代码计算 `min(1, p_target / p_draft)`，随机形成接受 mask，再用累积乘积保证只接受连续前缀。

如果首个拒绝发生在 draft block 内，就从 target 与 draft 的 residual distribution 采样下一个 token；如果全部 draft token 接受，则从 target 最后位置采样一个新 token。输出 `VerificationResult`，其中包含接受的 draft 数、target 输出、提交 token 和停止状态。

### 6.9 `Qwen3DSparkEvaluator._update`

输入是本轮 target verification output。它再次提取 `[1, 9, 17, 25, 33]` 层 hidden states，只保留 `accepted_draft_tokens + 1` 个已提交位置，作为下一轮 drafter 的 target context。

`generate_decoding_sample` 同时裁剪 target KV cache、推进 `start`，并累计 proposal、accepted draft 和 acceptance length。未接受的 draft token 不进入下一轮任何已提交状态。

## 7. 本机限制与观察边界

- CPU 的 1.413 token/s 不能代表 CUDA、SGLang 或生产服务性能，也不能证明 DSpark 相对普通 decoding 有加速；本实验没有运行 target-only 基线。
- Intel Arc 核显未被 PyTorch 使用；实际 device 是 CPU。
- 本实验没有验证训练、loss、confidence calibration、STS、请求调度、负载感知 block 调整或多请求 batching。
- `run.json` 暴露了 proposal length、accepted draft length、acceptance length 和 verify count，但没有暴露每 token 的 `p/q`、acceptance probability、随机 mask、confidence logits 或 residual sample。
- runner 没有分别计时 draft backbone、Markov head 和 target verify，也没有分别统计 target/draft 模型内存。
- `confidence_threshold=0.0` 固定使用完整 7-token proposal，本实验没有比较 confidence pruning 阈值。
- 单条 32-token prompt 的接受统计样本太小，不能外推为数据集接受率。

## 8. 下一阶段

下一阶段只建议做一件事：以本记录的九节点调用链和三组接受统计为语义基线，对照 llama.cpp 的 DSpark PR，先逐项映射它的 block hidden、Vanilla Markov 修正、proposal probability 与 target verification 实现，再决定最小 GGUF/CPU 运行实验；本阶段不执行 llama.cpp。
