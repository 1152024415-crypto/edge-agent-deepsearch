# DSpark 论文与源码架构深化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 把现有 DSpark 实验导读扩展为覆盖论文训练、半自回归推理、置信度调度和三套开源实现架构的完整教程与实验报告。

**Architecture:** 论文图提供动机与原始结论，Mermaid 图重绘训练/推理/调度数据流，固定 commit 源码提供函数和状态映射。本机实验、论文结果、源码推断保持三种证据层级，不互相替代。

**Tech Stack:** Markdown、Mermaid、arXiv HTML/PNG、PowerShell、Git、DeepSpec Python/PyTorch、llama.cpp C++/GGML、SGLang Python/Triton。

---

### Task 1: 固定论文图与授权信息

**Files:**
- Create: `assets/paper/dspark-figure-{1,2,4,5,6,8}.png`
- Create: `assets/paper/README.md`

- [x] **Step 1: 下载论文原图**

从 `https://arxiv.org/html/2607.05147v1/x{1,2,4,5,6,8}.png` 下载六张图，文件名使用稳定的 figure 编号。

- [x] **Step 2: 记录来源与授权**

在 `assets/paper/README.md` 记录论文标题、arXiv v1、作者、每张图用途和 CC BY 4.0 链接。

- [x] **Step 3: 校验图片**

运行：

```powershell
Get-ChildItem assets\paper\dspark-figure-*.png | ForEach-Object { "$($_.Name) $($_.Length)" }
```

预期：六张 PNG 均存在且大小大于 1 KB。

- [x] **Step 4: 提交**

检查 `.agent/config.yml` 的 `auto_commit`；不存在时按默认 `true`。提交信息：`docs: add attributed DSpark paper figures`。

### Task 2: 增写论文架构与训练章节

**Files:**
- Modify: `DSpark-完整实验与实现导读.md`

- [x] **Step 1: 新增论文贡献总览**

结合 Figure 1、2、4，解释 suffix decay、parallel backbone、Markov/RNN sequential head、anchor-first block 和串行开销边界。

- [x] **Step 2: 新增训练数据流**

加入 Mermaid 训练图并解读 target 冻结、共享 embedding/lm-head、anchor block、CE/TV/confidence loss、位置权重。

- [x] **Step 3: 新增置信度调度架构**

结合 Figure 5、6、8，区分 conditional confidence、prefix survival、STS 与 SPS-aware budget，并解释 non-anticipating property。

- [x] **Step 4: 校验新增概念**

运行 `rg -n "suffix decay|Markov head|RNN head|Sequential Temperature Scaling|non-anticipating|anchor|confidence loss" DSpark-完整实验与实现导读.md`，预期每项均有正文命中。

- [x] **Step 5: 提交**

检查 `auto_commit`；提交信息：`docs: explain DSpark paper architecture and training`。

### Task 3: 深化三套源码调用链与状态架构

**Files:**
- Modify: `DSpark-完整实验与实现导读.md`

- [x] **Step 1: DeepSpec 训练与推理映射**

补齐训练 loss、模型 head、proposal、verify、update 的函数链；对每个关键函数记录输入、输出、状态副作用和论文公式对应。

- [x] **Step 2: llama.cpp 运行时映射**

补齐 HF→GGUF tensor→GGML graph→proposal→target verify 的调用链，并解释 `ctx_other`、共享权重、双 KV cache 及 `conf_min` 不等于硬件感知调度器。

- [x] **Step 3: SGLang production 映射**

补齐 worker→proposer→confidence/STS→planner→ragged layout→verify→accept/commit→confidence relay 的调用链，解释动态 batch 与 CUDA graph tier。

- [x] **Step 4: 新增状态所有权表**

表格覆盖 token ids、draft logits、Markov feature、confidence、survival、target hidden、target/draft KV cache、accepted prefix、bonus token。

- [x] **Step 5: 校验源码引用**

逐个检查文档引用的本地文件存在，并用 `rg -n` 确认函数名位于固定源码版本。

- [x] **Step 6: 提交**

检查 `auto_commit`；提交信息：`docs: map DSpark architecture to open-source runtimes`。

### Task 4: 边界矩阵、架构问题与最终校验

**Files:**
- Modify: `DSpark-完整实验与实现导读.md`
- Modify: `README.md`
- Modify: `plans/2026-07-20-paper-source-architecture-expansion.md`

- [x] **Step 1: 新增实现覆盖矩阵**

对训练、Markov/RNN、confidence、STS、hardware-aware scheduler、ragged verify、overlap、CPU/GPU 实跑逐项标注 DeepSpec、llama.cpp、SGLang 的覆盖状态。

- [x] **Step 2: 回答八个架构问题**

每个回答必须关联论文机制与至少一个源码落点，并明确事实、推断或未验证边界。

- [x] **Step 3: 更新阅读入口与计划状态**

README 标注教程已包含论文图、训练和架构解读；将本计划完成项勾选。

- [x] **Step 4: 运行完整校验**

检查图片数和大小、Markdown 代码围栏配对、Mermaid 配对、必需章节、禁止占位符、实验 JSON、`git diff --check` 和工作树状态。

- [x] **Step 5: 最终提交**

检查 `auto_commit`；提交信息：`docs: complete DSpark paper-to-source report`。
