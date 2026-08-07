#!/usr/bin/env python3
"""Shared tag helpers plus a retired fixed-date prototype builder.

The weekly pipeline imports ``auto_tags`` and ``first_sentence`` from this
module.  Its old executable builder is deliberately disabled because it embeds
historical dates and hand-written GitHub entries; use ``build_run_week.py`` with
a validated collection manifest instead.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 摘要关键词 -> tag（方向/应用/硬件/模型 维度）
TAG_RULES = [
    ("方向:量化", [r"quantiz", r"low-bit", r"int4", r"int8", r"fp4", r"ternary", r"bitnet"]),
    ("方向:KV cache", [r"kv cache", r"kv-cache", r"key-value cache", r"kvcache"]),
    ("方向:投机解码", [r"speculative decod", r"spec decode", r"medusa", r"eagle"]),
    ("方向:剪枝稀疏", [r"\bprun", r"spars", r"n:m"]),
    ("方向:蒸馏", [r"distill"]),
    ("方向:高效注意力", [r"flashattention", r"efficient attention", r"linear attention", r"sliding window"]),
    ("方向:稀疏注意力", [r"sparse attention", r"block-sparse"]),
    ("方向:记忆", [r"\bmemory\b", r"memgpt", r"memory bank", r"long-term memory"]),
    ("方向:工具调用", [r"tool use", r"tool-use", r"function call", r"tool calling"]),
    ("方向:多模态", [r"multimodal", r"\bvlm\b", r"vision-language", r"vision language"]),
    ("方向:MoE", [r"mixture of experts", r"\bmoe\b"]),
    ("方向:能耗功耗", [r"energy", r"low-power", r"low power", r"thermal"]),
    ("方向:端云协同", [r"edge-cloud", r"cloud-edge", r"offload", r"edge cloud"]),
    ("方向:联邦学习", [r"federat"]),
    ("方向:安全隐私", [r"privacy", r"unlearn", r"differential privacy", r"poison"]),
    ("方向:评测基准", [r"benchmark", r"evaluat"]),
    ("方向:云端serving", [r"serving system", r"data center", r"datacenter", r"cluster"]),
    ("方向:端侧agent", [r"on-device", r"on device", r"\bedge\b", r"mobile", r"embedded", r"\biot\b", r"\bagent\b"]),
    ("方向:SNN", [r"spiking neural network", r"\bsnn\b", r"spikformer", r"spiking transformer", r"spiking neuron model"]),
    # NB: bare "neuromorphic" is deliberately NOT a 方向:SNN trigger — neuromorphic
    # is a superset (Ising machines / event-based hardware / memristor crossbars)
    # and matches papers that never use a spiking neuron (e.g. Ising QUBO
    # solvers). Likewise bare "spike-based"/"spiking neuron" can be biological
    # (neuroscience spike trains), not SNN architecture. Require phrases that
    # name the SNN architecture itself. Neuromorphic HARDWARE still gets the
    # 硬件:神经形态 tag below via its own chip-name rule.
    ("硬件:NPU", [r"\bnpu\b", r"hexagon", r"snapdragon", r"neural engine"]),
    ("硬件:GPU", [r"\bgpu\b", r"\bcuda\b", r"vulkan", r"rtx", r"h100", r"h800"]),
    ("硬件:Jetson", [r"jetson"]),
    ("硬件:手机", [r"phone", r"android", r"\bios\b", r"smartphone"]),
    ("硬件:MCU", [r"microcontroller", r"\bmcu\b"]),
    ("硬件:DGX", [r"dgx"]),
    ("硬件:神经形态", [r"loihi", r"spinnaker", r"truenorth", r"neuromorphic chip", r"tianjic"]),
    ("模型:Llama", [r"\bllama\b"]),
    ("模型:Qwen", [r"\bqwen\b"]),
    ("模型:DeepSeek", [r"deepseek"]),
    ("模型:BitNet", [r"bitnet", r"ternary"]),
    ("模型:Phi", [r"\bphi-\d", r"\bphi\b"]),
    ("模型:MiniCPM", [r"minicpm"]),
    ("模型:Gemma", [r"\bgemma\b"]),
    ("模型:Mistral", [r"\bmistral\b"]),
    ("模型:GPT", [r"\bgpt\b"]),
    ("应用:OCR", [r"\bocr\b"]),
    ("应用:RAG", [r"\brag\b", r"retrieval-augmented"]),
    ("应用:语音", [r"speech", r"\basr\b", r"\btts\b"]),
    ("应用:代码", [r"coding agent", r"code agent", r"software engineer"]),
    ("应用:机器人", [r"robot", r"embodied"]),
    ("应用:IoT命令", [r"iot command", r"smart home"]),
    ("应用:长上下文推理", [r"long context", r"long-context", r"reasoning"]),
]


def auto_tags(title: str, summary: str) -> list[str]:
    text = (title + " " + summary).lower()
    tags: list[str] = []
    for tag, pats in TAG_RULES:
        if any(re.search(p, text) for p in pats):
            if tag not in tags:
                tags.append(tag)
    # 至少一个方向 tag
    if not any(t.startswith("方向:") for t in tags):
        tags.insert(0, "方向:端侧agent")
    return tags[:8]


def first_sentence(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    m = re.split(r"(?<=[.!?])\s", s)
    out = m[0] if m else s
    return out[:160] + ("…" if len(out) > 160 else "")


def convert_arxiv(path: Path) -> list[dict]:
    papers = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for p in papers:
        aid = re.sub(r"v\d+$", "", p["id"])
        summary = p.get("summary", "")
        text = (p.get("title", "") + " " + summary).lower()
        is_edge = bool(re.search(r"on-device|on device|\bedge\b|mobile|embedded|\biot\b|npu|phone|microcontroller|neuromorphic|loihi|spinnaker", text))
        rel = 7 if is_edge else 5
        contrib = 5
        authors = p.get("authors") or []
        auth_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
        out.append({
            "id": f"arxiv-{aid}",
            "title": p.get("title", "").strip(),
            "title_zh": "",
            "abstract": first_sentence(summary),
            "effects": "未报告",
            "mechanism": "未报告",
            "paper_url": f"https://arxiv.org/abs/{aid}",
            "date": p.get("published", "")[:10],
            "score": rel + contrib,
            "score_relevance": rel,
            "score_contribution": contrib,
            "score_reason": "auto-converted（乙方案首版）；affiliation/精修大白话/精调分数待后续补",
            "source_tier": "学校预印本",
            "open_source": bool(re.search(r"github\.com|github\.io", summary, re.I)),
            "tags": auto_tags(p.get("title", ""), summary),
            "authors": auth_str,
            "vendors": "",
            "venue": "arXiv",
            # 自动转换只扩充完整收录；推荐必须由主 Agent 阅读来源后策展。
            "recommendation": "纳入",
            "recommendation_reason": "",
        })
    return out


GITHUB_ENTRIES = [
    {
        "id": "github-llamacpp-b9860",
        "title": "llama.cpp b9860：模型文件类型 API + 端侧 Android/iOS/Mac 构建",
        "abstract": "端侧推理引擎 llama.cpp 本周连续 release（b9858/b9859/b9860），b9860 新增 llama_ftype_name() C API 暴露模型量化文件类型（Q8_0/Q4_K 等），b9859 加 OpenCL 预编译二进制 kernel 加载（Adreno GPU），持续提供 Android/iOS XCFramework/macOS/Vulkan/SYCL 端侧构建。",
        "effects": "未报告",
        "mechanism": "GGUF 文件类型 API + OpenCL binary kernel + 端侧跨平台构建产物。",
        "paper_url": "https://github.com/ggml-org/llama.cpp/releases/tag/b9860",
        "date": "2026-07-02",
        "score": 14, "score_relevance": 9, "score_contribution": 5,
        "score_reason": "端侧推理核心引擎本周连续 release（MCP list_releases 验证 07-02）",
        "source_tier": "开源大项目", "open_source": True,
        "tags": ["方向:推理框架", "方向:编译部署", "硬件:手机"],
        "authors": "ggml-org", "vendors": "", "venue": "GitHub",
    },
    {
        "id": "github-vllm-v0.24.0",
        "title": "vLLM v0.24.0：DFlash 投机解码 + DiffusionGemma + 量化 Model Runner V2",
        "abstract": "vLLM v0.24.0（571 commits/256 contributors）：新增 MiniMax-M3、DeepSeek-V4 持续优化、DFlash 投机解码进 MRv2、DiffusionGemma 扩散 LLM、统一 streaming tool-call 解析引擎、MRv2 默认支持量化模型。",
        "effects": "未报告",
        "mechanism": "投机解码 + 扩散 LLM 路径 + 量化模型运行时 + 统一解析引擎。",
        "paper_url": "https://github.com/vllm-project/vllm/releases/tag/v0.24.0",
        "date": "2026-06-29",
        "score": 12, "score_relevance": 6, "score_contribution": 6,
        "score_reason": "云端 serving 大版本，含投机解码/量化/扩散 LLM 等可迁移端侧的技术（MCP 验证 06-29）",
        "source_tier": "开源大项目", "open_source": True,
        "tags": ["方向:云端serving", "方向:投机解码", "方向:推理框架"],
        "authors": "vllm-project", "vendors": "", "venue": "GitHub",
    },
    {
        "id": "github-sglang-v0.5.14",
        "title": "SGLang v0.5.14：DeepSeek-V4 GB300 + int8 线性注意力前缀缓存",
        "abstract": "SGLang v0.5.14：DeepSeek-V4 在 GB300 上 day-0 支持（5× 吞吐）、Waterfill/LPLB MoE 负载均衡、线性注意力 int8 检查点池大幅扩前缀缓存容量、KDA CuteDSL prefill kernel。",
        "effects": "未报告",
        "mechanism": "MoE 负载均衡 + 线性注意力 int8 状态压缩 + Blackwell kernel。",
        "paper_url": "https://github.com/sgl-project/sglang/releases/tag/v0.5.14",
        "date": "2026-06-26",
        "score": 11, "score_relevance": 5, "score_contribution": 6,
        "score_reason": "云端 serving 大版本，int8 前缀缓存等技术可参考端侧（MCP 验证 06-26）",
        "source_tier": "开源大项目", "open_source": True,
        "tags": ["方向:云端serving", "方向:KV cache", "方向:MoE"],
        "authors": "sgl-project", "vendors": "", "venue": "GitHub",
    },
    {
        "id": "github-deepseek-dspark-2026",
        "title": "DSpark：DeepSeek 投机解码 draft 模型（DeepSpec 框架）",
        "abstract": "DeepSeek 开源 DSpark 投机解码 draft 模型算法，发布在 DeepSpec 全栈训练/评测框架中，配套 Qwen3-4B/8B/14B 与 Gemma4-12B 的 block7 draft checkpoint；据新闻称让 DeepSeek-V4 推理快最高 85%。",
        "effects": "新闻称 DeepSeek-V4 推理速度提升最高 85%；README 给出 gsm8k/math500/aime25 等基准的投机解码 acceptance 评测。",
        "mechanism": "训练 draft model 做投机解码；DeepSpec 提供数据准备/训练/评测全栈，DSpark 为 block7 draft 架构（与 DFlash/Eagle3 并列）。",
        "paper_url": "https://github.com/deepseek-ai/DeepSpec",
        "date": "2026-06-27",
        "score": 15, "score_relevance": 7, "score_contribution": 8,
        "score_reason": "DeepSeek 官方开源投机解码框架（DeepSpec 仓，无 arXiv 无 release tag，社区已涌现 vLLM/MLX/GB10 移植版=爆火；URL 200）",
        "source_tier": "开源大项目", "open_source": True,
        "tags": ["方向:投机解码", "方向:推理框架", "模型:DeepSeek"],
        "authors": "DeepSeek AI", "vendors": "DeepSeek", "venue": "GitHub",
    },
    {
        "id": "github-prima-cpp-2026",
        "title": "prima.cpp：家用异构设备上 30-70B LLM 快速推理",
        "abstract": "prima.cpp（ICLR2026 official）在家用异构/日常设备上做 30-70B LLM 分布式推理，面向 on-device-llm 与 distributed-inference。",
        "effects": "未报告",
        "mechanism": "异构设备分布式推理 + 跨设备协同，把大模型塞进家用硬件。",
        "paper_url": "https://github.com/OpenCPIL/prima.cpp",
        "date": "2026-06-30",
        "score": 14, "score_relevance": 9, "score_contribution": 5,
        "score_reason": "ICLR2026 official 端侧大模型推理引擎（GitHub trending/search 发现，URL 200）",
        "source_tier": "开源大项目", "open_source": True,
        "tags": ["方向:推理框架", "方向:编译部署", "硬件:GPU"],
        "authors": "OpenCPIL", "vendors": "", "venue": "GitHub",
    },
    {
        "id": "github-sim-use-2026",
        "title": "sim-use：AI agent 在 iOS/Android 真机上的眼和手",
        "abstract": "LY Corp 开源 sim-use，让 AI agent 在 iOS Simulator 与 Android 真机/模拟器上有视觉与操作能力（eyes and hands），爆火。",
        "effects": "未报告",
        "mechanism": "移动设备 agent 控制，accessibility + 自动化接口。",
        "paper_url": "https://github.com/lycorp-jp/sim-use",
        "date": "2026-06-26",
        "score": 13, "score_relevance": 8, "score_contribution": 5,
        "score_reason": "爆火端侧 mobile agent 仓（GitHub trending 发现）",
        "source_tier": "开源大项目", "open_source": True,
        "tags": ["方向:端侧agent", "硬件:手机"],
        "authors": "LY Corp", "vendors": "LY Corp", "venue": "GitHub",
    },
    {
        "id": "github-caix-2026",
        "title": "caix：Apple Core AI 原生端侧推理服务",
        "abstract": "caix 是 Apple Silicon 原生的 Core AI 推理服务（beta），提供 OpenAI/Anthropic API、dashboard、带工具/技能/MCP 的流式对话，支持 MTP 投机解码，跑在 neural-engine/mlx 上。",
        "effects": "未报告",
        "mechanism": "Apple Core AI + neural engine + MLX，端侧推理服务 + 投机解码。",
        "paper_url": "https://github.com/RedHillsMediaFL/caix",
        "date": "2026-06-27",
        "score": 12, "score_relevance": 8, "score_contribution": 4,
        "score_reason": "Apple Core AI 端侧推理服务（稀缺信号，GitHub search 发现）",
        "source_tier": "开源大项目", "open_source": True,
        "tags": ["方向:推理框架", "方向:端侧agent"],
        "authors": "RedHillsMediaFL", "vendors": "", "venue": "GitHub",
    },
    {
        "id": "github-tenstorrent-vllm-tt-plugin-2026",
        "title": "Tenstorrent vLLM 后端插件：AI 加速器接入 vLLM",
        "abstract": "Tenstorrent 官方发布 vllm-tt-plugin，把 Tenstorrent AI 加速器作为后端插件接入 vLLM 推理，扩展非 GPU 加速器的 LLM serving 路径。",
        "effects": "未报告",
        "mechanism": "vLLM 后端插件抽象 + Tenstorrent 硬件 kernel。",
        "paper_url": "https://github.com/tenstorrent/vllm-tt-plugin",
        "date": "2026-07-02",
        "score": 12, "score_relevance": 6, "score_contribution": 6,
        "score_reason": "Tenstorrent 官方 AI 加速器后端接入 vLLM（GitHub search 本周新建，URL 200）",
        "source_tier": "开源大项目", "open_source": True,
        "tags": ["方向:推理框架", "方向:编译部署"],
        "authors": "Tenstorrent", "vendors": "Tenstorrent", "venue": "GitHub",
    },
]


def main() -> int:
    print(
        "[ERROR] fixed-date prototype retired; run agent/build_run_week.py with "
        "research_runs/collection-manifest.json",
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
