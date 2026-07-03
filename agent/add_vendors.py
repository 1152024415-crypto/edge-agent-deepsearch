#!/usr/bin/env python3
"""Append 11 vendor official-dynamics (官方动态) to the run JSON."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VENDORS = [
    {"id":"vendor-microsoft-local-routing-2026","title":"本地优先与全链路追踪：Ollama / Foundry Local ↔ Microsoft Foundry 路由",
     "abstract":"在本地模型(Ollama、Foundry Local)和云端 Foundry 之间路由 AI agent 工作负载，支持全链路追踪。",
     "effects":"未报告","paper_url":"https://techcommunity.microsoft.com/blog/educatordeveloperblog/local-first-and-fully-traced-routing-between-ollama-foundry-local-and-microsoft-/4529694",
     "date":"2026-06-26","score":12,"score_relevance":7,"score_contribution":5,
     "score_reason":"大厂应用真实技术：本地↔云 agent 路由实现（affiliation 待核实）",
     "source_tier":"官方动态","open_source":False,"tags":["方向:端侧agent","方向:端云协同"],
     "authors":"Microsoft","vendors":"Microsoft","venue":"Microsoft Tech Community"},
    {"id":"vendor-qualcomm-hf-device-cloud-2026","title":"Qualcomm 与 Hugging Face 深化合作：device-to-cloud 开放 AI",
     "abstract":"Qualcomm 与 Hugging Face 扩大合作，把开放、开发者驱动的 AI 覆盖 device-to-cloud，指向端侧/边缘部署。",
     "effects":"未报告","paper_url":"https://www.qualcomm.com/news/releases/2026/06/qualcomm-and-hugging-face-expand-relationship-to-advance-open-developer-driven-ai",
     "date":"2026-06-24","score":11,"score_relevance":7,"score_contribution":4,
     "score_reason":"官方动态，device-to-cloud 含端侧部署角度","source_tier":"官方动态","open_source":False,
     "tags":["方向:端侧agent","方向:端云协同","方向:编译部署"],"authors":"Qualcomm","vendors":"Qualcomm","venue":"Qualcomm News"},
    {"id":"vendor-mediatek-genio-pro-5100-2026","title":"MediaTek Genio Pro 5100：边缘实时视觉智能",
     "abstract":"Genio Pro 5100 IoT 平台为实时边缘 AI 视觉与自主决策提供高性能算力。",
     "effects":"未报告","paper_url":"https://www.mediatek.com/tek-talk-blogs/mediatek-genio-pro-5100-powering-real-time-vision-intelligence-at-the-edge",
     "date":"2026-06-25","score":11,"score_relevance":7,"score_contribution":4,
     "score_reason":"边缘 IoT AI 平台官方发布","source_tier":"官方动态","open_source":False,
     "tags":["方向:端侧agent","硬件:NPU"],"authors":"MediaTek","vendors":"MediaTek","venue":"MediaTek Tek Talk"},
    {"id":"vendor-mediatek-dgx-spark-2026","title":"在 DGX Spark 上本地运行 AI Agent",
     "abstract":"联发科介绍在 NVIDIA DGX Spark 上本地运行 agentic AI 工作负载，重计算留本地按需连云。",
     "effects":"未报告","paper_url":"https://www.mediatek.com/tek-talk-blogs/running-ai-agents-locally-on-dgx-spark",
     "date":"2026-06-24","score":12,"score_relevance":8,"score_contribution":4,
     "score_reason":"明确本地运行 agent","source_tier":"官方动态","open_source":False,
     "tags":["方向:端侧agent","方向:端云协同","硬件:DGX"],"authors":"MediaTek","vendors":"MediaTek","venue":"MediaTek Tek Talk"},
    {"id":"vendor-nvidia-nemotron-nvfp4-2026","title":"用 NVIDIA 模型优化器创建 Nemotron 3 Ultra NVFP4 检查点",
     "abstract":"用模型优化器创建 NVFP4 量化检查点，降低权重移动开销，面向边缘部署。",
     "effects":"未报告","paper_url":"https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/",
     "date":"2026-06-26","score":12,"score_relevance":7,"score_contribution":5,
     "score_reason":"NVFP4 量化技术落地边缘","source_tier":"官方动态","open_source":False,
     "tags":["方向:量化","方向:编译部署"],"authors":"NVIDIA","vendors":"NVIDIA","venue":"NVIDIA Developer"},
    {"id":"vendor-nvidia-ace-pubg-ally-2026","title":"KRAFTON 用 NVIDIA ACE 构建 PUBG Ally 端侧可同玩角色",
     "abstract":"KRAFTON 用 NVIDIA ACE 构建端侧可同玩角色，实时交互的 AI 伴侣。",
     "effects":"未报告","paper_url":"https://developer.nvidia.com/blog/how-krafton-built-pubg-ally-a-co-playable-character-powered-by-nvidia-ace/",
     "date":"2026-06-25","score":11,"score_relevance":7,"score_contribution":4,
     "score_reason":"端侧实时交互技术落地","source_tier":"官方动态","open_source":False,
     "tags":["方向:端侧agent"],"authors":"NVIDIA","vendors":"NVIDIA","venue":"NVIDIA Developer"},
    {"id":"vendor-nvidia-bev-pooling-2026","title":"在 NVIDIA GPU 上加速 BEV Pooling 用于物理 AI",
     "abstract":"在 NVIDIA GPU 上加速 BEV Pooling，用于自动驾驶/机器人边缘感知。",
     "effects":"未报告","paper_url":"https://developer.nvidia.com/blog/accelerating-bev-pooling-on-nvidia-gpus-for-physical-ai-applications/",
     "date":"2026-06-24","score":12,"score_relevance":7,"score_contribution":5,
     "score_reason":"边缘感知技术落地","source_tier":"官方动态","open_source":False,
     "tags":["方向:端侧agent","硬件:GPU"],"authors":"NVIDIA","vendors":"NVIDIA","venue":"NVIDIA Developer"},
    {"id":"vendor-nvidia-halos-robotics-2026","title":"NVIDIA Halos for Robotics：物理 AI 全栈功能安全",
     "abstract":"面向物理 AI 的全栈功能安全系统，给与人并肩工作的机器人。",
     "effects":"未报告","paper_url":"https://developer.nvidia.com/blog/inside-nvidia-halos-for-robotics-a-full-stack-functional-safety-system-for-physical-ai/",
     "date":"2026-06-22","score":12,"score_relevance":7,"score_contribution":5,
     "score_reason":"机器人安全系统落地","source_tier":"官方动态","open_source":False,
     "tags":["方向:安全隐私","方向:端侧agent"],"authors":"NVIDIA","vendors":"NVIDIA","venue":"NVIDIA Developer"},
    {"id":"vendor-nvidia-dflash-blackwell-2026","title":"在 Blackwell 上用 DFlash 投机解码提升推理 15 倍",
     "abstract":"在 NVIDIA Blackwell 上用 DFlash 投机解码把自回归 LLM 推理性能提升最高 15 倍。",
     "effects":"推理性能提升最高 15 倍","paper_url":"https://developer.nvidia.com/blog/boost-inference-performance-up-to-15x-on-nvidia-blackwell-using-dflash-speculative-decoding/",
     "date":"2026-06-23","score":12,"score_relevance":5,"score_contribution":7,
     "score_reason":"投机解码论文被大厂应用（用户认可信号）","source_tier":"官方动态","open_source":False,
     "tags":["方向:投机解码","方向:云端serving"],"authors":"NVIDIA","vendors":"NVIDIA","venue":"NVIDIA Developer"},
    {"id":"vendor-google-gemini-computer-use-2026","title":"Gemini 3.5 Flash 引入计算机使用",
     "abstract":"Gemini 3.5 Flash 内置计算机使用功能，agent 可跨浏览器/移动/桌面运行。",
     "effects":"未报告","paper_url":"https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-computer-use-gemini-3-5-flash/",
     "date":"2026-06-24","score":11,"score_relevance":6,"score_contribution":5,
     "score_reason":"computer use 是真 agent 能力（云端 Gemini）","source_tier":"官方动态","open_source":False,
     "tags":["方向:端侧agent","方向:工具调用","方向:云端serving"],"authors":"Google","vendors":"Google","venue":"Google Blog"},
    {"id":"vendor-samsung-6g-agents-2026","title":"从自动化到自主：AI Agent 重塑 6G 网络管理",
     "abstract":"AI agent(MCP/A2A)把 6G 网络管理从规则自动化转向自主意图驱动决策。",
     "effects":"未报告","paper_url":"https://research.samsung.com/blog/From-Automation-to-Autonomy-How-AI-Agents-Are-Reshaping-6G-Network-Management",
     "date":"2026-06-24","score":10,"score_relevance":5,"score_contribution":5,
     "score_reason":"6G 网络 agent（date 待确认）","source_tier":"官方动态","open_source":False,
     "tags":["方向:端侧agent","方向:云端serving"],"authors":"Samsung","vendors":"Samsung","venue":"Samsung Research"},
]


def main() -> int:
    p = ROOT / "research_runs" / "run-20260627-real2.json"
    run = json.loads(p.read_text(encoding="utf-8"))
    existing = {x["id"] for x in run["papers"]}
    added = 0
    for v in VENDORS:
        if v["id"] not in existing:
            run["papers"].append(v)
            added += 1
    p.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"appended {added} vendor entries; total now {len(run['papers'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
