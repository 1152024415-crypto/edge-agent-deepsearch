---
id: agentcpm-gui-20250617
slug: agentcpm-gui-mobile-agent-rft
title: "AgentCPM-GUI：基于 MiniCPM-V 的端侧移动 GUI Agent（强化微调）"
authors: ["Zhong Zhang et al.", "OpenBMB", "面壁智能", "清华大学"]
affiliations: ["ModelBest"]
source_type: 学术论文
date: 2025-06-17
url: https://arxiv.org/abs/2506.01391
branches: ["感知、记忆与规划", "核心概念与系统架构"]
vendors: ["ModelBest"]
score: 85
score_relevance: 35
score_vendor: 25
score_contribution: 15
score_quality: 10
score_recency: 0
recommendation: 纳入
review_hint: "CAGUI 准确率是否复现"
insight_person: Codex
wiki_url: https://github.com/1152024415-crypto/edge-agent-deepsearch/wiki/agentcpm-gui-mobile-agent-rft
---

OpenBMB / 面壁智能 / 清华大学联合发布 AgentCPM-GUI，8B 端侧 GUI agent，基于 MiniCPM-V，面向中英文移动应用自动化。

## 工作原理
三阶段训练：Stage I 视觉感知与 grounding（OCR / 控件定位）→ Stage II 监督模仿学习（人类动作轨迹 SFT）→ Stage III 强化微调（GRPO 提升推理）。引入紧凑动作空间，平均每命令 9.7 token，支持端侧低延迟执行。

## 实际效果
- CAGUI 中文基准：96.9% Type-Match, 91.3% Exact-Match
- 模型：8B（基于 MiniCPM-V）
- 开源：代码 / 权重 / 评测数据全公开

## 创新贡献
提出 reinforcement fine-tuning（GRPO）用于 GUI agent，构建 CAGUI 中文 GUI 基准，补齐中文移动生态评测空白。
