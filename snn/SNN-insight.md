# SNN 洞察：脉冲神经网络端侧落地

> SNN 的价值不是"二值脉冲"本身，而是端到端的动态稀疏：只有当输入在时间上稀疏、网络发放率低、硬件能跳过零事件、权重和神经元状态主要驻留片上、事件路由开销可控时，理论上的加法与稀疏优势才会变成整机能耗优势。最可信的近期落地不是静态图像分类或大模型，而是 always-on 时序感知（关键词唤醒、声音事件、振动/电流异常、毫米波雷达、IMU/ECG/EEG、事件相机）。算法精度已不再是唯一主矛盾——NeurIPS 2024 的 QKFormer 在 ImageNet-1K 报告 85.65% top-1，但这仍是论文训练结果，不等于同一模型已经在端侧神经形态芯片上实现同等精度、吞吐和能效。产业瓶颈已转向软件、映射、基准和产品集成：NIR 正在尝试成为类似 ONNX 的神经形态中间表示，NeuroBench 开始统一算法与系统评测，与此同时 Intel 在 2026-05-13 归档 Lava 框架，表示下一代 Loihi 与新 SDK 将转向开放标准 AI 框架。端侧 SoC 的合理动作是先做系统级 PoC（建议 12 周、双任务、双基线、Go 条件：质量下降不超过 1 个百分点、端到端能耗至少降低 5 倍、p95 延迟不劣化、可稳定复现），而不是先改主 NPU。

## 1. SNN 是什么

### 1.1 一句话定义

**SNN（Spiking Neural Network，脉冲神经网络）**是一类模拟真实大脑神经元工作方式的神经网络。和传统神经网络（ANN）输出连续数值不同，SNN 中的神经元只在积累足够信号后才发出一个短暂的**脉冲（spike）**，信息编码在脉冲的**时间、频率和模式**中。

先分清四个常被混用的概念：

| 概念 | 本质 | 必然使用 spike？ | 例子 |
|---|---|---:|---|
| **SNN** | 具有神经元状态、阈值发放和时间动态的网络模型 | 是（至少神经元间通信通常为事件） | LIF-SNN、Spikformer、RSNN |
| **神经形态计算** | 借鉴神经系统的局部状态、存算邻近、稀疏通信、异步/事件驱动等原则的计算范式 | 不一定 | Loihi 2、BrainScaleS-2、NorthPole |
| **事件传感器** | 只报告变化或事件的传感器 | 输出事件，但后端可用 ANN | DVS 事件相机、事件音频前端 |
| **脑启发 ANN 加速器** | 用存算邻近、分布式 SRAM 等方式高效运行普通 ANN | 否 | IBM NorthPole |

因此"神经形态芯片"不等于"SNN 芯片"，"事件相机 + ANN"可能比"帧相机 + SNN"更接近真正的事件驱动系统；IBM NorthPole 是高效 ANN 推理架构，其公开基准主要是 ResNet、YOLO、BERT 等 ANN，不应放进严格的 SNN 芯片性能表。

### 1.2 从生物神经元讲起

**生物神经元**的结构：

- **树突**（dendrites）：接收来自其他神经元的信号
- **细胞体**（soma）：累积信号
- **轴突**（axon）：当信号累积到一定阈值，产生一次电脉冲（动作电位），沿着轴突传给下游神经元

关键机制：

1. 神经元在"静息状态"时，细胞膜内外存在电位差（约 $-70\,\mathrm{mV}$），叫**静息膜电位**
2. 当上游神经元释放神经递质，产生兴奋性信号，膜电位上升
3. 当膜电位达到**阈值**（约 $-55\,\mathrm{mV}$），神经元**发放**（fire）一个动作电位
4. 发放后，膜电位迅速回落，进入短暂的**不应期**（refractory period），期间不能再发放
5. 如果没有足够兴奋信号，膜电位会慢慢**泄漏**回静息状态

这个过程可以用一个极简模型描述——**LIF 模型**（Leaky Integrate-and-Fire，漏电积分放电）。连续时间形式：

$$
\frac{\mathrm{d}V(t)}{\mathrm{d}t}
= -\frac{V(t)-V_{\mathrm{rest}}}{\tau}+R\,I(t)
$$

发放规则：当 $V(t) \geq V_{\mathrm{th}}$ 时发放一个脉冲，随后令 $V(t) \leftarrow V_{\mathrm{reset}}$。

离散时间形式（实现与训练中常用）：

$$
\tilde u_i[t]=\beta u_i[t-1]+\sum_j w_{ij}s_j[t]+I_i[t],
$$

$$
s_i[t]=H\!\left(\tilde u_i[t]-V_{\mathrm{th}}\right),
$$

其中 $u$ 是膜电位，$\beta\in[0,1]$ 是泄漏系数，$s\in\{0,1\}$ 是脉冲，$H$ 是阶跃函数。发放后常见两种重置：

$$
\text{硬重置：}\quad u_i[t]=(1-s_i[t])\tilde u_i[t]+s_i[t]V_{\mathrm{reset}},
$$

$$
\text{减阈值重置：}\quad u_i[t]=\tilde u_i[t]-s_i[t]V_{\mathrm{th}}.
$$

减阈值重置保留超过阈值的"余量"，ANN-to-SNN 转换时通常比直接清零更少引入量化误差。

其中各符号含义：

- $V(t)$ / $u$：膜电位
- $V_{\mathrm{rest}}$：静息电位
- $\tau$：膜时间常数（决定电位衰减速度）；$\beta$：离散泄漏系数
- $R$：膜电阻
- $I(t)$：当前输入电流
- $V_{\mathrm{th}}$：发放阈值
- $V_{\mathrm{reset}}$：重置电位
- $w_{ij}$：突触权重；$s_j[t]$：上游神经元 $j$ 在 $t$ 步的脉冲

```text
输入事件 → 突触加权累积 → 膜电位泄漏 → 达到阈值?
                                         ├ 否 → 继续泄漏
                                         └ 是 → 发送 spike → 重置或减阈值 → 继续泄漏
```

**这就是 SNN 的计算核心。** 每个神经元做的事情很简单：积累输入、达到阈值就放电、放电后休息。但大量神经元连接在一起，就能产生复杂的计算能力。

### 1.3 "spike 是 0/1"不等于整个网络只有 0/1

SNN 内部至少还存在：

- 膜电位、适应阈值、突触电流等有状态变量；
- 多比特权重；
- 可能的延迟、分区、读出和归一化；
- 某些硬件支持 graded spike，即事件携带多比特载荷（Loihi 2 就在纯二值 spike 之外加入了可编程神经元与 graded spike）。

"乘法可全部变成加法"只在前突触激活确实是 0/1、权重读取和累加可按事件跳过时成立；首层输入编码、归一化、残差、注意力、读出等部分常仍含乘法或稠密操作。

### 1.4 信息怎么编码

在 SNN 中，信息不是用 $0.73$ 或 $-1.2$ 这样的连续数字表示的，而是编码在脉冲中。主要的编码方式：

| 编码方式 | 信息位于 | 优点 | 主要代价/风险 | 适合输入 |
|---|---|---|---|---|
| **频率编码**（Rate Coding） | 时间窗内 spike 数 | 鲁棒、易与 ReLU 对齐 | 需要较长时间窗、脉冲多 | ANN-to-SNN、静态输入 |
| **时间编码 / TTFS**（Temporal / latency） | 首个 spike 的时间 / 精确时序模式 | spike 少、低延迟潜力 | 对时间噪声敏感、训练更难 | 快速分类、语音、控制、事件视觉 |
| **群体编码**（Population Coding） | 神经元群体联合活动 | 鲁棒、可表达连续量 | 占用更多神经元 | 控制、回归、神经信号 |
| **相位编码**（Phase Coding） | 脉冲相对于振荡周期的相位 | 与脑节律耦合 | 硬件时间精度要求高 | 听觉定位 |
| **Delta / sigma-delta** | 信号变化量 | 与连续传感器和稀疏变化相容 | 阈值选择、噪声抖动 | 音频、IMU、模拟传感器 |
| **原生事件** | 传感器直接输出事件 | 避免 frame-to-spike 开销 | 依赖新传感器和数据集 | DVS、事件触觉 |

### 1.5 SNN 的三个核心特性

**1. 事件驱动（Event-driven）**
没有输入信号时，神经元保持静息，理想事件驱动数据通路不执行动态突触计算。但要注意：**"无事件时不消耗计算资源"是需限定的表述**——传感器、漏电、状态保持、控制核和系统常驻功耗仍然存在。这和传统神经网络每帧都要做完整计算不同。

→ **意义**：适合传感器数据（摄像头检测到变化才处理、麦克风听到声音才分析）。

**2. 时间天然性（Temporal）**
神经元的膜电位随时间演化，天然处理时序信息。不需要像 LSTM 那样用特殊结构"记住"时间。

→ **意义**：适合语音、振动、生物电信号等连续时间序列。

**3. 稀疏计算（Sparse）**
在任意时刻，只有少数神经元发放脉冲。大部分神经元大部分时间处于静息状态。

→ **意义**：在专用神经形态硬件上，稀疏活动意味着极低功耗——前提是硬件能按事件调度且路由不过载。

### 1.6 SNN 的局限

SNN 不是万能的，它有明显短板：

- **训练困难**：脉冲发放是阶跃函数（不可导），标准反向传播无法直接工作
- **需要时间步**：SNN 需要多个时间步积累信号才能得出结论；rate coding 常有窗口延迟，但 TTFS、早停和异步事件反而可实现低平均延迟
- **静态输入不划算**：对于一张静态图片，编码成 spike 序列需要额外时间步，不如直接 CNN 处理（算法研究已能在 ImageNet 达高精度，但作为产品选择通常仍不如量化 CNN/NPU 实际）
- **软件生态不成熟**：没有 PyTorch/TensorFlow 级别的通用框架，部署工具链碎片化，Intel Lava 已于 2026-05-13 归档
- **在 GPU 上不一定省电**：SNN 的能效优势需要在**专用神经形态硬件**上才能体现。GPU 擅长规则、批量、稠密的矩阵乘；SNN 则引入时间维、条件发放、稀疏索引、神经元状态更新和不规则事件通信。若用稠密张量把 $T$ 个时间步全部展开，计算量近似放大 $T$ 倍，且大量零值仍被计算。GPU 训练 SNN 的价值主要是开发效率与吞吐，不应拿 GPU 模拟功耗证明端侧 SNN 能效

## 2. SNN 和 ANN 到底有什么区别

| 维度 | ANN（传统神经网络） | SNN（脉冲神经网络） |
|---|---|---|
| **信号类型** | 连续实数值（如 $0.73$、$-1.2$） | 离散脉冲（发放 or 不发放） |
| **激活函数** | ReLU、Sigmoid、Tanh、Softmax 等 | 阈值比较 + 脉冲发放（Heaviside 阶跃函数） |
| **信息编码** | 激活值的大小 | 脉冲的时间、频率、模式 |
| **时间处理** | 通常无时间维度（一帧算一帧）；RNN/LSTM 显式引入时间 | 天然有时间维度，膜电位随时间演化 |
| **计算方式** | 每层所有神经元同时计算（密集矩阵乘法） | 只有接收到输入的神经元才计算（事件驱动） |
| **可训练性** | 成熟：反向传播 + 梯度下降，工具完善 | 困难：阶跃函数不可导，需要特殊技术 |
| **硬件适配** | GPU/TPU/NPU 完美适配，密集矩阵运算 | 需要神经形态芯片才能发挥能效优势 |
| **能效** | 高功耗（即使空闲也在算） | 理论上极低功耗（无事件不计算，但需限定：传感器与系统功耗仍存在） |
| **典型任务** | 图像分类、文本理解、语音识别、生成模型 | 事件驱动感知、低功耗边缘推理、传感器处理 |

**类比理解：**

- ANN 像一个**一直亮着的灯泡**——不管有没有人看，它都在发光，消耗电力
- SNN 像一个**感应灯**——只有检测到人的时候才亮，没人时完全关闭（但感应灯的待机电路仍耗极小电）

## 3. 发展历史

### 3.1 早期基础（1907–1990s）

| 时间 | 关键节点 | 意义 |
|---|---|---|
| 1907 | Louis Lapicque 提出 integrate-and-fire 模型 | SNN 最早的数学基础 |
| 1952 | Hodgkin-Huxley 模型 | 用微分方程解释动作电位，获诺贝尔奖 |
| 1980s | Carver Mead 推动 neuromorphic engineering | 把脑启发计算从理论推进到芯片实现 |
| 1990s | STDP、SpikeProp 等学习规则 | SNN 从神经科学工具进入机器学习 |
| 1997 | Wolfgang Maass 将 SNN 称为"第三代神经网络" | 确立学术定位 |

### 3.2 芯片原型与商业化起步（2000s–2010s）

| 时间 | 关键节点 | 意义 |
|---|---|---|
| 2002 | SpikeProp：SNN 最早的梯度学习算法 | 开始解决训练问题 |
| 2013 | Qualcomm Zeroth 处理器 | 移动芯片公司首次明确押注 SNN |
| 2014 | **IBM TrueNorth**：100 万神经元，65mW | 证明大规模低功耗神经形态芯片可行 |
| 2017 | **Intel Loihi** 发布 | 首次集成片上学习能力 |
| 2019 | **清华 Tianjic** 芯片，Nature 封面 | 首个 ANN+SNN 混合芯片 |

### 3.3 软件生态与精度突破（2020s 初）

| 时间 | 关键节点 | 意义 |
|---|---|---|
| 2021 | **Intel Loihi 2** + Lava 开源框架 | 微码可编程，软件生态开放 |
| 2021 | SynSense Speck 发布 | 传感器+处理一体 SoC，<1mW |
| 2023 | **Spikformer**（ICLR 2023） | SNN 首次接入 Transformer 架构，ImageNet 74.81% |
| 2023 | **IBM NorthPole**（Science） | 25.6 TOPS/W 能效（脑启发 ANN 推理，非 SNN 芯片） |

### 3.4 规模化与 mainstream 化（2024–至今）

| 时间 | 关键节点 | 意义 |
|---|---|---|
| 2024.4 | **Intel Hala Point**：1,152 片 Loihi 2，11.5 亿神经元，最大 2,600W | 全球最大神经形态系统，部署于 Sandia，是研究系统而非端侧芯片 |
| 2024 | **NIR 标准**发表（Nature Comms） | 跨平台统一中间表示，论文演示 11 个平台；官网称 12+，文档列 9 个模拟器与 5 个硬件后端，统计维度不同 |
| 2024 | **QKFormer**（NeurIPS 2024） | 直接训练 SNN 在 ImageNet-1K 报告 85.65% top-1，超过 85% |
| 2024.8 | Nature Comms：0.3 spikes/neuron 高精度 SNN | 极端稀疏仍保持精度 |
| 2024.9 | Nature：23 位作者联合路线图论文 | 识别稀疏性、芯片间通信、可重构性为关键特征 |
| 2025 | **Proc. IEEE 最佳论文**颁给 SNN 训练教程 | 学术主流认可（Eshraghian, Lu 等） |
| 2025 | **SpikeLLM**（ICLR 2025） | 首个将 SNN 扩展至 70 亿-700 亿参数的脉冲 LLM；但其方法包含量化和混合编码，不等于 70B 纯 SNN 已在神经形态芯片部署 |
| 2025.5 | **Innatera Pulsar** 发布 | 首个大众市场神经形态 MCU |
| 2025.6 | **SpiNNaker2 @ Sandia** 部署 | 1.75 亿神经元，用于国防研究 |
| 2025.12 | **Unconventional AI** 以 \$4.5B 估值融资 \$475M | a16z + Bezos 投资；但公司目标是更广义的 biology-scale/新计算 substrate，融资事实可查但不等于 SNN 市场验证拐点 |
| 2025 | Nature Comms：商业化路径分析 | 商业化的剩余障碍已转向软件与生态 |
| 2026.2 | **Robust SNN**（ICLR 2026） | 理论连接 SNN 鲁棒性与阈值动力学 |
| 2026.5.13 | **Intel Lava 框架归档** | GitHub 显示归档；Intel 同时称在开发下一代 Loihi 与基于开放标准框架的新 SDK，重大生态冲击 |
| 2026.6 | **SpikeVLA**（ICML 2026 / 预印本） | SNN 首次进入 VLA 具身智能；公开可查为 2026-06 预印本/OpenReview 论文，技术新且尚无产品级硬件验证 |
| 2026.6 | **ExSpike**（FPL 2026） | FPGA 全事件神经形态架构；应标为新近论文而非成熟平台 |
| 2026.6 | **Adaptive Speech-to-Spike**（Interspeech 2026） | 紧凑语音编码；35k 参数变体 89.8%，完整模型最高报告 94.97% |

### 3.5 几个关键里程碑的解读

**ImageNet 准确率演进（SNN 直接训练）：**

| 年份 | SNN 模型 | SNN 准确率（ImageNet-1K top-1） | 时间步 | 说明 |
|---|---|---|---:|---|
| 2023 | Spikformer V1 | 74.81% | 4 | 首次将 spike-form self-attention 扩到 ImageNet |
| 2024 | Spikformer V2 | 80.38%；SSL 81.10% | 4；1 | SCS 与自监督提高精度；172M 版本并不"轻量" |
| 2024 | Meta-SpikeFormer（ICLR 2024） | 80.0% | 4 | 面向分类、检测、分割的 meta 架构 |
| 2024 | SGLFormer | 83.73% | 4 | 全局—局部融合，但已不是最新精度上限 |
| 2024 | **QKFormer**（NeurIPS 2024） | **85.65%** | 4 | 直接训练 SNN 超过 85%；能耗仍主要是理论操作估算 |

> **重要修正**：不能把上述 SNN 精度与"ANN 约 91%"粗略相减后宣布"仍差 7-10 个百分点"。不同规模和训练 recipe 不能直接相减；最新直接训练 SNN 已超过 85%，应做同数据、同输入、相近参数/训练 recipe、同芯片、同精度、同 batch、同测量边界下的匹配比较。

**SNN 进入大模型时代（应归为探索，不是近期端侧路线）：**

- SpikeLLM（ICLR 2025）证明脉冲机制可以参与大模型压缩/编码，扩展到 7B-70B LLM；但论文核心包含混合脉冲编码与量化 ANN，未证明 70B、端到端纯 spike-driven LLM 已在神经形态硬件上高效部署
- QSLM（DATE 2025）解决脉冲 LLM 的内存瓶颈（减少 86.5%）
- SpikeVLA（2026-06 预印本）把 SNN 带入视觉-语言-动作的具身导航，是早期研究信号，不应写成已完成的产业落地里程碑

**从实验室到市场的拐点：**

- Nature Comms 2025 的里程碑论文指出瓶颈已从"能否造出来"转向"能否围绕它建立生态"
- 融资与专利数量不能证明技术可落地，因此不作为路线判断的核心证据

## 4. 怎么训练

SNN 最大的技术挑战是**训练**。脉冲发放是一个阶跃函数（达到阈值就发放，没达到就不发放），数学上几乎处处导数为零，标准反向传播无法工作。以下是目前主流的训练方法。

### 先看 ANN 怎么做

在普通 ANN 中，训练流程你已经很熟悉：

```text
输入 x → 线性层 → ReLU → ... → 输出 ŷ
                                ↓
                          loss = f(ŷ, y)
                                ↓
                      反向传播：∂loss/∂W = ?
                                ↓
                          优化器更新 W
```

关键在于：**每一步运算都是可导的**。ReLU 虽然在 0 处不可导，但几乎处处有导数（$x>0$ 时为 1，$x<0$ 时为 0），所以反向传播可以顺利地把损失梯度传回每一个权重。

### SNN 卡在哪里

SNN 的输出不是 ReLU 那样的连续值，而是**阶跃函数**（Heaviside step function）：

$$
s = \begin{cases} 1 & \text{if } u \geq V_{\mathrm{th}} \\ 0 & \text{if } u < V_{\mathrm{th}} \end{cases}
$$

这个函数的导数是：

- $u \neq V_{\mathrm{th}}$ 时：导数为 **0**（函数值恒为 0 或恒为 1，不变化）
- $u = V_{\mathrm{th}}$ 时：**不可导**（跳跃点）

这意味着：

```text
loss → ... → s_t → u_t → W
                  ↑
            反向传播到这里，梯度 = 0
            W 收不到任何学习信号
```

如果用标准反向传播，**所有权重的梯度都会变成零**，网络完全无法学习。

### 为什么有多种训练路线？

这个"不可导"问题有多种绕过方式，每种方式对应一条训练路线：

```text
                   阶跃函数不可导，怎么办？
                          │
          ┌───────────────┼───────────────┐
          │               │               │
    绕过阶跃函数      不训练 SNN        不用全局梯度
          │               │               │
    用平滑函数近似    先训练 ANN        只看局部时序
          │            再转换              │
          │               │               │
    代理梯度+BPTT    ANN-to-SNN        STDP
    Spiking Transformer
```

> **BPTT** = Back-Propagation Through Time（沿时间反向传播），和 RNN 的训练方式相同：把网络沿 $T$ 个时间步展开，从损失反传到第一步，累加每步对同一权重的梯度。

- **代理梯度**：前向用阶跃函数（保持脉冲语义），反向用平滑函数近似（让梯度能通过）
- **ANN-to-SNN**：先在 ANN 上训好，再利用"ReLU 激活值 ≈ 发放率"的关系转成 SNN
- **STDP**（Spike-Timing-Dependent Plasticity，脉冲时序依赖可塑性）：完全不用全局损失函数，只根据突触前后神经元的发放时间差来调整权重

下面逐一展开。

### 4.1 方法概览

| 方法 | 核心思想 | 是否需要先训练 ANN | 精度水平 | 适用场景 |
|---|---|---|---|---|
| **Surrogate Gradient + BPTT** | 前向用阶跃函数，反向用平滑函数近似梯度 | 否 | 最高（ImageNet 85%+） | GPU 训练，当前 SOTA |
| **ANN-to-SNN Conversion** | 先训练好 ANN，再转成等价 SNN | 是 | 高（接近 ANN 精度） | 利用已有 ANN 模型 |
| **STDP** | 生物启发的无监督学习，根据脉冲时序调整突触 | 否 | 中（MNIST 91-98%） | 片上学习，无监督 |
| **Spiking Transformer** | 把 Transformer 的注意力机制脉冲化 | 否 | 最高（ImageNet 85%+） | 大规模视觉任务 |
| **e-prop / 在线学习** | 资格迹 + 三因子学习规则，内存恒定 | 否 | 中（语音 91%） | 持续适应，硬件友好 |

#### 这五种方法的分类逻辑

这五种方法不是平行的选项，而是按**解决"不可导"问题的策略**分成三类：

| 类别 | 方法 | 核心策略 | 类比 |
|---|---|---|---|
| **直接训练** | Surrogate Gradient、Spiking Transformer | 从头训练 SNN，用技巧绕过不可导 | 直接解方程，但用近似方法处理困难项 |
| **间接转换** | ANN-to-SNN | 先在"容易的世界"（ANN）训练好，再翻译成 SNN | 先在实数域解好，再映射到离散域 |
| **局部学习** | STDP、e-prop | 不用全局损失函数，只靠局部信号更新权重 | 不解全局方程，每个连接自己适应 |

> **术语说明：** e-prop（eligibility propagation，资格迹传播）是一种三因子学习规则：每个突触维护一个"资格迹"（记录最近的前后脉冲时序），再乘以一个全局广播的学习信号（如奖励或误差）来更新权重。它的内存开销恒定（不随 $T$ 增长），适合在线学习和硬件部署。e-prop 将梯度分解为局部资格迹和广播学习信号，避免把所有时间步保存在 BPTT 图中，适合在线学习，但不能简单等同于 BPTT 的精度。

#### 什么场景用什么方法——决策树

```text
你的任务是什么？
│
├── 有标注数据，追求最高精度？
│   │
│   ├── 已有高质量 ANN 模型？ ──→ ANN-to-SNN（省训练时间）
│   │
│   └── 从头训练？ ──→ Surrogate Gradient + BPTT（当前 SOTA）
│                      或 Spiking Transformer（大规模视觉任务）
│
├── 无标注数据，想学特征？ ──→ STDP（无监督，局部学习）
│
└── 需要在线持续学习，内存有限？ ──→ e-prop（内存恒定，硬件友好）
```

**对于大多数入门者和研究项目，Surrogate Gradient + BPTT 是首选起点**——它不需要先训练 ANN，精度最高，工具链最成熟（snnTorch、SpikingJelly 等框架都支持）。

### 4.2 Surrogate Gradient（代理梯度）— 当前主流

在讲代理梯度之前，需要先理解一个更基础的问题：**SNN 为什么要"展开时间"来训练？**

#### 4.2.1 先理解 BPTT（Back-Propagation Through Time）

如果训练过 RNN（LSTM、GRU），已经用过 BPTT 了。SNN 的训练方式和 RNN 几乎一样：

```text
RNN 展开：

h_0 ──→ [W] ──→ h_1 ──→ [W] ──→ h_2 ──→ [W] ──→ h_3
        x_1              x_2              x_3
                         ↑
                   同一个 W 用了 3 次

SNN 展开（一样的结构，只是激活函数不同）：

u_0 ──→ [W, LIF] ──→ u_1, s_1 ──→ [W, LIF] ──→ u_2, s_2 ──→ [W, LIF] ──→ u_3, s_3
        x_1                        x_2                        x_3
                                     ↑
                               同一个 W 用了 3 次
```

**关键点**：

- `W` 是**同一份权重**，在 $T$ 个时间步中被重复使用
- 每个时间步产生的输出（$s_1, s_2, s_3$）都会对最终损失有贡献
- 反向传播时，$W$ 的梯度 = 来自 $t=1$ 的贡献 + 来自 $t=2$ 的贡献 + ... + 来自 $t=T$ 的贡献

#### 4.2.2 SNN 到底卡在哪里

假设一个最简单的情况：1 个神经元、3 个时间步、阈值 $V_{\mathrm{th}} = 1.0$、硬重置。

```text
输入序列: I = [0.4, 0.8, 0.6]
初始膜电位: u_0 = 0
权重: W = 1.0（固定，不学习，只看前向）
```

**前向传播**（膜电位更新：$\tilde{u}_t = 0.5 \cdot u_{t-1} + I_t$，$s_t = \Theta(\tilde{u}_t - 1.0)$，硬重置到 0）：

| 时间步 $t$ | 输入 $I_t$ | 重置前电位 $\tilde{u}_t$ | 脉冲 $s_t$ | 重置后 $u_t$ |
|---|---|---|---|---|
| 1 | 0.4 | $0.5 \times 0 + 0.4 = 0.4$ | 0（< 1.0）| 0.4 |
| 2 | 0.8 | $0.5 \times 0.4 + 0.8 = 1.0$ | 1（≥ 1.0）| 0（硬重置）|
| 3 | 0.6 | $0.5 \times 0 + 0.6 = 0.6$ | 0（< 1.0）| 0.6 |

输出脉冲序列：$[s_1, s_2, s_3] = [0, 1, 0]$。假设损失函数 $L = (s_1 + s_2 + s_3 - y)^2$，目标 $y = 2$。

**反向传播时发生了什么？**

梯度需要从 $L$ 传回 $W$。路径是：

$$
\frac{\partial L}{\partial W} = \sum_{t=1}^{3} \frac{\partial L}{\partial s_t} \cdot \frac{\partial s_t}{\partial \tilde{u}_t} \cdot \frac{\partial \tilde{u}_t}{\partial W}
$$

问题出在 $\frac{\partial s_t}{\partial \tilde{u}_t}$：

- $t=1$：$\tilde{u}_1 = 0.4 \neq 1.0$，所以 $\frac{\partial s_1}{\partial \tilde{u}_1} = 0$
- $t=2$：$\tilde{u}_2 = 1.0$，阶跃函数在跳跃点**不可导**
- $t=3$：$\tilde{u}_3 = 0.6 \neq 1.0$，所以 $\frac{\partial s_3}{\partial \tilde{u}_3} = 0$

**结果：$\frac{\partial L}{\partial W} = 0$，权重完全无法更新。**

#### 4.2.3 代理梯度怎么解决这个问题？

代理梯度的思想极其简单：**在反向传播时，假装阶跃函数是一个平滑函数**。

**前向传播（不变）：**

$$
s_t = \Theta(\tilde{u}_t - V_{\mathrm{th}}) \quad \text{← 真正的阶跃函数，输出 0 或 1}
$$

**反向传播（替换导数）：**

$$
\frac{\partial s_t}{\partial \tilde{u}_t} \approx g(\tilde{u}_t - V_{\mathrm{th}}) \quad \text{← 用平滑函数 } g \text{ 近似}
$$

比如用 **Fast Sigmoid** 代理函数 $g(x) = \frac{1}{(\beta|x|+1)^2}$（$\beta=5$）：

| 时间步 | $\tilde{u}_t - V_{\mathrm{th}}$ | $g(\tilde{u}_t - V_{\mathrm{th}})$ | 说明 |
|---|---|---|---|
| 1 | $0.4 - 1.0 = -0.6$ | $\frac{1}{(5 \times 0.6 + 1)^2} = 0.0625$ | 梯度虽小但非零 ✓ |
| 2 | $1.0 - 1.0 = 0$ | $\frac{1}{(5 \times 0 + 1)^2} = 1.0$ | 阈值处梯度最大 ✓ |
| 3 | $0.6 - 1.0 = -0.4$ | $\frac{1}{(5 \times 0.4 + 1)^2} = 0.111$ | 梯度虽小但非零 ✓ |

**现在每一步都有非零梯度，$W$ 可以正常更新了。**

#### 4.2.4 正式公式

把手算例子推广到一般形式。脉冲发放函数 $s(u)=\Theta(u-V_{\mathrm{th}})$ 在分布意义下的导数为：

$$
\frac{\mathrm{d}s}{\mathrm{d}u}=\delta\!\left(u-V_{\mathrm{th}}\right),
$$

这就是前面手算中"梯度为零"的数学根源。代理梯度的正式定义是：

$$
\begin{aligned}
\text{前向：}\quad s
&=\Theta\!\left(u-V_{\mathrm{th}}\right), \\
\text{反向：}\quad \frac{\partial s}{\partial u}
&\approx g\!\left(u-V_{\mathrm{th}}\right).
\end{aligned}
$$

其中 $g(\cdot)$ 是代理梯度函数。下面列出常用的几种选择：

| 函数 | 公式 | 特点 |
|---|---|---|
| Rectangular（矩形） | $\begin{cases}\frac{1}{a}, & \lvert x\rvert<a, \\ 0, & \lvert x\rvert\geq a\end{cases}$ | 最简单 |
| Sigmoid | $\alpha\,\sigma(\alpha x)\left[1-\sigma(\alpha x)\right]$ | 平滑但需 $\exp(\cdot)$ |
| Fast Sigmoid | $\frac{1}{\left(\beta\lvert x\rvert+1\right)^2}$ | 无需 $\exp(\cdot)$，高效 |
| Arctangent | $\frac{\alpha}{2\left[1+\left(\frac{\pi\alpha x}{2}\right)^2\right]}$ | snnTorch 默认 |
| Piecewise Linear | $\max\!\left(0,1-\lvert x\rvert\right)$ | 最廉价 |

**关键发现**：Zenke et al. (2021) 证明代理函数的具体形状对最终精度影响不大，不同函数间差异通常在 1-2% 以内。这意味着不需要纠结选哪个函数，更重要的是网络架构和时间步设置。

**精度表现**：

| 数据集 | 精度 | 来源 |
|---|---|---|
| MNIST | ~98.4% | snnTorch Tutorial |
| CIFAR-10 | 94-95% | AAAI 2024 |
| ImageNet | 85.65%（QKFormer） | NeurIPS 2024 |

#### 4.2.5 训练时最容易被忽略的工程变量

1. **时间步 $T$**：决定可表达的时序分辨率、训练显存、延迟和操作数
2. **重置方式**：硬重置与减阈值重置会改变误差和梯度路径
3. **detach reset**：反向时是否让 reset 路径传梯度，会影响稳定性
4. **发放率正则**：只追准确率可能得到高发放率网络，部署后无能效
5. **阈值与泄漏量化**：训练中 FP32 的 $\beta$、$V_{\mathrm{th}}$ 到芯片定点格式可能出现系统误差
6. **层间残差与归一化**：含连续值的 shortcut 或 BN 会破坏"全 spike-driven"
7. **早停策略**：若输出置信度已足够，动态停止可降低平均时间步，但运行时必须支持
8. **硬件约束训练**：fan-in/out、支持的 kernel、权重位宽、状态位宽和片上 SRAM 应在训练期进入约束

### 4.3 ANN-to-SNN Conversion — 实用路线

#### 核心直觉：ReLU 激活值 ≈ 发放率

这条路线的出发点很朴素：**ANN 中 ReLU 的输出值，可以直接理解为 SNN 中神经元的平均发放率**。

```text
ANN:   ReLU(x) = 0.73
                  ↓ 理解为
SNN:   该神经元在 T 步内的发放率 = 73%
       即 T=100 步中大约发放 73 次
```

为什么这个映射成立？因为 ReLU 和脉冲发放率有一个共同的特性：**都是非负的、输入越大输出越大**。如果 ANN 的 ReLU 输出 0.73（归一化后），那么让 SNN 的神经元以每步 0.73 的概率发放脉冲，跑足够多步后，平均发放率就会趋近 0.73。

> 注意：下面用 Bernoulli 随机采样来解释"发放率如何逼近连续值"，是为了建立直觉。实际转换不用随机采样，而是通过缩放权重和阈值，让 LIF 神经元在恒定电流驱动下以确定的频率发放。随机采样只是帮助理解"为什么 T 步的平均发放率可以近似一个连续值"。

#### 数值例子：ReLU(0.73) 如何在 T 步中变成脉冲

ANN 某层 ReLU 输出为 0.73（归一化后）。转换后，SNN 神经元在每个时间步独立地以概率 $p = 0.73$ 发放脉冲。

**什么是 Bernoulli 过程？** 就是"每步独立抛一枚有偏硬币"：每步结果是 0 或 1，发放概率固定为 $p$，各步之间互不影响。跑 $T$ 步后，总脉冲数服从二项分布 $B(T, p)$，期望值为 $T \times p$。

**期望脉冲数怎么算？** 直接用 $T \times 0.73$：

- $T = 4$：$4 \times 0.73 = 2.92$
- $T = 16$：$16 \times 0.73 = 11.68$
- $T = 64$：$64 \times 0.73 = 46.72$
- $T = 256$：$256 \times 0.73 = 186.88$

但实际脉冲数必须是整数（不可能发 2.92 次），所以每次模拟的结果会在期望值附近波动。下表是一次具体模拟的结果：

| $T$ | 期望脉冲数 $T \times 0.73$ | 实际脉冲数 | 实际发放率 | 与 0.73 的误差 |
|---:|---:|---:|---:|---:|
| 4 | $4 \times 0.73 = 2.92$ | 3 | $3/4 = 0.75$ | $+2.7\%$ |
| 16 | $16 \times 0.73 = 11.68$ | 12 | $12/16 = 0.75$ | $+2.7\%$ |
| 64 | $64 \times 0.73 = 46.72$ | 47 | $47/64 = 0.734$ | $+0.6\%$ |
| 256 | $256 \times 0.73 = 186.88$ | 185 | $185/256 = 0.723$ | $-1.0\%$ |

**逐列解释：**

- **第 2 列（期望脉冲数）**：$T \times 0.73$。这是理论期望值，不是整数。
- **第 3 列（实际脉冲数）**：一次模拟中 $T$ 步里实际发放了多少次。比如 $T=4$ 时恰好发了 3 次，$T=256$ 时发了 185 次。
- **第 4 列（实际发放率）**：实际脉冲数 $/$ $T$。比如 $3/4 = 0.75$，$185/256 = 0.723$。这就是 SNN 转换后该神经元的输出。
- **第 5 列（误差）**：实际发放率与目标值 0.73 的偏差。$T$ 越大，误差越小。

**$T$ 越大，发放率越接近目标值。** 这是因为 $T$ 步的发放率只能取 $0, \frac{1}{T}, \frac{2}{T}, \ldots, 1$ 这些离散值，$T$ 越大分辨率越高，量化误差越小。

**核心权衡**：$T$ 越大 → 转换精度越高，但推理时间也越长。

#### ANN-to-SNN 不是简单地"把 ReLU 换成 LIF"

ANN-to-SNN 的目标是使有限时间窗内的脉冲读出近似 ANN 激活，并控制逐层误差累积。现代方法会重新设计源 ANN 的激活、校准阈值、折叠 BN、补偿残余膜电位，甚至进行转换后微调。低时间步转换已从"数百步 rate coding"发展到 4 步附近，但通常牺牲架构自由度或要求专门训练源 ANN。

#### 转换的完整流程

```text
1. 正常训练 ANN（ReLU 激活，标准方法）
        ↓
2. 用校准数据集统计每层激活的最大值
        ↓
3. 按比例缩放权重和阈值：
   - 让 SNN 的阈值 = 1
   - 让权重缩放因子 = ANN 该层最大激活值
   - 这样 ReLU(x) ∈ [0, max] 就映射到发放率 ∈ [0, 1]
        ↓
4. 折叠 BatchNorm（把 BN 的缩放和偏移吸收到权重和偏置中）
        ↓
5. 运行 SNN T 步，用平均发放率作为输出
```

#### 三个常见的坑

| 坑 | 为什么会出问题 | 怎么解决 |
|---|---|---|
| **负激活值** | ReLU 输出都是非负的，但如果网络中有负值（比如没加 ReLU 的残差分支），SNN 的发放率无法表示负数 | 使用 ReLU-only 架构，或引入正/负双通道编码 |
| **BatchNorm 未折叠** | BN 在推理时有缩放和偏移，直接转换会导致发放率偏移 | 必须在转换前把 BN 参数吸收到前一层的权重和偏置中 |
| **有限 T 的量化误差** | T=4 时，发放率只能是 0、0.25、0.5、0.75、1.0 五个值，无法精确表示 0.73 | 增大 T（精度提高但延迟增加），或用误差补偿技术 |

**最新进展（2024-2026）**：

- Training-Free Conversion：64 时间步仅 0.2% 精度损失（AAAI 2025）
- Error Compensation Learning：CIFAR-10 仅 2 时间步达 94.75%（2025）
- Differential Coding：极低时间步高精度（ICML 2025）

### 4.4 STDP — 生物启发的无监督学习

#### 与反向传播的根本区别

在讲 STDP（Spike-Timing-Dependent Plasticity）之前，先对比已经熟悉的反向传播：

| | 反向传播（BP） | STDP |
|---|---|---|
| **更新依据** | 全局损失函数的梯度 | 突触前、后神经元的发放时间差 |
| **信息范围** | 需要整条计算图反传 | 只看突触两端的两个神经元 |
| **需要标签？** | 是（有监督） | 否（无监督） |
| **优化目标** | 最小化损失函数 | "一起发放的连接变强" |
| **适合硬件** | GPU（全局梯度归约） | 神经形态芯片（局部更新） |

一句话总结：**反向传播从"全局对不对"出发，STDP 从"局部谁先谁后"出发。**

#### 核心原理

STDP 的规则极其简单：

```text
突触前神经元 A ──── w ────→ 突触后神经元 B

情况 1：A 先发放，B 后发放
  → "A 的脉冲对 B 的发放有贡献"
  → Δt = t_post - t_pre > 0
  → LTP（长时程增强）：w 增大

情况 2：B 先发放，A 后发放
  → "A 的脉冲对 B 的发放没有帮助"
  → Δt = t_post - t_pre < 0
  → LTD（长时程抑制）：w 减小
```

权重变化量随时间差指数衰减：

$$
\Delta w = \begin{cases} +A_+ \exp\!\left(-\dfrac{\Delta t}{\tau_+}\right) & \text{if } \Delta t > 0 \\[6pt] -A_- \exp\!\left(\dfrac{\Delta t}{\tau_-}\right) & \text{if } \Delta t < 0 \end{cases}
$$

#### 一个具体场景：STDP 在学什么？

假设你有一个 SNN 接收事件相机的输入，场景中经常出现"一个物体先出现在左侧、再移动到右侧"的模式：

```text
时间线：
  t=1: 左侧神经元 A 发放（物体出现在左）
  t=3: 右侧神经元 B 发放（物体移动到右）

STDP 的效果：
  A→B 的连接：A 先于 B → LTP → 连接增强
  B→A 的连接：B 后于 A → LTD → 连接减弱

经过多次训练后：
  A 一发放，B 就倾向于跟着发放（"预测"物体要向右移动）
```

STDP 本质上是在学习**时间因果关系**：经常先发生的事件，会获得预测后续事件的能力。

#### 为什么实际系统用 STDP 做特征提取，再单独训练读出层？

STDP 是无监督的——它不知道"这个输入是猫还是狗"，只知道"哪些神经元经常一起发放"。所以 STDP 擅长的是**学到好的特征表示**，而不是直接做分类。

典型的工程做法是**两阶段**：

```text
阶段 1（STDP，无监督）：
  输入数据 → STDP 学习前端权重 → 提取时间特征
  （不需要标签，可以在设备端在线学习）

阶段 2（监督学习）：
  STDP 学到的特征 → 冻结前端权重 → 只训练最后的线性分类器
  （用少量标签数据训练读出层）
```

**优势**：完全本地化，不需要全局误差信号，天然适合硬件片上学习。

**局限**：纯无监督，复杂任务精度远低于监督方法。

### 4.5 Spiking Transformer — 2022 年以来的突破方向

#### 先回顾：Transformer 的自注意力在做什么

如果你了解 Transformer，你知道自注意力的核心是 **Q/K/V**（Query、Key、Value）：

```text
输入序列 X（比如一张图片切成 196 个 patch）
    │
    ├── 线性变换 → Q（"我在找什么"）
    ├── 线性变换 → K（"我能提供什么"）
    └── 线性变换 → V（"我的具体内容"）
```

$$
\text{注意力权重} = \mathrm{softmax}\!\left(\frac{Q K^\top}{\sqrt{d}}\right) \quad \text{← 每个 patch 对其他 patch 的关注度}
$$

$$
\text{输出} = \text{注意力权重} \times V \quad \text{← 加权汇总信息}
$$

关键点：**softmax 产生连续的注意力权重**（比如 0.03、0.15、0.42...），这些值在 0 到 1 之间且总和为 1。

#### 问题：softmax 为什么在 SNN 中不好用？

SNN 追求的是**稀疏性和离散性**——脉冲是 0 或 1，大量计算可以跳过。但 softmax 有两个特性与此冲突：

| 冲突 | 原因 |
|---|---|
| **输出永远是稠密的** | softmax 把所有值都变成正数（> 0），即使某个 patch 完全无关也会得到一个非零权重（比如 0.001），无法跳过 |
| **需要全局归一化** | softmax 的分母需要求所有 $e^{q_i k_j}$ 的和，这意味着必须等所有值算完才能出结果，无法逐步计算 |

#### Spiking Self-Attention (SSA) 怎么解决？

SSA 的核心思想：**把 Q、K、V 全部换成二值脉冲序列**，然后用脉冲的相似度替代 softmax。

**传统 Transformer：**

$$
Q, K, V \in \mathbb{R}^{n \times d} \text{（连续浮点数）}
$$

$$
\text{Attention} = \mathrm{softmax}\!\left(\frac{Q K^\top}{\sqrt{d}}\right) V \quad \text{← 稠密、需要 softmax}
$$

**Spiking Transformer (SSA)：**

$$
Q_{\text{spike}}, K_{\text{spike}}, V_{\text{spike}} \in \{0, 1\}^{T \times n \times d} \text{（0/1 脉冲序列，T 步累积）}
$$

$$
\text{Attention} = \left(Q_{\text{spike}} K_{\text{spike}}^\top\right) V_{\text{spike}} \quad \text{← 稀疏、无 softmax}
$$

具体地，Q 和 K 的点积变成了**脉冲序列的匹配计数**：两个神经元如果在相同时间步都发放了脉冲，就算一次匹配。匹配越多，注意力越强。这完全不需要 softmax，而且零匹配可以直接跳过。

#### 其他关键技术

- **Spiking Convolutional Stem**：用脉冲卷积替代 Transformer 的 patch embedding（把图片切成小块）。传统 patch embedding 直接把像素线性映射成特征，信息损失大；脉冲卷积保留了更多空间结构。
- **Self-Supervised Pre-training**：借鉴 BERT/MAE 的思路，随机遮挡 75% 的 patch，让模型学会从可见部分重建被遮挡部分，再在下游任务上微调。这大幅提高了大数据集上的训练效果。

#### ImageNet 准确率演进

| 年份 | 模型 | 准确率 | 关键技术突破 |
|---|---|---|---|
| 2023 | Spikformer V1 | 74.81% | 首次将 SSA 应用于 ImageNet |
| 2024 | Spikformer V2 | 80.38% → 81.10% | 改进脉冲卷积 Stem + 自监督预训练 |
| 2024 | Meta-SpikeFormer | 80.0% | 面向分类/检测/分割的 meta 架构 |
| 2024 | SGLFormer | 83.73% | 融合局部与全局脉冲注意力 |
| 2024 | **QKFormer** | **85.65%** | 直接训练 SNN 首破 85% |
| ANN 基准 | ViT-Base | ~91% | — |

> **精度突破不等于部署突破。** 这些结果不能与"ANN 约 91%"粗略相减后宣布仍差多少，因为参数量、输入分辨率、预训练、数据增强和训练预算不同；能耗仍主要是理论操作估算，不等于端侧神经形态芯片上的实测能效。

## 5. 硬件平台：神经形态芯片

### 5.1 横向对比总表

> **重要 caveat**：下表的"神经元数"和"TOPS/W"经常误导。不同平台的神经元状态位宽、模型复杂度、更新频率和时间复用不同；SOP 定义不同（有的统计突触读写，有的统计有效事件，有的报告峰值）；功耗边界不同（核动态、芯片、开发板或含传感器/主机的系统功耗）；工艺和位宽不同（28nm 4-bit 与 12nm 8-bit 的 TOPS/W 不能代表架构本身）。研究系统与产品不是同一维度。厂商"最高可达"若缺少完整 workload 和测量边界，只作为厂商声明，不参与跨平台排名。

| 芯片 | 年份 | 机构 | 制程 | 神经元数 | 功耗 | 能效 | 商用 | 类型 |
|---|---|---|---|---|---|---|---|---|
| **Loihi** | 2017 | Intel | 14nm | 131K | <1.5W | — | ❌ | 数字 |
| **Loihi 2** | 2021 | Intel | Intel 4 | ~1M | ~1W | ~104 GOPS/W | ❌ | 数字 |
| **Hala Point** | 2024 | Intel+Sandia | Intel 4 | **1.15B**（1,152 片 Loihi 2） | 最大 2,600W | 15 TOPS/W | ❌ | 系统（研究，非端侧） |
| **TrueNorth** | 2014 | IBM | 28nm | 1M（256M 突触） | **65mW** 实时运行 | — | ❌ | 数字 |
| **NorthPole** | 2023 | IBM | 12nm | N/A* | ~74W | **25.6 TOPS/W** | ❌ | 脑启发 ANN 推理* |
| **Akida 1000** | 2021 | BrainChip | 28nm | 可配置（20 核，0.7 TOPS） | **~30mW** | — | ✅ | 数字事件 |
| **Akida 2** | 2026 | BrainChip | TSMC 12nm | 可扩展 IP | — | — | ✅ | 数字事件 |
| **Speck** | 2021 | SynSense | 22nm | 128×128 DVS + 9 SCNN core（~320K） | **<1mW** | — | ✅ | 数字事件+DVS |
| **DYNAP-CNN** | 2020 | SynSense | 22nm | 1M | ~5mW | — | ✅ | 数字事件 |
| **Innatera T1/Pulsar** | 2024 | Innatera | 28nm | ~500（SNN fabric + RISC-V） | **<10mW**（厂商称毫瓦级） | — | ✅ | 混合信号 MCU |
| **SpiNNaker** | ~2010 | Manchester | 130nm | ~18K | ~1W | — | ❌ | 数字 |
| **SpiNNaker2** | ~2022 | Dresden | 22nm FD-SOI | 152K（每芯片 ~152 ARM core） | 2-5W | — | ❌ | 数字 many-core |
| **BrainScaleS-2** | ~2020 | Heidelberg | 65nm | 512（模拟 AdEx/LIF，131K 突触） | ~1W | — | ❌ | 模拟/混合（~1000× 生物实时） |
| **Tianjic** | 2019 | 清华 | 28nm | 40K（156 core，10M 突触） | ~1W | — | ❌ | 异构 ANN+SNN |
| **Darwin3** | 2024 | 浙大 | — | **2.35M**（支持压缩连接与新 ISA） | — | — | ❌ | 数字 |

\* NorthPole **不是 SNN 芯片**，是存算邻近的脑启发 ANN 推理加速器，其公开基准主要是 ResNet、YOLO、BERT 等 ANN。不应把神经形态、SNN、事件计算、脑启发 ANN 混成一个芯片榜单。

### 5.2 三个梯队

**第一梯队：商用产品**

- **BrainChip Akida**：数字事件域商用芯片/IP，已部署在汽车、工业、太空场景。AKD1000 为 28nm、20 个神经处理核、0.7 TOPS；Akida 2 为可扩展 IP。支持模型转换、少样本/片上学习。2025 年收入增长 374%，但年营收仅 ~US\$2M，功耗必须按具体板卡/模型实测。
- **SynSense Speck/DYNAP-CNN**：DVS + SNN 一体 SoC，<1mW 功耗（厂商公布指标，需注明具体 workload），适合 always-on 视觉 IoT。Sinabs/Samna 工具链紧密集成。
- **Innatera T1/Pulsar**：SNN fabric + RISC-V + 传感器接口的混合信号神经形态 MCU，<10mW（厂商称毫瓦级，公开第三方基准有限），定位"神经形态微控制器"，Talamo SDK。

**第二梯队：大规模研究系统**

- **Intel Hala Point**：1,152 片 Loihi 2，11.5 亿神经元，全球最大。部署于 Sandia 国家实验室，最大 2,600W，是研究系统而非端侧芯片。
- **浙大 Darwin3/悟空**：单片最高 2.35M 神经元，支持压缩连接与新 ISA。
- **SpiNNaker2 @ Sandia**：1.75 亿神经元，22nm FD-SOI，用于国防研究。

**第三梯队：研究平台**

- **IBM TrueNorth**（历史里程碑，已被超越；离线配置，无通用片上学习）
- **BrainScaleS-2**：唯一模拟晶圆级系统，1000× 加速仿真，PPU 支持可编程可塑性
- **Tianjic**：异构融合先驱（ANN/SNN 统一功能核）

### 5.3 关键瓶颈

1. **软件生态碎片化**：每个芯片有自己的 SDK，没有统一编程模型（NIR 正在尝试成为类似 ONNX 的中间表示，但后端完全等价仍做不到）
2. **On-chip learning 极为有限**：几乎所有芯片的片上学习都受限
3. **benchmark 不统一**：TOPS/W vs GOPS/W vs "比 CPU 低 90%"，无法横向比较；NeuroBench 正在建立共同指标
4. **精度与能效的矛盾**：模拟芯片受噪声限制；数字芯片需量化换能效
5. **映射与通信才是硬件真正难的地方**：部署一个 SNN，编译器需要同时满足每核 neuron state/权重/突触表容量、fan-in/fan-out 与路由表限制、卷积权重复用或稀疏连接压缩格式、片间事件流量与拥塞、定点阈值/泄漏/延迟与累积溢出、输入/输出事件与主机 DMA 的批次和时间戳语义。如果网络数学上很稀疏但映射后大量跨核 fan-out、路由表膨胀或状态落到外部存储，能效可能反而下降。

> **不要把 4.6 pJ/MAC 与 0.9 pJ/AC 当成芯片实测。** 这组数来自 2014 年 ISSCC 对 45nm 工艺中浮点乘与加的粗略能耗量级估算，不含模型访存、膜电位状态、控制、索引、事件路由、片外 I/O 和静态功耗。它适合做同架构的计算上限估算，不适合与真实 MCU/NPU/神经形态芯片的板级焦耳数直接比较。2026 年的一项重新评估也指出，忽略数据搬运和内存访问会高估 SNN 相对量化 ANN 的能效。

## 6. 当前使用场景

### 6.1 选择场景的六个问题

一个场景同时满足越多条件，SNN 价值越大：

1. 输入是否天然是事件或连续时间序列？
2. 环境是否大部分时间无有效事件？
3. 是否必须 always-on，且平均功耗比峰值算力更重要？
4. 是否强调单样本低尾延迟，而不是大 batch 吞吐？
5. 是否需要设备端持续适应或小样本个性化？
6. 现有 MCU/DSP/NPU 的量化 ANN 是否仍不能满足能耗预算？

### 6.2 最适合 SNN 的场景

| 场景 | 时间/事件天然性 | 空闲稀疏 | 功耗刚需 | 当前 PoC 成熟度 | 综合判断 |
|---|---|---|---|---|---|
| 关键词唤醒 / 声音事件检测 | 5 | 4 | 5 | 4 | **第一优先级**；必须与 DS-CNN/流式 KWS 实测 |
| 工业振动 / 电流异常检测 | 5 | 4 | 4 | 4 | **第一优先级**；数据较易采集，业务价值清楚 |
| 毫米波雷达存在 / 手势 | 5 | 4 | 5 | 3 | **高优先级**；雷达前端与编码决定成败 |
| IMU/EMG/ECG/EEG 可穿戴健康 | 5 | 3 | 5 | 3 | **高优先级**；注意连续高活动下的 spike rate |
| 事件相机手势 / 高速目标 | 5 | 5 | 4 | 3 | **高匹配**；需要传感器、数据和整链路集成 |
| AR/VR 眼动与动作触发 | 4 | 3 | 5 | 2 | 潜力高；精度、用户差异和传感器成本是风险 |

评分：5 为非常匹配，1 为不匹配。成熟度指"能做出工程 PoC"，不是规模营收。

### 6.3 不适合 SNN 的场景

| 场景 | 时间/事件天然性 | 空闲稀疏 | 功耗刚需 | 当前 PoC 成熟度 | 综合判断 |
|---|---|---|---|---|---|
| 普通帧相机静态分类 | 2 | 2 | 3 | 4 | 通常量化 CNN/NPU 更实际 |
| 计算摄影主链路 | 2 | 1 | 3 | 1 | 不建议作为首个 SNN 项目；可研究事件相机旁路 |
| 端侧 LLM | 1 | 1 | 5 | 1 | **近期不建议**；量化、稀疏 ANN、线性注意力优先 |
| 数据中心批推理 | 1 | 1 | 3 | 2 | SNN 的 batch 劣势明显；仅特殊稀疏问题值得研究 |

### 6.4 三类最现实产品架构

**架构 A：SNN 作为 always-on 唤醒器**

```text
低功耗传感器 → SNN 唤醒器 → 无事件则继续待机
                          → 置信度越阈 → DSP/NPU 主模型 → 业务结果
```

SNN 不承担完整识别，只负责把高功耗主链路的占空比降下来。这通常比把整个业务模型全部脉冲化更容易形成整机收益。

**架构 B：原生事件传感器 + SNN**

事件相机直接输出亮度变化事件，避免固定帧采样。IBM 的 DVS Gesture 系统曾在 TrueNorth 上实现 96.5% 准确率、105 ms 延迟且处理芯片功耗低于 200 mW，是端到端事件感知的经典例子；该结果来自 2017 年特定硬件和数据集，只能说明路线可行，不能当作今天所有 DVS 任务的通用指标。

**架构 C：混合 ANN-SNN**

- ANN/卷积前端处理高带宽、局部密集特征
- SNN/RSNN 处理长时间依赖、事件触发与状态
- ANN 读出输出分类/回归

这种结构可能牺牲一部分纯事件驱动，但能显著降低模型迁移风险。它也更符合 Akida、Tianjic、SpiNNaker2 等混合能力的现实。

### 6.5 判断标准

如果面临以下情况，SNN 值得考虑：

| 问题 | 如果答案是"是" |
|---|---|
| 输入是事件流/时间序列/传感器连续流？ | SNN 适合 |
| 有 always-on、毫瓦级或电池寿命硬约束？ | SNN 适合 |
| 需要低延迟闭环反应，而不是高吞吐 batch？ | SNN 适合 |
| 能通过传统 CNN/NPU 已经低成本解决？ | SNN 价值下降 |

## 7. 产业生态

### 7.1 融资概览

| 公司 | 累计融资 | 估值/市值 | 年营收 | 阶段 |
|---|---|---|---|---|
| **Unconventional AI** | \$475M（种子轮!） | **\$4.5B** | 0 | 种子 2025.12（但公司目标是更广义的 biology-scale/新计算 substrate，融资事实可查，不等于 SNN 市场验证拐点） |
| **BrainChip** | ~\$25M + 公开市场 | ~A\$364M 市值 | ~US\$2M/年 | 上市 |
| **Prophesee** | €127M | — | — | 破产重组 |
| **SynSense** | ~\$87M | ~\$300M | — | 产品化 |
| **Innatera** | ~\$43M | — | — | Series A |
| **SpiNNcloud** | ~€14M | — | — | EIC 支持 |
| **nextSilicon** | ~\$303M | ~\$1.5B | — | Series C |

> 融资与专利数量不能证明技术可落地，因此不作为路线判断的核心证据。

### 7.2 专利布局

> **需限定**：公开可查的"2025 年专利增长 401%（239 件）/ Qualcomm 约 450 件 SNN 专利"等说法缺少检索式、专利族去重、法域和"严格 SNN"定义，**未充分验证**，不应直接沿用为产业判断核心证据。下表仅作参考性方向信号。

| 指标 | 数值（参考性，未独立验证） |
|---|---|
| 累计（截至 2026 年初） | ~596 件（自称） |
| 2025 年专利增长 | ~401%（239 件，自称） |
| Qualcomm | ~450 件 SNN 专利（自称，领先） |
| 清华大学 | 68 件 |
| 北京大学 | 35 件 |
| BrainChip | 18+ 件已授权 + ~30 件待审 |
| Prophesee | 50+ 件 |

### 7.3 开源社区

| 项目 | Stars | 状态 | 说明 |
|---|---|---|---|
| **SpikingJelly** | 2,100 | ✅ 活跃 | PyTorch 原生，中文资料较多；支持 torch/CuPy/Triton 后端 |
| **snnTorch** | 2,000 | ✅ 活跃 | 最佳教程，API 简洁、教学和研究复现好 |
| **BindsNET** | 1,700 | ✅ 活跃 | STDP 无监督学习 |
| **Brian2** | 1,200 | ✅ 活跃 | 计算神经科学 |
| **Intel Lava** | 735 | ❌ **2026-05-13 已归档** | 历史 Loihi 能力完整；新 SDK 尚在过渡，不宜新增长期依赖 |
| **Norse** | 809 | ✅ 活跃 | PyTorch 神经动力学模块 |
| **Sinabs/Samna** | 117 | ✅ 活跃 | SynSense 硬件专用 |
| **NEST** | 651 | ✅ 活跃 | 大规模仿真 |
| **NIR** | — | ✅ 标准化中 | 跨框架/芯片中间表示；论文演示 11 个平台，官网称 12+，文档列 9 个模拟器与 5 个硬件后端 |
| **NeuroBench** | — | ✅ 形成中 | 算法与系统评测，v1.0 含事件相机目标检测、持续少样本关键词学习等 |

### 7.4 开发者生态

- Open Neuromorphic Discord：**2,700 人**（仍很小）
- 大学课程：Stanford / MIT / UCSC
- 旗舰会议：ICONS / NICE
- 中国领先研究机构：清华（施路平、张悠慧）、北大（赵非凡）、复旦（郑骁庆、吕昌泽）

## 8. 各大公司的态度

| 类型 | 公司/机构 | 态度 |
|---|---|---|
| 强投入研究平台 | **Intel** | 最连续的大型芯片公司投入。Loihi → Loihi 2 → Hala Point。但 Lava 框架已于 2026-05-13 归档，下一代 Loihi 与新 SDK 将转向开放标准 AI 框架。 |
| 早期先锋，转向脑启发推理 | **IBM** | TrueNorth 是里程碑；NorthPole 更偏 ANN 推理（非 SNN），不再强调纯 SNN。 |
| 早期 SNN 探索，转向端侧 DL | **Qualcomm** | Zeroth 早期明确用 SNN，后续转向 Hexagon NPU。自称持有最多 SNN 专利（~450 件，未独立验证）。 |
| 长线研究 | **Samsung** | 2021 "copy and paste the brain" 愿景。投资了 SynSense。 |
| 事件传感器商业化 | **Sony + Prophesee** | 积极推动 event-based vision。Prophesee 破产后转型国防。 |
| 专用边缘 SNN 商用 | **BrainChip / SynSense / Innatera** | 最积极的产品化阵营。 |
| 软件平台探索 | **Kaspersky** | 开源 KNP 平台。 |
| 主流 AI 算力 | **NVIDIA / Google / Apple / Tesla** | 公开主线是 GPU/TPU/NPU/Transformer，不是 SNN。 |

### 8.1 2026-07 三家 SNN 芯片公司实查动态

WebFetch 各家官网/投资者页（2026-07-15）确认的近期事实：

- **BrainChip** | AKD1500 神经形态处理器宣布商用量产发货；Akida 2 IP 授权给 EDGEAI 做智能电表；AkidaTag 可穿戴参考平台发布；签 ASICLAND/ForwardEdge ASIC/MicroIP/Klepsydra/MDS Intelligence 等生态伙伴 | 2026-03~06 | https://investor.brainchip.com/
- **SynSense** | 发布下一代神经形态视觉芯片 Aeveon™，并据新闻页 slug 关联一轮战略融资以加速高速 3D 神经形态处理器 DYNAP™-CNN2 开发 | 2026-06-24 | https://www.synsense.ai/news/
- **SynSense** | 推出 BridgeMonitoring 基础设施智能方案，同期开放神经形态开发者社区论坛与开发套件 datasheet 访问 | 2026-05-21 | https://www.synsense.ai/news/
- **Innatera** | 在 CES 2026 展示真实场景神经形态边缘 AI；Pulsar（首款面向传感器边缘的大众市场神经形态 MCU，含 SNN 加速+RISC-V+CNN 加速）已发布 | 2026-01(CES) | https://innatera.com/
- **Innatera** | 签 Joya 为 ODM 客户、与 42T 联合推动智能产品创新、VLSI EXPERT 采用其 SNN 处理器建人才池（具体日期官方页未标，据 innatera.com 首页新闻条目） | 2026（日期未标） | https://innatera.com/

## 9. SNN 对移动旗舰 SoC 的参考

### 9.1 移动旗舰 SoC 当前 AI 架构现状

**优势：**

- 成熟的 NPU 软件栈，开发者生态相对完善
- 已支持端侧大模型
- 与移动操作系统深度集成，系统级 AI 调度
- 支持低功耗计算与模型演进

**痛点：**

- Always-on 场景（语音唤醒、手势、存在检测）的功耗，尤其在 AIOS 时代需要常驻
- 静态 NPU 架构无法动态适应稀疏、事件驱动的输入

### 9.2 哪些移动旗舰 SoC 场景可能从 SNN 受益

| 场景 | 当前实现 | SNN 潜在收益 | 可行性 |
|---|---|---|---|
| **语音唤醒** | 低功耗 DSP + 小模型 | SNN 可进一步降低功耗到 μA 级（需端到端实测，非通用保证），事件驱动只在有声音时计算 | ⭐⭐⭐⭐ 高 |
| **手势识别** | 摄像头 + NPU 推理 | 事件相机 + SNN 可实现 <1mW 持续感知 | ⭐⭐⭐ 中（需事件传感器） |
| **存在检测** | SensorHub | SNN 适合处理 IMU/雷达的稀疏时序信号 | ⭐⭐⭐⭐ 高 |
| **计算摄影** | ISP + NPU | SNN 对事件驱动的动态场景（快速运动、HDR）有优势 | ⭐⭐ 中低（需重新设计 pipeline） |
| **端侧 LLM** | NPU INT8/INT4 推理 | SNN 理论上能效更高，但当前仍是探索而非近期端侧路线 | ⭐ 低（短期不现实） |
| **生物识别** | NPU + 安全芯片 | SNN 可用于低功耗指纹/面部持续认证 | ⭐⭐⭐ 中 |

### 9.3 技术可行性评估

**如果移动旗舰 SoC 要集成 SNN，有三条路线：**

**路线 A：专用 SNN 协处理器（独立 always-on island）**

- 在 SoC 中增加一个小规模的 SNN 加速器，放在低压域，保持局部状态
- 规模：1K-100K 神经元，功耗预算毫瓦级（具体需端到端实测，非通用保证）
- 用于：语音唤醒、手势、存在检测等 always-on 任务
- 优点：不影响主 NPU 架构，风险可控；即便 SNN 路线不扩展到大模型，该 island 仍可作为稀疏时序/触发加速器使用
- 缺点：需要额外的硅面积和设计成本

**路线 B：扩展现有 NPU 支持 SNN 模式**

- 在 NPU 架构中增加事件驱动执行模式
- 通过软件配置切换 ANN/SNN 模式
- 优点：复用现有硬件，开发成本低
- 缺点：主 NPU 的阵列、DMA 和调度围绕稠密 tensor 设计，细粒度异步事件会降低利用率；always-on 功耗预算与主 NPU 峰值算力目标冲突；能效优势有限，工程风险很高

**路线 C：授权商用 SNN IP**

- 集成 BrainChip Akida 或 Innatera SNN IP
- 优点：快速获得成熟方案，软件栈已验证
- 缺点：依赖外部 IP，与自研路线冲突

**推荐路线：A**（专用 SNN 协处理器 / 独立 always-on island），原因：

1. 风险最低，不影响现有 NPU 架构
2. 硅面积可控（具体面积由工艺、SRAM、路由、接口和容量决定，未给设计点不能下定论）
3. 可快速验证 SNN 在移动场景的价值
4. 独立岛可放在低压域，保持局部状态并在命中时唤醒主 NPU
5. 业务范围可限制为音频/IMU/雷达等，算子和编译器问题可控
6. 如果验证成功，再考虑扩展到主 NPU

### 9.4 软件生态挑战

**集成 SNN 的主要瓶颈不是硬件，而是软件：**

| 挑战 | 现状 | 需要做的 |
|---|---|---|
| **训练工具** | snnTorch / SpikingJelly 可用，但成熟度不如 PyTorch | 适配端侧 AI 框架，提供 SNN 训练 API |
| **模型转换** | ANN-to-SNN 转换工具有，但精度损失大；不是简单"把 ReLU 换成 LIF" | 开发专用的优化转换流程（校准阈值、折叠 BN、补偿残余膜电位、转换后微调） |
| **部署工具** | 各 SNN 芯片 SDK 碎片化；NIR 解决共同图和动力学表示，不自动解决算子不支持、定点等价性、功耗最优分区映射 | 在 NPU 软件栈中增加 SNN 运行时支持；考虑兼容 NIR 而非从零造格式 |
| **开发者生态** | SNN 开发者社区极小（~2,700 人）；Lava 已归档是现实案例 | 需要投入教育成本，培养开发者；版本冻结、源码归档、抽象 HAL、双硬件 PoC |
| **Benchmark** | 缺乏统一的能效/精度对比标准；NeuroBench 仍在成长 | 建立评测体系；与 MLPerf Tiny 同功耗级 MCU/NPU 基线组合比较 |

### 9.5 风险与机会

**风险：**

1. **软件生态不成熟**：Intel Lava 已归档，SNN 框架碎片化，自建生态成本极高
2. **精度差距（需正确比较）**：不能简单相减称"差 7-10%"，但端侧 LLM 场景短期无法用 SNN，量化 ANN 仍优先
3. **市场验证不足**：BrainChip 年营收仅 ~\$2M，说明 SNN 市场规模仍很小；融资事实不等于 SNN 商业拐点
4. **技术债务**：如果 SNN 路线失败，投入的硬件设计成本无法回收
5. **"伪能效"陷阱**：用 45nm 理论 MAC/AC 数推断 7/12/22/28nm 实际板级能耗；ANN 用 FP32、SNN 用 1-4bit 却把收益全归 spike；只统计有效 SOP 不统计膜电位更新、路由、索引和内存——这些都会高估 SNN 相对量化 ANN 的能效

**不应写进立项材料的未经验证承诺：**

- "SNN 固定比 ANN 省 10-100 倍"（某些任务/硬件有数量级结果，但没有跨任务通用保证）
- "协处理器一定小于 1 mm²"（面积主要由工艺、SRAM、路由、接口和容量决定）
- "语音唤醒一定能做到 μA 级"（必须端到端实测）
- "现有 NPU 加一个事件模式就能复用全部能力"（容易两边都不高效）
- "NIR 已经解决跨芯片部署"
- "脉冲 LLM 已证明端侧可用"

**机会：**

1. **差异化竞争力**：如果在旗舰 SoC 中率先集成高效 SNN，在 AIOS 时代常驻业务会更有优势
2. **功耗优势（需端到端可复现）**：always-on 场景功耗可能降低数量级，对续航有显著提升——前提是连续工作负载下获得可复现的优势（建议门槛：含传感器后处理或至少含完整 AI 子系统，J/hour 或 J/event 降低 ≥5×，p95 延迟不劣化）
3. **生态布局**：提前布局 SNN，为未来事件传感器（事件相机、神经形态麦克风）做准备
4. **学术合作**：中国高校（清华、北大、复旦）在 SNN 领域领先，可联合研发

**最终判断：**

- SNN 对移动旗舰 SoC **有价值，但不是优先级最高的方向**
- 当前核心竞争力仍在 NPU + 端侧大模型，应继续优化这条主线
- SNN 更适合作为**长期技术储备**和**差异化特性**，而非短期产品卖点
- 如果决策投资，**先做系统级 PoC**（12 周、双任务、双基线、可复现门槛），**从小规模协处理器开始**，验证价值后再扩展
- 主 NPU 仍应围绕量化、稀疏 tensor、存算邻近和端侧大模型优化，SNN 不应分散主线资源

## 10. 近期 SNN 论文

arXiv Atom API 扫 2026-04-15~2026-07-15（近 3 个月）窗口，按收紧口径（摘要含 `spiking neural network` / `spikformer` / `spiking transformer` / `spiking neuron model` / `\bsnn\b`，不靠 `neuromorphic` 单独判定）筛得 129 篇真 SNN；下面精选 20 篇（优先顶会/高相关/方向多样性：硬件加速、Spikformer、剪枝量化、医疗、语音、汽车、安全、理论），并入本周 run 里 `方向:SNN` 标签的 6 篇（标 ★，其中 2607.12862 摘要未直含 SNN 关键词但被 run 分类器判为 SNN 方向，按任务要求并入）。窗口内无顶会正式 proceedings，以 arXiv preprint 为准。

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

## 11. SNN 框架对比表

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

> 注：snnTorch 实际仓在 `jeshraghian/snntorch`（非 `snf-lab/snnTorch`，后者 404）；Lava 实际仓在 `lava-nc/lava`（非 `intel/neuromorphic`，后者 404）。stars/活跃度为 2026-07-15 GitHub API 实查值，会随时间变化。
