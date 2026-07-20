# llama.cpp DSpark PR 实验与关键代码解读

## 结论

llama.cpp 中有 DSpark 实现，但截至 2026-07-17 仍位于未合并 PR `#25173`，不在稳定主线。固定 PR 头 `27cc3bae61b1d00db07e8fa0f02b23c5fee30ab9` 后，本机已完成 Qwen3-4B + `dspark_qwen3_4b_block7` 的 GGUF 转换、CPU 构建和两次真实生成。

## 固定版本与产物

- 源码：`D:\proj\dspark-blog\llama.cpp`，分支 `codex/dspark-study`
- 构建：WSL2 Ubuntu 22.04，GCC 11.4，`GGML_NATIVE=ON`、OpenMP、CPU-only
- target：Q8_0，4,280,405,280 bytes，SHA256 `5A03875A...278D00`
- draft：Q8_0，659,703,200 bytes，SHA256 `BC48A1C3...17EED3`
- 完整哈希与指标：`results/llamacpp-summary.json`

target 与 draft 都由 DeepSpec 阶段已经下载的 Hugging Face 权重转换，没有重复下载。draft 转换使用 `--target-model-dir`，从 target 继承 tokenizer 与 token embedding。

## 实跑结果

固定 prompt `Speculative decoding is`、greedy、seed 42、32 output tokens。两次输出完全相同：

> a technique used in neural machine translation (NMT) to improve the quality of the generated translations by considering the potential future words in the target sequence. This approach

| `conf_min` | 生成速度 | draft 生成/接受 | 接受率 | mean len |
|---:|---:|---:|---:|---:|
| 0.0 | 7.21 tok/s | 86 / 18 | 20.93% | 2.38 |
| 0.5 | 9.30 tok/s | 25 / 17 | 68.00% | 2.42 |

`conf_min=0.5` 的单次结果说明 confidence head 的截断路径确实工作：它在低置信位置提前停止块，少生成了大量无效 draft。单 prompt、短输出不足以证明 28.9% 的速度差可泛化，因此这里只把它记录为机制验证，不作为 benchmark 结论。

服务日志：

- `artifacts/llamacpp-dspark-server-conf0.log`
- `artifacts/llamacpp-dspark-server-conf05.log`
- `artifacts/llamacpp-response-conf0.json`
- `artifacts/llamacpp-response-conf05.json`

## 关键调用链

### 1. 参数与类型注册

`common/arg.cpp` 将 `--spec-draft-conf-min` 写入 `params.speculative.draft.conf_min`；`common/speculative.cpp` 把字符串 `draft-dspark` 映射到 `COMMON_SPECULATIVE_TYPE_DRAFT_DSPARK`。

### 2. 权重转换与加载

`conversion/qwen.py` 识别 DeepSpec checkpoint，并把 Markov W1/W2、confidence projection 转成 GGUF tensor；`src/llama-arch.*` 注册 tensor 名；`src/models/dflash.cpp` 在 DFlash 模型上发现 Markov tensor 后启用 DSpark 分支。

### 3. 一次 draft forward 内的半自回归 Markov 链

核心是 `src/models/dflash.cpp::build_dspark_markov_head()`：

1. DFlash backbone 一次产生整个 block 的 base logits。
2. 第 0 位用已提交的 anchor token 查 `markov_w1`，再由 `markov_w2` 投影为 vocab bias。
3. `corrected_logits = base_logits + markov_bias`。
4. 图内对 corrected logits 做 argmax，得到下一位置的 previous token，依次串起整个 block。
5. confidence head 对 `[draft hidden; markov embedding]` 做线性投影和 sigmoid，输出每个位置的预计接受概率。

因此它不是把小模型运行 7 次，而是一个 GGML graph 中完成一次 block forward 加轻量的顺序 Markov 修正。当前代码注释也明确：图内 conditioning 链固定为 greedy；外部 sampling 参数只影响最终 token pick，这是该 PR 当前语义上的限制。

### 4. 提案与置信度截断

`common/speculative.cpp::common_speculative_impl_draft_dflash` 同时承载 DFlash/DSpark：

1. 为每条 sequence 放入 anchor + mask block。
2. 一次 `llama_decode(ctx_dft, batch)` 生成整个块。
3. DSpark 从位置 0 开始读 proposal。
4. 若 confidence 小于 `conf_min`，在第一个低置信位置停止。
5. target 走 llama.cpp 通用 speculative verification 和 accept/reject 路径，日志最终给出 accepted/generated。

### 5. target/draft 上下文关联

`common_speculative_init_result` 先设置 `cparams.ctx_other = ctx_tgt`，draft 图由此共享 target 的 embedding/lm-head 语义。`llama-server` 通过此入口初始化，是真正支持 DSpark 的入口。

## 一次重要失败及根因

最初使用旧示例 `llama-speculative`，稳定报：

```text
dflash requires ctx_other to be set
Command terminated by signal 11
```

峰值 RSS 约 10.3 GiB，无 swap，所以不是内存不足。源码回溯显示旧示例分别调用两次 `common_init_from_params()`，没有设置 `ctx_other`；PR 文档给出的 `llama-server` 则调用新的 `common_speculative_init_from_params()`。切换到文档入口后同一权重正常运行。该记录提醒学习时不要把旧 speculative 示例当作 DSpark 驱动器。

## 可复现命令

```powershell
wsl -d Ubuntu-22.04 -- bash /mnt/d/proj/dspark-blog/research/scripts/run_llamacpp_dspark_wsl.sh
wsl -d Ubuntu-22.04 -- bash -lc 'CONF_MIN=0.5 RUN_LABEL=conf05 bash /mnt/d/proj/dspark-blog/research/scripts/run_llamacpp_dspark_wsl.sh'
```

参数解析测试 `test-arg-parser` 已通过。构建和转换原始日志位于 `artifacts/`，大模型 GGUF 被 `.gitignore` 排除。

## 本机最快路径

不要在 `/mnt/d` 上直接全量编译：跨 NTFS 的大量小文件 I/O 很慢。源码保留在 D 盘做审计，在 WSL 原生文件系统构建，然后读取 D 盘 GGUF；Q8_0 能把 target+draft 文件控制在约 4.6 GiB。启动模型约 44–49 秒，启动后短生成约 7–9 tok/s。
