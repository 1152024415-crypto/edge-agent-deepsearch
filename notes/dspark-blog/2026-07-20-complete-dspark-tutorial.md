# DSpark Complete Tutorial Document Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 写成一篇可独立阅读的中文教程与实验记录，把 DSpark 算法步骤映射到 DeepSpec、llama.cpp 和 SGLang 的直接相关代码。

**Architecture:** 正文采用“统一执行模型 → 三阶段实验与源码映射 → 横向对照 → 复现路线”的结构。已有阶段 spec、结构化 JSON 和源码是事实来源；正文只精选 DSpark 直接相关符号，原始日志不整段复制。

**Tech Stack:** Markdown、Mermaid、Git、PowerShell、ripgrep、Python JSON 校验。

---

### Task 1: 建立正文骨架与统一原理

**Files:**
- Create: `DSpark-完整实验与实现导读.md`
- Reference: `specs/004-complete-tutorial-document-design.md`

- [x] **Step 1: 写入正文目录、阅读说明和证据等级**

创建 11 个设计中确认的一级章节，明确“本机实跑 / CPU 源码验证 / 官方数据”三类证据。

- [x] **Step 2: 写统一 DSpark 执行模型**

给出 block draft、Markov 修正、confidence、target verify、accept/commit 的符号定义、伪代码和 Mermaid 数据流。

- [x] **Step 3: 检查术语一致性**

运行：

```powershell
rg -n "draft block|verify window|acceptance length|survival" "DSpark-完整实验与实现导读.md"
```

预期：每个术语首次出现时有中文解释，后续含义一致。

- [x] **Step 4: Commit（若 auto_commit 开启）**

检查 `.agent/config.yml`；若不存在或 `auto_commit: true`，在最终整体验收后统一提交正文，避免未完成长文进入历史；若 `auto_commit: false`，不暂存、不提交。

### Task 2: 写三阶段实验与 DSpark 源码导读

**Files:**
- Modify: `DSpark-完整实验与实现导读.md`
- Reference: `D:\proj\dspark-blog\deepspec\specs\001-qwen3-4b-dspark-first-run-record.md`
- Reference: `specs/001-llamacpp-dspark-experiment.md`
- Reference: `specs/002-sglang-dspark-experiment.md`
- Reference: `results/llamacpp-summary.json`
- Reference: `results/sglang-summary.json`

- [x] **Step 1: 写 DeepSpec 章节**

记录环境、命令、32-token 指标、下载/WSL 故障，并解读 evaluator、draft ops、Markov head、verify、update 五个 DSpark 直接相关边界。

- [x] **Step 2: 写 llama.cpp 章节**

记录 PR、GGUF 转换、构建、错误入口根因、两轮 confidence 实验，并解读 tensor 注册、`build_dspark_markov_head()`、proposal 截断和 `ctx_other`。

- [x] **Step 3: 写 SGLang 章节**

记录合并版本、56 个 CPU 测试、CUDA guard，并解读 `DSparkWorkerV2._forward_decode()`、block proposer、confidence/STS、planner、ragged verify、accept/commit。

- [x] **Step 4: 逐项核对数字**

运行 Python 读取两个 summary JSON，并与正文表格中的 token 数、速度、accept 数和测试数人工对照；DeepSpec 数字与首次运行 spec 对照。

- [x] **Step 5: Commit（若 auto_commit 开启）**

检查 `.agent/config.yml`；最终整体验收通过后统一提交。若 `auto_commit: false`，跳过暂存和提交。

### Task 3: 写横向对照、复现路线和源码索引

**Files:**
- Modify: `DSpark-完整实验与实现导读.md`
- Reference: `specs/003-three-implementations-comparison.md`
- Reference: `scripts/run_llamacpp_dspark_wsl.sh`
- Reference: `scripts/run_sglang_cpu_test.py`

- [x] **Step 1: 写三实现映射图和对照表**

比较算法表达、置信度使用方式、验证粒度、调度层级、硬件要求和最适合的学习目标。

- [x] **Step 2: 写本机最快复现路线**

给出 DeepSpec、llama.cpp、SGLang CPU 测试的可复制命令，说明预期耗时、文件体积和硬件边界。

- [x] **Step 3: 写 NVIDIA 后续实验设计**

只给 SGLang static/compact/non-spec 的公平对照方法和官方启动入口，不把官方数据冒充本机结果。

- [x] **Step 4: 写源码阅读索引**

按“先算法张量、再本地运行时、最后生产调度”排序，每个文件注明阅读问题。

- [x] **Step 5: Commit（若 auto_commit 开启）**

检查 `.agent/config.yml`；最终整体验收通过后统一提交。若 `auto_commit: false`，跳过暂存和提交。

### Task 4: 文档验收、入口更新与提交

**Files:**
- Modify: `README.md`
- Verify: `DSpark-完整实验与实现导读.md`

- [x] **Step 1: 更新 README 入口**

把完整教程置于阅读顺序首位，原有阶段 spec 保留为详细证据。

- [x] **Step 2: 扫描占位符和结构**

运行：

```powershell
rg -n "TODO|TBD|待补|以后再写" "DSpark-完整实验与实现导读.md"
rg -n "^#{1,4} " "DSpark-完整实验与实现导读.md"
```

预期：无占位符；章节顺序与设计 spec 一致。

- [x] **Step 3: 校验引用的本地文件和源码符号**

用 `Test-Path` 验证文档引用的实验文件，用 `rg` 验证所有重点函数确实存在于固定 commit。

- [x] **Step 4: 检查 Markdown 与 Git diff**

运行：

```powershell
git diff --check
git diff --stat
```

预期：无空白错误；只改正文、README 和本计划的完成状态。

- [x] **Step 5: Commit（若 auto_commit 开启）**

读取 `.agent/config.yml`。若不存在或 `auto_commit: true`：

```powershell
git add "DSpark-完整实验与实现导读.md" README.md plans/2026-07-20-complete-dspark-tutorial.md
git commit -m "docs: add complete DSpark implementation tutorial"
```

若 `auto_commit: false`，跳过暂存和提交并报告文件已准备好。
