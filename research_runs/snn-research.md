## A. 近期 SNN 论文

arXiv Atom API 扫 2026-04-15~2026-07-15（近 3 个月）窗口，按收紧口径（摘要含 `spiking neural network` / `spikformer` / `spiking transformer` / `spiking neuron model` / `\bsnn\b`，不靠 `neuromorphic` 单独判定）筛得 129 篇真 SNN；下面精选 20 篇（优先顶会/高相关/方向多样性：硬件加速、Spikformer、剪枝量化、医疗、语音、汽车、安全、理论），并入本周 run 里 `方向:SNN` 标签的 6 篇（标 ★，其中 2607.12862 摘要未直含 SNN 关键词但被 run 分类器判为 SNN 方向，按任务要求并入）。全部为 arXiv 论文，窗口内无顶会正式 proceedings，故以 arXiv preprint 为准。

| 标题 | 日期 | arxiv 链接 | 一句大白话 |
|---|---|---|---|
| Mega: A 22 nm Convolutional SNN Accelerator Achieving 0.375 pJ/SOP for Efficient Edge Vision | 2026-06-29 | https://arxiv.org/abs/2606.30039 | 22nm 工艺卷积 SNN 加速器，每 SOP 仅 0.375 pJ，瞄准低功耗边缘视觉 |
| SpikON: A Dual-Parallel and Efficient Accelerator for Online SNN Learning | 2026-06-29 | https://arxiv.org/abs/2606.30926 | 支持在线学习(非只推理)的 SNN 加速器，双并行结构解决在线训练难部署 |
| SpikeLogBERT: Energy-Efficient Log Parsing Using Spiking Transformer Networks | 2026-06-30 | https://arxiv.org/abs/2606.31781 | 用 Spiking Transformer 改造 BERT 做日志解析，低功耗版 NLP |
| Dendritic In-Context Learning in a Single-Layer Spiking Neural Network | 2026-07-02 | https://arxiv.org/abs/2607.02283 | 单层 SNN 靠树突结构实现 In-Context Learning，过 Garg-2022 基准 |
| A Spiking Sequence Generator for Polar Trajectories on Neuromorphic Hardware | 2026-07-02 | https://arxiv.org/abs/2607.02753 | 在神经形态硬件上生成极坐标轨迹的 SNN 序列控制器，可解释+低功耗 |
| AIGOR: A Modular, Event-Driven Neuromorphic Architecture for Configurable SNN Inference | 2026-07-03 | https://arxiv.org/abs/2607.03191 | 模块化事件驱动架构，跨多种神经元模型/硬件统一跑 SNN 推理 |
| Online Data Reduction with SNN: Temporal-Coincidence Encoder for ePIC dRICH Detector | 2026-07-03 | https://arxiv.org/abs/2607.03492 | 用 SNN 在线压缩高能物理探测器 32 万通道数据，对付 SiPM 暗计数 |
| EEG-Based Imagined Speech Decoding Using a Hybrid CNN-SNN Architecture | 2026-07-04 | https://arxiv.org/abs/2607.03844 | CNN+SNN 混合架构解脑电想象语音，服务 BCI 通信 |
| Burst Spiking Neural Networks | 2026-07-05 | https://arxiv.org/abs/2607.11914 | 提出 Burst 脉冲机制，同时提升 SNN 精度与对抗扰动鲁棒性 |
| Efficient Perception in Automotive Detection and Tracking Using Neuromorphic Computing | 2026-07-06 | https://arxiv.org/abs/2607.04921 | 把 SNN 用到汽车检测与跟踪，主打边缘低功耗可持续 |
| A Hardware-Aware Open-Source Framework for Design Space Exploration of Mixed-Signal SNNs | 2026-07-07 | https://arxiv.org/abs/2607.06456 | 开源框架模拟混合信号 SNN 硬件非理想特性，做架构设计空间探索 |
| Breaking Local-Minimum Traps in SNN-Based Solvers for CSPs via Parallel Tempering ★ | 2026-07-09 | https://arxiv.org/abs/2607.08897 | 用并行回火让随机 SNN 解约束满足问题时不陷局部最小 |
| Event Burst Trigger: An Availability Backdoor Attack on Event-Based SNN Object Detection | 2026-07-10 | https://arxiv.org/abs/2607.09115 | 揭露事件相机 SNN 检测器的可用性后门攻击，安全方向 |
| Efficient and Robust SNN for sEMG-Based Muscle Fatigue Detection ★ | 2026-07-13 | https://arxiv.org/abs/2607.11065 | 用 SNN 做肌电疲劳检测，低功耗可穿戴场景 |
| SpikeDS: Dual Sparsity Spikformer for Perineural Invasion Prediction in 3D MRI ★ | 2026-07-13 | https://arxiv.org/abs/2607.11986 | 双稀疏 Spikformer 在 3D MRI 里预测胆管癌神经侵犯 |
| Event-based Neural Decoding for Neuroprosthetic Motor Control ★ | 2026-07-13 | https://arxiv.org/abs/2607.11445 | 事件驱动 SNN 解神经假肢运动控制，降延迟/能耗/体积 |
| A Comparative Analysis of Ising Formulations for Neuromorphic Maximum-Likelihood Channel Decoding ★ | 2026-07-14 | https://arxiv.org/abs/2607.12862 | 比较多种 Ising 构型做最大似然信道解码（神经形态求解器） |
| A 32-channel event-based bio-signal analog front-end with adaptive delta and pulse frequency encoding ★ | 2026-07-14 | https://arxiv.org/abs/2607.12901 | 32 通道事件驱动生物信号模拟前端 ASIC，配脉冲频率编码 |
| SpikeTimer: Exploring Active Copyright Protection in SNN via Temporal Backdoor Regularization | 2026-06-25 | https://arxiv.org/abs/2606.26841 | 给 SNN 加时间后门做主动版权保护（SNN 版水印） |
| Criticality-Constrained Iterative Pruning for Energy-Efficient SNNs | 2026-06-26 | https://arxiv.org/abs/2606.30676 | 按临界性约束迭代剪枝 SNN，保能耗效率不掉精度 |

## B. SNN 框架对比表

GitHub API 实查 8 个 SNN 框架 repo（2026-07-15 取数）。状态判定：archived→「已归档」；否则 pushed_at 距今 ≤6 月→「活跃」，>6 月→「低活动」。

| 框架 | stars | 最近更新 | 语言 | 许可 | 状态 | 定位 |
|---|---|---|---|---|---|---|
| SpikingJelly | 2067 | 2026-07-12 | Python | NOASSERTION | 活跃 | PyTorch 深度学习 SNN 框架，训练为主，国内生态最活跃 |
| snnTorch | 2012 | 2026-06-29 | Python | MIT | 活跃 | PyTorch SNN 深度/在线学习库，文档教程好，社区大 |
| BindsNET | 1685 | 2026-07-10 | Python | AGPL-3.0 | 活跃 | PyTorch 模拟 SNN，研究友好，偏仿真 |
| Brian2 | 1200 | 2026-07-06 | Python | NOASSERTION | 活跃 | 通用脉冲网络模拟器，计算神经科学为主 |
| Norse | 812 | 2026-07-07 | Python | LGPL-3.0 | 活跃 | PyTorch SNN 深度学习库，偏研究 |
| Lava | 739 | 2026-05-13 | Jupyter Notebook | NOASSERTION | 已归档(2026-05-13) | Intel 神经形态计算框架，2026-05-13 全仓归档停更 |
| NEST | 655 | 2026-07-13 | C++ | GPL-2.0 | 活跃 | 大规模脉冲网络模拟器，HPC 神经科学 |
| Sinabs | 118 | 2026-02-05 | Python | Apache-2.0 | 活跃 | SynSense 出品，PyTorch 训练+支持神经形态硬件推理 |

## C. 厂商动态

- **BrainChip** | AKD1500 神经形态处理器宣布商用量产发货；Akida 2 IP 授权给 EDGEAI 做智能电表；AkidaTag 可穿戴参考平台发布；签 ASICLAND/ForwardEdge ASIC/MicroIP/Klepsydra/MDS Intelligence 等生态伙伴 | 2026-03~06 | https://investor.brainchip.com/
- **SynSense** | 发布下一代神经形态视觉芯片 Aeveon™，并据新闻页 slug 关联一轮战略融资以加速高速 3D 神经形态处理器 DYNAP™-CNN2 开发 | 2026-06-24 | https://www.synsense.ai/news/
- **SynSense** | 推出 BridgeMonitoring 基础设施智能方案，同期开放神经形态开发者社区论坛与开发套件 datasheet 访问 | 2026-05-21 | https://www.synsense.ai/news/
- **Innatera** | 在 CES 2026 展示真实场景神经形态边缘 AI；Pulsar（首款面向传感器边缘的大众市场神经形态 MCU，含 SNN 加速+RISC-V+CNN 加速）已发布 | 2026-01(CES) | https://innatera.com/
- **Innatera** | 签 Joya 为 ODM 客户、与 42T 联合推动智能产品创新、VLSI EXPERT 采用其 SNN 处理器建人才池（具体日期官方页未标，据 innatera.com 首页新闻条目） | 2026（日期未标） | https://innatera.com/
