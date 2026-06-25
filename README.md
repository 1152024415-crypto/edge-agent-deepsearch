# edge_agent — 端侧 AI Agent 周报雷达

> runtime agent 每周搜集端侧 agent / 推理最新动态（过去一周、大厂优先），本地 build，push 成品到 GitHub 纯展示。
> 架构与工作流见 [AGENTS.md](AGENTS.md) / [ARCHITECTURE.md](ARCHITECTURE.md)；需求规格以 [docs/product-specs/SPEC.md](docs/product-specs/SPEC.md) 为准。

---

# 搜集提示词（agent 运行时执行）

> 以下为 runtime agent 每次搜集执行用的提示词。与 `docs/product-specs/SPEC.md` 同步，**修改以 SPEC.md 为准**。

## 〇、时间窗口与运行模式
- 窗口：**过去一周**（每次运行读 `data/.last_run` 计算 cutoff，滚动；`never` 则首次用 `now-7d`）
- 模式：高频滚动雷达，每周扫描最新动态
- 增量：仅处理窗口内新增、且未在 `data/index.json` 收录的条目（去重属 harness 层）

## 一、信息源（四类，缺一则雷达跑空）
1. **学术论文**：arXiv + 顶会顶刊（NeurIPS / ICML / ICLR / MobiSys / SenSys / ASPLOS / CVPR / ACL / TPAMI / TNNLS）
2. **厂商技术博客**：Apple ML、Google Research、Meta AI、Microsoft、高通 / 联发科官方、华为 / 小米 / OPPO / vivo / 荣耀技术博客
3. **GitHub releases / 公告**：MNN、MLC-LLM、MediaPipe LLM、llama.cpp、ONNX Runtime、各厂端侧框架
4. **产品 / 大会发布**：WWDC、Google I/O、Snapdragon Summit、各厂开发者大会

## 二、检索式
**基础**：`("mobile agent" OR "edge agent" OR "embedded agent" OR "agentic AI" OR "agentification") AND ("on-device" OR "edge computing" OR "resource-constrained")`

**技术深化**：`("LLM" OR "VLM" OR "foundation model") AND ("mobile" OR "edge") AND ("quantization" OR "pruning" OR "distillation" OR "efficient inference") AND ("agent" OR "autonomous")`

**厂商特定**：`("Apple Intelligence" OR "CoreAI" OR "Samsung Gauss" OR "Gemini Nano" OR "Phi-3" OR "Llama 3.2" OR "MiniCPM" OR "Qwen2.5") AND ("on-device" OR "edge" OR "mobile" OR "embedded") AND ("agent" OR "optimization" OR "deployment")`

**评测基准**：`("AndroidWorld" OR "Mobile-Env" OR "AIoTBench" OR "MLPerf Tiny") AND ("agent" OR "GUI automation")`

**厂商动态**（博客 / GitHub / 发布，非布尔，按厂商官方渠道 + 关键词：on-device / edge / agent / 端侧 / 智能体 / 推理 / 部署，限过去一周）

## 三、任务目标
构建端侧 AI Agent **周度动态候选集**，主题聚焦面向移动 / 嵌入式设备的端侧 AI Agent（端侧 agent 优先，端侧推理引擎次之纳入）。由 runtime agent 深度语义评估。

核心研究问题：
1. 当周端侧 Agent 核心系统架构与认知框架进展？
2. 支撑端侧 Agent 在资源受限设备运行的使能技术（量化 / KVcache / 投机解码 / 感知记忆 / 规划）进展？
3. 主要设备厂商与模型厂商当周的技术布局、架构演进、发布动态？
4. 学术界与工业界当周热点、效果与方向？

## 四、纳入 / 排除标准
**硬门槛（gate，不满足直接排除）**：
- 时间：发布 / 发表日期在过去一周内
- 主题：涉及端侧 / 边缘设备 且（agent 或 推理优化）至少其一

**纳入倾向**（由评分体现，非硬性）：
- 端侧 agent 系统设计 / 优化 / 评估
- 关键技术分支覆盖（见第五节）
- 部署环境明确（手机 / IoT / 嵌入式 / 车载 / 无人机等资源受限节点）
- 大厂出品或与大厂架构关联（优先级更高，见评分）

**排除**：
- 纯云端 Agent，无端侧部署 / 优化考量
- 无 Agent 技术且无端侧推理优化（如纯联邦学习 / 通用边缘计算）
- Short / Demo 论文或纯商业宣传无技术创新
- 非主流渠道且无实质技术贡献
- （不分语言；英文为质量软信号，不硬排除中文）

## 五、关键技术分支与关键词矩阵

### 1. 核心概念与系统架构
- **Agentic AI / Agentification**：边缘通用智能、自主感知-推理-行动闭环
- **Mobile / Embedded AI Agents**：手机 GUI 智能体、MCU 物理智能体（Embodied Agent）
- **Cognitive Edge Computing**：认知推理 + 边缘计算
- **Multi-Agent Collaboration (on Edge)**：边缘多智能体协作、分布式调度（如 6G）

### 2. 模型轻量化与基础模型优化
- **Elastic Inference**：运行时资源波动的动态结构重组（动态深度 / 宽度、早期退出）
- **Quantization**：GPTQ / AWQ / SmoothQuant / KV Cache Quantization
- **Pruning & Sparsity**：SparseGPT / Wanda / N:M Sparsity
- **Knowledge Distillation**：EdgeSAM / MobileCLIP 等
- **Efficient Attention & Decoding**：FlashAttention / PagedAttention / Speculative Decoding（Medusa / EAGLE）

### 3. 运行时自适应与资源效率
- **Test-time Adaptation**：在线 Prompt 学习、PEFT / LoRA、记忆增强（解决数据漂移）
- **Dynamic Multimodal Integration**：异步传感器自适应路由、动态注意力、Token 压缩（如 LLaVA-Mini）
- **Energy-aware Computing**：电池 / 热功耗感知的动态负载调度
- **On-device / Edge-Cloud Collaborative Inference**：端云协同、弹性卸载（Elastic Offloading）

### 4. 感知、记忆与规划
- **Multimodal Perception**：VLM 端侧部署、GUI 理解、屏幕解析（Screen Parsing）
- **Memory Mechanisms**：向量数据库轻量化、上下文压缩、KV Cache 管理
- **Planning & Reasoning**：任务分解、CoT、工具调用（Tool Use / Function Calling）端侧执行框架

### 5. 评估、基准与硬件
- **Benchmarks**：AndroidWorld / Mobile-Env / AIoTBench / MLPerf Tiny
- **Hardware-Aware Compilation**：NPU / DSP / GPU 感知编译（MLC-LLM / llama.cpp / ONNX Runtime）

### 6. 主要厂商技术与架构
- **设备厂商**：Apple（Apple Intelligence / CoreAI / AX NPU）、Samsung（Gauss / Galaxy AI / Exynos）、Huawei（HarmonyOS AI / Pangu / HiAI / Ascend）、Qualcomm（AI Hub / Hexagon NPU）、MediaTek（NeuroPilot / APU）、小米（HyperAI / MiLM / AISP / 澎湃OS）、OPPO（AndesGPT / ColorOS AI）、vivo（BlueLM / BlueOS / 蓝心小V）、荣耀（MagicOS AI / YOYO / MagicRing）
- **模型厂商**：Google（Gemini Nano / MediaPipe / AICore）、Microsoft（Phi-3/4 / Copilot Runtime / DirectML）、OpenAI（轻量化 / Function Calling for Mobile）、Anthropic（Haiku 边缘适用）、Meta（Llama 3.2 1B/3B / Scout）、Mistral（Ministral 3B/8B）、面壁智能（MiniCPM 系列）、Qwen（Qwen2.5 0.5B-7B / Mobile-Agent）

## 六、评分体系（多维加权，满分 100；纳入由 runtime 裁量）

硬门槛见第四节，不满足不评分。

| 维度 | 权重 | 满分档 | 中档 | 低档 |
|---|---|---|---|---|
| 主题契合度 | 35% | 端侧 agent 系统/算法/优化=35 | 端侧推理引擎优化(非 agent)=22 | 端云协同/边缘通用=15；仅边缘涉及=5 |
| 大厂关联度 | 25% | 作者 affiliation 含大厂/模型厂=25 | 与大厂架构直接对比/优化/适配=18 | 学术机构无大厂关联=8；纯学生无机构=3 |
| 技术贡献度 | 20% | 新架构/方法/基准=20 | 现有技术系统优化=14 | 调研/综述/经验=10；无实质贡献=3 |
| 信息质量 | 15% | 顶会顶刊=15 | 高质量预印本=12 | 厂商技术博客(有细节)=10；产品发布(细节少)=5 |
| 时效新鲜度 | 5% | 24h 内=5 | 2-3 天=4 | 4-7 天=3 |

- **大厂白名单**（affiliation）：设备厂 Apple / Samsung / Huawei / Qualcomm / MediaTek / 小米 / OPPO / vivo / 荣耀；模型厂 Google / Microsoft / OpenAI / Anthropic / Meta / Mistral / 面壁 / Qwen（详见 `docs/references/vendor-whitelist.md`）
- 英文为信息质量软信号（同等优先），不单独扣中文分
- **纳入判定**：综合得分由 runtime agent 依据本体系裁量（高分自动纳入、中分纳入待复审、低分排除；阈值非硬编码，runtime 综合判断）

## 七、深度语义分析（每条入库时 runtime 回答）
1. **核心对齐度**：是否针对端侧 / 边缘提出新 agent 系统或推理优化？
2. **技术分支归属**：属第五节哪一 / 多个分支？
3. **大厂生态关联**：与哪类大厂架构关联 / 对比 / 优化？（驱动大厂关联度评分）
4. **创新贡献**：新架构 / 算法 / 基准 / 系统分析？
5. **实际效果**：推理速度 / 模型大小 / 准确率 / 能耗（**必须来自原文，摘不到写"未报告"，禁止补编**）
6. **工作原理**：核心机制 2-3 句
7. **趋势意义**：对端侧 agent 落地的潜在影响

## 八、输出格式（runtime 产出内容字段；frontmatter 映射 / 洞察人 / wiki 链接由 harness 层处理）

```markdown
### 条目分析
| 字段 | 内容 |
|---|---|
| 标题 | |
| 作者与机构 | |
| 来源类型 | 学术论文 / 厂商博客 / GitHub / 产品发布 |
| 日期 | YYYY-MM-DD |
| 链接 | URL |
| 摘要原文 | |
| 技术分支 | 分支1 > 分支2 |
| 大厂关联 | 厂商 / 架构 - 说明 |
| 工作原理 | 2-3 句 |
| 实际效果 | 关键数据（未报告则注明） |
| 创新贡献 | |
| 综合评分 | X/100 + 各维度分 |
| 推荐意见 | 纳入 / 纳入待复审 / 排除 |
| 关注建议 | 人工复审重点方向 |
```
