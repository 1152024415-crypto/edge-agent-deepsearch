# DeepSpec、llama.cpp、SGLang 的 DSpark 实现对照

## 最终结论

三者不是重复实现，而是三层不同抽象：

| 实现 | 最适合学什么 | 本机状态 |
|---|---|---|
| DeepSpec | 论文算法与 tensor 语义 | CPU 真实生成已完成 |
| llama.cpp PR | 算法如何落成单机 GGML graph/低依赖推理 | CPU 真实 server 已完成 |
| SGLang | 算法如何进入多请求、高并发 CUDA serving | 56 个 CPU 断言完成；完整 server 因无 CUDA不可运行 |

## 推荐学习顺序（基础和论文已掌握之后）

1. **DeepSpec runner**：先把 `draft block → target verify → accept length` 的张量形状和统计对上。
2. **llama.cpp `dflash.cpp`**：看一次 block forward 如何通过 Markov W1/W2 在图内恢复顺序依赖。
3. **llama.cpp `common/speculative.cpp`**：看 confidence 截断与通用 accept/reject 如何接起来。
4. **SGLang `models/dspark.py` + `dspark_draft.py`**：对照 Python 版 Markov/confidence head 与 block proposer。
5. **SGLang `dspark_worker_v2.py::_forward_decode()`**：建立生产调用链全景。
6. **SGLang `dspark_planner.py` + `dspark_sps.py`**：理解为什么每个 request 的 verify 长度不同。
7. **SGLang `ragged_verify.py`、CUDA graph runner、overlap utils**：最后学习性能工程，不要一开始陷进 kernel 细节。

## 算法映射

```text
DeepSpec reference
  block drafter + Markov/confidence heads
            |
            +--> llama.cpp: GGUF tensors + one GGML graph + local threshold truncation
            |
            +--> SGLang: PyTorch/Triton drafter + per-request planner
                         + ragged CUDA graph + overlap + cost model + metrics
```

共同核心都是：DFlash 类 backbone 一次给出整块 base logits，轻量顺序头用前一 token 修正每一位置，target 并行验证并提交连续正确前缀。区别主要发生在“验证多少”和“怎么调度”：

- DeepSpec 参考代码重算法可读性。
- llama.cpp 当前 PR 用单一 `conf_min` 在每个块内遇低置信即截断，适合单机/本地服务。
- SGLang 把 confidence 转为 survival probability，并结合并发下实测 step cost，在全 batch 内分配总 verify budget；同一批请求可以有不同窗口。

## 本机实证对照

### DeepSpec

- Qwen3-4B + block-7，CPU，32 tokens。
- 22.65 秒 generation，约 1.41 tok/s。
- 13 次 verify，平均接受 draft 1.46，平均每轮前进 2.46 tokens。
- 峰值 RSS 约 9.73 GiB。

### llama.cpp

- 相同模型家族，Q8_0 target + draft，CPU，32 tokens。
- `conf_min=0`：7.21 tok/s，18/86 draft accepted。
- `conf_min=0.5`：9.30 tok/s，17/25 draft accepted；输出相同。
- 注意：量化、构建、采样实现均不同，不能把 7.21/1.41 直接解释成框架纯加速比。

### SGLang

- SPS 21、scheduler 25、STS 10，共 56/56 CPU tests。
- CPU device guard 实际拒绝完整 DSpark server。
- 官方 GPU 性能数字只作为外部参考，不混入本机结果。

## 针对这台硬件最快跑法

### 想看真实 token 输出

优先 llama.cpp PR + Q8_0：它已在本机达到 7–9 tok/s，模型总文件约 4.6 GiB。源码放 D 盘，构建放 WSL 原生文件系统，避免 `/mnt/d` 编译 I/O。

### 想改算法

优先 DeepSpec：Python/PyTorch 最容易插入 tensor dump、修改 confidence 规则和统计 acceptance，不必反复编 C++。

### 想学 SGLang 生产实现

本机运行 CPU planner/STS/SPS 测试，阅读 worker 调用链；完整吞吐实验必须换 NVIDIA CUDA 机器。Intel Arc 不是 SGLang DSpark 支持的 CUDA device。

## 已验证与未验证边界

已验证：

- DeepSpec PyTorch CPU generation。
- llama.cpp PR 编译、GGUF 转换、server DSpark generation、confidence 截断。
- SGLang 成本表、STS、CPU planner/reference schedule、ragged layout、CUDA 参数 guard。

未验证：

- llama.cpp PR 在 GPU backend 上的行为和长期稳定性。
- llama.cpp confidence threshold 在大数据集上的最优值。
- SGLang CUDA kernels、full CUDA graph、DP attention 与真实在线吞吐。
- 三框架在严格同精度、同采样、同请求集下的性能对比。

这些边界是硬件与实验设计限制，不是把未运行部分视作失败。
