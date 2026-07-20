# SGLang DSpark 实验与关键代码解读

## 结论

SGLang 已正式合并 DSpark。研究固定合并 PR `#30261` 的头提交 `dd694b43dac56355f9f9192eca47d9a899e03a93`。该实现不是简单移植 draft model，而是面向多请求在线服务增加动态 verify budget、ragged CUDA graph、overlap scheduler、成本模型与可观测性。

本机没有 NVIDIA/CUDA，完整 server 被上游参数校验明确拒绝；因此本阶段执行了真实的 CPU reference 代码和上游断言，共 56/56 通过，并实际触发 CUDA guard。没有伪造 GPU 吞吐数据。

## 固定版本与验证结果

- 源码：`D:\proj\dspark-blog\sglang`，分支 `codex/dspark-study`
- commit：`dd694b43dac56355f9f9192eca47d9a899e03a93`
- PR diff：84 files，约 17,700 additions
- 环境：WSL2、Python 3.10.12、torch 2.9.1+cpu、msgspec 0.21.1

| 上游测试 | 覆盖重点 | 结果 |
|---|---|---:|
| `test_dspark_sps_table.py` | SPS/加性成本表、JSON、查表边界 | 21/21 |
| `test_dspark_scheduler.py` | survival、预算 argmax、per-request verify length、ragged layout | 25/25 |
| `test_dspark_sts.py` | confidence head、STS 校准、数据 shard | 10/10 |

完整结果：`results/sglang-summary.json`。隔离引导器只占位未参与被测计算的完整服务类型，DSpark 模块、上游测试函数和断言保持原样。

设备边界探针直接执行 PR 的 `_handle_dspark()`：

```text
ValueError: DSpark speculative decoding only supports CUDA device.
```

## 关键调用链

### 1. 参数解析与 worker 选择

`server_args.py` 注册 `DSPARK`、block size、SPS table、STS path 等参数；`arg_groups/speculative_hook.py::_handle_dspark()` 验证 CUDA、pipeline parallel、draft checkpoint，并把 `gamma` 映射为 verify window `gamma + 1`；`spec_info.py`/`spec_registry.py` 最终选择 `DSparkWorkerV2`。

### 2. draft 模型

`models/dspark.py` 包含：

- `run_markov_block()`：上一 token 逐位置修正 base logits；
- `VanillaMarkov` / `GatedMarkovHead` / RNN 变体：半自回归轻量头；
- `DSparkConfidenceHead`：输出每位置置信度并应用 STS；
- `DSparkDraftMixin`：把 DFlash backbone、lm-head 与顺序头组合。

`dspark_draft.py::DraftBlockProposer.propose()` 负责准备 draft block、运行 draft forward、采样并返回 `DraftProposal`。

### 3. 每个 decode step 的主干

`dspark_worker_v2.py::DSparkWorkerV2._forward_decode()` 是最值得顺读的入口：

1. `alloc_verify_window()` 分配本轮验证窗口。
2. `_proposer.propose()` 产生 `gamma` 个 draft tokens 与 confidence。
3. `DSparkVerifyPlanner.resolve_verify_token_budget()` 根据历史/当前 confidence 和 SPS 成本表求总预算。
4. `schedule_layout()` 将总预算按 survival probability 分给每个 request，得到不同 verify length。
5. compact 模式执行 `TargetVerifyExecutor.run_compact()`；其他模式走 full/non-compact。
6. `accept_and_finalize()` 做 target 接受、bonus token 与 commit length。
7. `commit_hidden()` 更新 target hidden/KV 状态；observers 记录 acceptance ceiling、置信度和预算。

### 4. 动态预算的含义

`compute_sort_survival()` 对位置置信度做前缀乘积：第 i 位能被验证并接受，前 i 位必须都存活。`compute_verify_token_budget()` 遍历候选额外验证 token，最大化大意为：

```text
expected committed tokens × steps_per_second(total verify tokens)
```

`SpsCostTable` 或 `SpsAdditiveCostTable` 提供不同 batch/verify token 数的真实 step cost。低负载时多验证的边际代价小；高负载时 target verify 变贵，预算会收缩。

### 5. ragged verify 与 CUDA graph

`ragged_verify.py::RaggedVerifyLayout` 保存每请求 verify length、前缀和与 graph tier。compact 模式不是把所有请求 padding 到最大 block，而是把各请求的有效 token 前端打包，再按总 token 数向上取最近的 CUDA graph tier。这样裁掉的 token 确实不进入 attention/MLP，而不只是被 mask。

### 6. overlap 与可观测性

SGLang 把 confidence 通过 overlap scheduler 延迟传递，用前序 step 信息隐藏 CPU 调度开销；`DsparkVerifyEpilogue` 可把 compact scatter、accept、commit 融进 captured graph。`dspark_observability.py`、block accept estimator、STS recorder 则补齐“裁剪后看不到未验证尾部”的观测问题。

## 本机测试隔离方法

SGLang 顶层 `sglang/__init__.py` 会加载完整服务栈；Windows 直接导入先因 POSIX `resource` 缺失失败，WSL 最小环境也无需安装全部 CUDA wheel。`scripts/run_sglang_cpu_test.py` 建立 namespace package，并只为 planner 的服务期类型注入 import contract，随后运行上游测试文件本身。CPU Torch reference kernels、成本表、STS 与 planner 算法仍是 PR 原码。

## NVIDIA 机器上的下一步命令

官方复现使用 CUDA 容器/源码、DeepSeek-V4 DSpark checkpoint，并以 `--speculative-algorithm DSPARK` 启动。真正评估动态 scheduler 时至少要对照：

```bash
SGLANG_RAGGED_VERIFY_MODE=static  python3 -m sglang.launch_server ... --speculative-algorithm DSPARK
SGLANG_RAGGED_VERIFY_MODE=compact python3 -m sglang.launch_server ... --speculative-algorithm DSPARK --speculative-dspark-sps-table-path sps_table.json
```

必须在同 GPU、同模型、同请求集、同并发下比较 static/compact/non-spec；本机 Intel Arc 不能替代这一步。
