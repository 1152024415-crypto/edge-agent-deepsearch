# DSpark 论文与源码架构深化设计

## 1. 目标

在现有 `DSpark-完整实验与实现导读.md` 基础上，新增一条严格围绕 DSpark 论文贡献展开的讲解主线：先说明论文试图解决的生成质量与系统效率问题，再结合 DeepSpec、llama.cpp、SGLang 固定版本源码解释训练、推理和生产调度如何落地。

本文不扩展为三个项目的通用架构介绍；所有新增代码均须直接回答 DSpark 论文提出的机制。

## 2. 表达方案

采用“论文原图 + 中文重绘 + 源码映射”组合：

1. 引用论文 Figure 1、2、4、5/6、8，标明图号、论文链接、作者和 CC BY 4.0 来源。
2. 原图用于说明论文动机、实验现象和生产结论，不冒充本机实验结果。
3. 用 Mermaid 重绘运行时调用链、训练数据流、状态提交和 production scheduling。
4. 每个架构节点给出固定源码文件、函数、关键张量或状态。

## 3. 内容结构

### 3.1 论文贡献主线

- 并行 drafter 的首位置容量优势与 suffix decay。
- 重并行 backbone 与轻量 sequential head 的半自回归结构。
- Markov head、RNN head 的条件分布与部署取舍。
- confidence head 的条件接受概率、prefix survival 的累积语义。
- STS 后处理校准。
- hardware-aware prefix scheduler、SPS 曲线和动态 verify budget。
- 无损性所要求的连续前缀与 non-anticipating property。

### 3.2 训练架构

- target 冻结，embedding/lm-head 共享并冻结。
- anchor-bounded block 训练样本。
- CE、分布匹配、confidence 三项 loss 与位置权重。
- DeepSpec 中训练模型、Markov/Confidence head 和 loss 的源码映射。
- 论文生产训练优化若未开源，明确标为论文信息而非本机源码验证。

### 3.3 推理与 serving 架构

- DeepSpec：reference proposal、target verification、cache update。
- llama.cpp：DSpark tensor 的 GGUF 转换、GGML graph 中的 sequential loop、`ctx_other` 共享 target 权重、静态 `conf_min` 边界。
- SGLang：proposal/confidence、STS、SPS planner、ragged verify、CUDA graph tier、accept/commit 和 overlap relay。

## 4. 必须回答的架构问题

1. 为什么轻量串行 head 不会把 DSpark 退化为普通自回归 drafter？
2. Markov 低秩矩阵如何将前一 token 映射为下一位置 logit bias？
3. conditional confidence 与 prefix survival 为什么不能混用？
4. STS 为什么是调度正确估值所需，而不只是提高分类准确率？
5. 为什么 verification 只能保留连续前缀？回看未来 candidate 为什么可能引入 selection bias？
6. 动态 verify length 为什么带来 ragged batch、padding、CUDA graph 和 CPU/GPU 同步问题？
7. target/draft 的共享权重、hidden state、KV cache 分别由谁拥有，接受后怎样提交？
8. 三套开源实现分别覆盖论文的哪些部分，哪些只是静态阈值或工程近似？

## 5. 证据与边界

- 论文事实引用 arXiv v1 和原图。
- 源码事实固定到现有仓库 commit，并使用本地文件与行号。
- 本机实跑数字沿用结构化结果，不与论文生产数据混合。
- llama.cpp 的 `conf_min` 明确描述为局部阈值，不等同于论文 hardware-aware scheduler。
- SGLang CPU 测试不能证明 CUDA/Triton production path 已在本机运行。
- 论文中的内部生产训练优化若无对应开源代码，只解释架构含义，不虚构源码落点。

## 6. 验收标准

- 文档包含论文训练、半自回归推理、confidence/STS、hardware-aware scheduling 四条完整主线。
- 至少五组论文图得到来源标注和源码解释。
- 三套实现均有端到端调用链或数据流图。
- 关键代码讲解包含输入、输出、状态、副作用和与论文公式的对应关系。
- 新增“完整论文机制 / 开源实现覆盖 / 本机验证边界”矩阵。
- Markdown 结构、代码围栏、本地图片、引用链接和实验 JSON 全部通过校验。
