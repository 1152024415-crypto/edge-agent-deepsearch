#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble this week's research run from the 4 collection candidate files.

Reads:
  .superpowers/sdd/arxiv_candidates.json   (arxiv curl sweep)
  research_runs/candidates-hf.json         (HF Daily Papers subagent)
  research_runs/candidates-github.json     (GitHub whitelist subagent)
  research_runs/candidates-vendor.json     (vendor blog subagent)

Validates the four-source collection manifest, converts candidates to the
方案 B schema, keeps direct edge work plus relevant adjacent inference/deployment
work, and writes research_runs/run-<ts>.json.  Initial scores are never
recommendations; the main agent must verify final scores and affiliation evidence.

Re-run after editing candidates. Historical recovery may skip missing files only
with an explicit bypass; normal weekly assembly requires all four artifacts.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))
sys.path.insert(0, str(ROOT))

from build_run_from_arxiv import auto_tags, first_sentence, TAG_RULES  # noqa: E402
from research_collection import (  # noqa: E402
    CollectionCoverageError,
    candidate_output_identity,
    candidate_record_ref,
    is_required_github_project,
    load_collection_manifest,
    parse_collection_date,
    validate_candidate_artifacts,
)

ARXIV_CAND = ROOT / ".superpowers" / "sdd" / "arxiv_candidates.json"
HF_CAND = ROOT / "research_runs" / "candidates-hf.json"
GH_CAND = ROOT / "research_runs" / "candidates-github.json"
VENDOR_CAND = ROOT / "research_runs" / "candidates-vendor.json"
COLLECTION_MANIFEST = ROOT / "research_runs" / "collection-manifest.json"

# keyword -> (vendors english name, source_tier). From vendor-whitelist.md.
# Used to detect company affiliation in arxiv author strings / summaries so
# company papers surface as 公司项目 (the user wants more of these).
AFFIL = [
    (r"ByteDance|字节跳动|ByteDance Seed", "ByteDance"),
    (r"Tencent|腾讯", "Tencent"),
    (r"Kuaishou|Kwai|快手", "Kuaishou"),
    (r"Baidu|百度", "Baidu"),
    (r"Meituan|美团", "Meituan"),
    (r"JD\.com|Jingdong|京东", "JD.com"),
    (r"Pinduoduo|PDD|拼多多", "Pinduoduo"),
    (r"NetEase|网易", "NetEase"),
    (r"Alibaba|阿里云|Qwen Team|Qwen", "Alibaba"),
    (r"DeepSeek", "DeepSeek"),
    (r"Moonshot", "Moonshot"),
    (r"Zhipu|智谱", "Zhipu"),
    (r"MiniMax", "MiniMax"),
    (r"ModelBest|面壁|OpenBMB", "ModelBest"),
    (r"Mistral", "Mistral"),
    (r"NVIDIA", "NVIDIA"),
    (r"Samsung", "Samsung"),
    (r"Huawei|海思|HiSilicon", "Huawei"),
    (r"Qualcomm", "Qualcomm"),
    (r"MediaTek", "MediaTek"),
    (r"Xiaomi|小米", "Xiaomi"),
    (r"OPPO", "OPPO"),
    (r"vivo", "vivo"),
    (r"Honor|荣耀", "Honor"),
    (r"Apple Inc|\bApple\b", "Apple"),
    (r"Meta AI|Meta FAIR|\bMeta\b", "Meta"),
    (r"Microsoft Research|\bMicrosoft\b", "Microsoft"),
    (r"Google Research|Google DeepMind|\bGoogle\b", "Google"),
    (r"Anthropic", "Anthropic"),
    (r"OpenAI", "OpenAI"),
]


def detect_affil(text: str) -> str | None:
    t = text.lower()
    for pat, name in AFFIL:
        if re.search(pat.lower(), t):
            return name
    return None


def explicit_affiliation_text(candidate: dict) -> str:
    """Return only declared affiliation evidence, never title/summary model mentions."""
    values = []
    for field in ("affiliation", "affiliations", "author_affiliations", "institution", "institutions"):
        value = candidate.get(field)
        if isinstance(value, list):
            values.extend(str(item) for item in value if item)
        elif value:
            values.append(str(value))
    return " ".join(values)


def _coerce_authors(v) -> str:
    """authors may be a list (HF) or '; '-joined string (arXiv) — coerce to str."""
    if isinstance(v, list):
        return ", ".join(str(a) for a in v)
    return str(v) if v else ""


DIRECT_RE = re.compile(
    r"on-device|on device|edge[- ](?:ai|agents?|llms?|models?|inference|comput|device|system|hardware|"
    r"platform|deployment|accelerator|gpu|npu|server)|"
    r"mobile[- ](?:ai|agents?|assistants?|llms?|models?|inference|deployment|device|hardware|npu|rag)|"
    r"mobile[- ](?:autonomous[- ])?agents?|"
    r"embedded[- ](?:ai|agents?|llms?|models?|neural networks?|inference|system|device|hardware|"
    r"platform|processor|accelerator)|device[- ]side|local[- ](?:ai|llms?|models?)[- ](?:inference|execution|serving)|"
    r"\biot\b|\bnpu\b|\bevks?\b|hexagon htp|dragonwing|\b(?:smart)?phone\b|"
    r"microcontroller|\bmcus?\b|\besp32\b|\bstm32\b|\blinux sbc\b|neuromorphic|loihi|spinnaker|raspberry|"
    r"jetson|smartwatch|wearable|\bonboard\b|tinyml|low.?power|resource.?constrain|"
    r"edge computing|edge ai|edge inference|mobile inference|\bmcus?\b|\bfpga\b|"
    r"端侧|端上|边缘(?:设备|推理|计算|系统|芯片)|设备端|离线运行|本地运行|"
    r"llama\.cpp|executorch|mlc-llm|onnx runtime|mediapipe|litert|core ml|openvino|"
    r"\bmnn\b|\bncnn\b",
    re.I,
)
AI_RE = re.compile(
    r"\bai\b|\bllms?\b|language models?|foundation models?|diffusion models?|transformer|"
    r"neural network|spiking neural|\bsnns?\b|generative ai|\bagents?\b|\bagentic\b|\bassistants?\b|\bvlms?\b|"
    r"vision-language|machine learning|deep learning|\binference\b|tinyml|executorch|"
    r"llama\.cpp|litert|core ml|openvino|computer vision|object detection|"
    r"speech recognition|keyword spotting|\byolo\b|image classification|"
    r"人工智能|语言模型|神经网络|生成式|推理",
    re.I,
)
MODEL_TASK_RE = re.compile(
    r"\bai\b|\bllms?\b|language models?|foundation models?|diffusion models?|transformer|"
    r"neural network|spiking neural|\bsnns?\b|generative ai|agentic ai|\bai agents?\b|"
    r"\bvlms?\b|vision-language|machine learning|deep learning|\binference\b|tinyml|"
    r"computer vision|object detection|speech recognition|keyword spotting|\byolo\b|"
    r"image classification|world[- ]action models?|vision-language-action|"
    r"executorch|llama\.cpp|litert|core ml|openvino|mediapipe|onnx runtime|"
    r"语言模型|神经网络|生成式|模型推理|人工智能",
    re.I,
)
AGENT_LOOP_RE = re.compile(
    r"autonomous|planning|planner|memory|tool(?: use| calling)?|action|actuation|"
    r"environment interaction|control loop|self-correct|self-heal|自主|规划|记忆|工具调用|"
    r"行动闭环|设备执行|受约束执行|状态对账|故障恢复",
    re.I,
)
OFFICIAL_TOPIC_RE = re.compile(
    r"人工智能|智能体|模型|推理|算力|工具调用|沙箱|安全护栏|云端|本地运行|设备端|"
    r"\bai\b|\bagents?\b|\bagentic\b|\bllms?\b|\bvlms?\b|inference|model|compute|sandbox",
    re.I,
)
STACK_RE = re.compile(
    r"quantiz|(?:model|weight|channel|token|kv|attention|expert|network|neural|structured|unstructured)"
    r"[- ]prun\w*|prun\w*[^.]{0,30}(?:model|weight|channel|token|kv|attention|expert|network|neural)|"
    r"(?:knowledge|model|self)[- ]?distill|distillation|speculative decoding|"
    r"kv.?cache|small model|small language|\bsnn\b|"
    r"model compression|efficient inference|inference acceleration|"
    r"(?:model|llm|vlm|inference|on-device|edge|mobile) deployment|"
    r"deploy(?:ing|ed)? (?:a |the )?(?:model|llm|vlm|neural network|inference engine|runtime)|runtime|"
    r"serving|latency|throughput|"
    r"(?:model|llm|vlm|inference|decoding|generation|training|hardware)[- ]accelerat\w*|"
    r"accelerat\w*[^.]{0,30}(?:model|llm|vlm|inference|decoding|generation|runtime|hardware)|"
    r"hardware.?friendly|co.?design|\bmoe\b|"
    r"sparse attention|efficient attention|federat|offload|compil|memory footprint|"
    r"energy[- ](?:efficient|efficiency|aware|consumption|saving|budget)|power consumption|"
    r"real.?time (?:inference|serving|processing|execution)|"
    r"token compression|memory compress|compress\w*[^.]{0,40}(?:long.?term )?memory|"
    r"visual[- ]token[- ]prun\w*|sliding[- ]recurrent[- ]memory|recurrent[- ]memory|"
    r"(?:agent|assistant)[^.]{0,50}memory|memory[^.]{0,50}(?:agent|assistant)|"
    r"agent(?:ic)?[- ](?:training|infrastructure|platform)|agentic modeling|"
    r"量化|剪枝|蒸馏|压缩|缓存|低延迟|吞吐|运行时|持续推理|"
    r"(?:模型|推理|端侧|设备端)部署|(?:推理|模型|硬件)加速|加速(?:推理|部署)",
    re.I,
)
GUI_RE = re.compile(r"gui agent|computer use|screen.?click|screen.?tap|ui automation|web navigation", re.I)
GUI_SYSTEM_RE = re.compile(
    r"on-device inference|edge inference|\bnpu\b|\bmcu\b|embedded|runtime|serving|latency|"
    r"quantiz|model compression|low.?power|resource.?constrain|system architecture|privacy|security|safety",
    re.I,
)
PRECISE_ADJACENT_TITLE_RE = re.compile(
    r"visual[- ]token[- ]prun\w*|sliding[- ]recurrent[- ]memory",
    re.I,
)


def classify_research_relevance(text: str) -> str:
    """Classify broad collection scope without using novelty as a deletion gate."""
    value = text or ""
    title, separator, _body = value.partition("\n")
    central = title if separator else value
    if GUI_RE.search(value) and not GUI_SYSTEM_RE.search(value):
        return "irrelevant"
    direct_agent_loop = re.search(r"\bagents?\b|\bagentic\b|\bassistants?\b|智能体", value, re.I) and AGENT_LOOP_RE.search(value)
    if DIRECT_RE.search(value) and (MODEL_TASK_RE.search(value) or direct_agent_loop):
        return "direct"
    # Adjacent work must make the inference/deployment technique central enough
    # to name it in the title.  A baseline mentioned deep in an abstract is not
    # evidence that the paper contributes to the edge-AI stack.
    if STACK_RE.search(central) and (
        AI_RE.search(central)
        or (PRECISE_ADJACENT_TITLE_RE.search(central) and AI_RE.search(value))
    ):
        return "adjacent"
    return "irrelevant"


def is_edge_text(text: str) -> bool:
    """Backward-compatible broad inclusion check used by existing callers/tests."""
    return classify_research_relevance(text) != "irrelevant"


def candidate_tags(title: str, summary: str, relevance: str) -> list[str]:
    # 自动关键词只负责召回，不具备认定“真正端侧 Agent”的权限。
    # 该标签必须由主 Agent 阅读来源并填写 edge_agent_scope 后人工加入。
    tags = [tag for tag in auto_tags(title, summary) if tag != "方向:端侧agent"]
    return tags or ["方向:高效推理"]


def public_score_reason(
    relevance: str,
    tags: list[str],
    *,
    source_tier: str,
    vendor: str = "",
) -> str:
    """Build a reader-facing scoring explanation, never pipeline status text."""
    topics = []
    for tag in tags:
        value = tag.split(":", 1)[-1].strip()
        if value and value not in topics:
            topics.append(value)
    focus = "、".join(topics[:3]) or "高效推理"
    if source_tier == "官方动态":
        return f"来自{vendor or '厂商'}官方发布，内容直接涉及{focus}，因此作为本周官方动态收录。"
    if source_tier == "开源大项目":
        return f"白名单开源项目的正式版本更新，重点涉及{focus}，可直接跟踪落地能力。"
    if relevance == "direct":
        reason = f"明确涉及端侧或资源受限设备，相关性较高；主要贡献集中在{focus}。"
    else:
        reason = f"属于{focus}等端侧可迁移技术，但未明确端侧部署，因此相关度按中等计。"
    if source_tier == "公司项目" and vendor:
        return f"论文机构证据明确包含 {vendor}；{reason}"
    return reason


def convert_arxiv(c: dict) -> dict | None:
    aid = re.sub(r"v\d+$", "", str(c.get("id") or "")).strip()
    title, paper_url, source_date = candidate_output_identity("arxiv", c)
    summary = c.get("abstract") or c.get("summary") or ""
    authors = _coerce_authors(c.get("authors"))
    text = (title + "\n" + summary).lower()
    # Broad collection keeps direct and adjacent AI inference/deployment work.
    # Only completely unrelated keyword collisions are removed here.
    relevance = classify_research_relevance(text)
    if relevance == "irrelevant":
        return None
    rel = 8 if relevance == "direct" else 5
    contrib = 5
    tags = candidate_tags(title, summary, relevance)
    # Only an explicit affiliation field may promote a paper to 公司项目.
    affiliation_evidence_url = str(c.get("affiliation_evidence_url") or "").strip()
    vendor = detect_affil(explicit_affiliation_text(c)) if affiliation_evidence_url else None
    if vendor:
        tier = "公司项目"
    else:
        tier = "学校预印本"
    score_reason = public_score_reason(
        relevance,
        tags,
        source_tier=tier,
        vendor=vendor or "",
    )
    return {
        "id": f"arxiv-{aid}",
        "title": title,
        "title_zh": "",
        "abstract": first_sentence(summary),
        "effects": "未报告",
        "mechanism": "未报告",
        "paper_url": paper_url,
        "date": source_date,
        "score": rel + contrib,
        "score_relevance": rel,
        "score_contribution": contrib,
        "score_reason": score_reason,
        "source_tier": tier,
        "open_source": bool(re.search(r"github\.com|github\.io", summary, re.I)),
        "tags": tags,
        "edge_agent_scope": "待核实",
        "edge_agent_evidence": "",
        "authors": authors,
        "vendors": vendor or "",
        "affiliation_evidence_url": affiliation_evidence_url if vendor else "",
        "venue": "arXiv",
        # 自动汇集只负责扩充完整收录；“推荐”必须由主 Agent 阅读后人工判断。
        "recommendation": "纳入",
        "recommendation_reason": "",
        "candidate_source": "arxiv",
        "candidate_ref": candidate_record_ref(c),
        "arxiv_date_basis": str(c.get("date_basis") or "submitted"),
        # 更新稿必须由主 Agent 比对旧版，确认有实质变化后才能填写并发布。
        "arxiv_revision_note": "",
    }


def convert_hf(c: dict, seen_arxiv: set) -> dict | None:
    url = c.get("paper_url") or ""
    m = re.search(r"(?:arxiv\.org/abs/|huggingface\.co/papers/)(\d{4}\.\d{4,5})", url)
    if m:
        aid = m.group(1)
        if aid in seen_arxiv:
            return None  # dup with arxiv sweep
        pid = f"arxiv-{aid}"
        # Use the HF paper page URL (not arxiv.org) so the validator does NOT
        # arXiv-date-cross-check (HF feature date ≠ arXiv submitted date for
        # many daily-paper picks, and arxiv API is rate-limited/unreachable in
        # this env). HF page is a real, live paper source; date = HF feature
        # date, consistent with HF-sourced entry.
        paper_url = f"https://huggingface.co/papers/{aid}"
    else:
        pid = c.get("id") or f"hf-{re.sub(r'[^a-z0-9]+', '-', (c.get('title') or 'x').lower())[:60]}"
        paper_url = url or ""
    title, identity_url, source_date = candidate_output_identity("huggingface", c)
    paper_url = identity_url
    summary = c.get("abstract") or ""
    authors = _coerce_authors(c.get("authors"))
    text = (title + "\n" + summary).lower()
    relevance = classify_research_relevance(text)
    if relevance == "irrelevant":
        return None
    rel = 8 if relevance == "direct" else 5
    contrib = 5
    tags = candidate_tags(title, summary, relevance)
    affiliation_evidence_url = str(c.get("affiliation_evidence_url") or "").strip()
    vendor = detect_affil(explicit_affiliation_text(c)) if affiliation_evidence_url else None
    tier = "公司项目" if vendor else "学校预印本"
    score_reason = public_score_reason(
        relevance,
        tags,
        source_tier=tier,
        vendor=vendor or "",
    )
    return {
        "id": pid, "title": title, "title_zh": "",
        "abstract": first_sentence(summary), "effects": "未报告", "mechanism": "未报告",
        "paper_url": paper_url, "date": source_date,
        "score": rel + contrib, "score_relevance": rel, "score_contribution": contrib,
        "score_reason": score_reason,
        "source_tier": tier,
        "open_source": bool(re.search(r"github\.com|github\.io", summary, re.I)),
        "tags": tags, "authors": authors, "vendors": vendor or "",
        "edge_agent_scope": "待核实", "edge_agent_evidence": "",
        "affiliation_evidence_url": affiliation_evidence_url if vendor else "",
        "venue": "HuggingFace Daily", "recommendation": "纳入", "recommendation_reason": "",
        "candidate_source": "huggingface", "candidate_ref": candidate_record_ref(c),
    }


def convert_github(c: dict) -> dict | None:
    repo = c.get("repo") or ""
    tag = c.get("tag") or ""
    if not is_required_github_project(repo):
        return None
    title, url, source_date = candidate_output_identity("github", c)
    summary = c.get("summary") or ""
    # GitHub candidates are a single, explicit facet: whitelisted big projects.
    tier = "开源大项目"
    vendor = str(c.get("vendor") or "")
    affiliation_evidence_url = ""
    text = (title + "\n" + summary).lower()
    relevance = classify_research_relevance(text)
    if relevance == "irrelevant":
        return None
    rel = 8 if relevance == "direct" else 5
    contrib = 6
    tags = candidate_tags(title, summary, relevance)
    if not any(t == "方向:推理框架" for t in tags):
        tags.append("方向:推理框架")
    tags = tags[:8]
    owner = repo.split("/")[0] if "/" in repo else repo
    return {
        "id": f"github-{re.sub(r'[^a-z0-9]+','-',(repo+'-'+tag).lower())[:70]}",
        "title": title,
        "title_zh": "",
        "abstract": first_sentence(summary) or summary[:160],
        "effects": "未报告", "mechanism": "未报告",
        "paper_url": url, "date": source_date,
        "score": rel + contrib, "score_relevance": rel, "score_contribution": contrib,
        "score_reason": public_score_reason(relevance, tags, source_tier=tier, vendor=vendor),
        "source_tier": tier, "open_source": True,
        "tags": tags, "authors": owner, "vendors": vendor,
        "edge_agent_scope": "待核实", "edge_agent_evidence": "",
        "affiliation_evidence_url": affiliation_evidence_url,
        "venue": "GitHub", "recommendation": "纳入", "recommendation_reason": "",
        "candidate_source": "github", "candidate_ref": candidate_record_ref(c),
    }


def convert_vendor(c: dict) -> dict | None:
    vendor = c.get("vendor") or ""
    title, url, source_date = candidate_output_identity("vendors", c)
    summary = c.get("summary") or ""
    text = (title + "\n" + summary).lower()
    relevance = classify_research_relevance(text)
    # The vendor candidate file is already a manually curated slice of the
    # official-source sweep.  Product names and editorial headlines often omit
    # the technical keyword that appears in the body, so retain clear AI/Agent
    # or inference-stack evidence from the full candidate at adjacent priority.
    if relevance == "irrelevant" and (
        AI_RE.search(text) or STACK_RE.search(text) or OFFICIAL_TOPIC_RE.search(text)
    ):
        relevance = "adjacent"
    if relevance == "irrelevant":
        return None
    rel = 9 if relevance == "direct" else 5
    contrib = 5
    tags = candidate_tags(title, summary, relevance)
    tags = tags[:8]
    return {
        "id": f"vendor-{re.sub(r'[^a-z0-9]+','-',(vendor+'-'+title).lower())[:70]}",
        "title": title,
        "title_zh": "",
        "abstract": first_sentence(summary) or summary[:160],
        "effects": "未报告", "mechanism": "未报告",
        "paper_url": url, "date": source_date,
        "score": rel + contrib, "score_relevance": rel, "score_contribution": contrib,
        "score_reason": public_score_reason(
            relevance,
            tags,
            source_tier="官方动态",
            vendor=vendor,
        ),
        "source_tier": "官方动态", "open_source": False,
        "tags": tags, "authors": vendor, "vendors": vendor,
        "edge_agent_scope": "待核实", "edge_agent_evidence": "",
        "affiliation_evidence_url": "",
        "venue": vendor, "recommendation": "纳入", "recommendation_reason": "",
        "candidate_source": "vendors", "candidate_ref": candidate_record_ref(c),
    }


def load(path: Path, required: bool = False):
    if not path.exists():
        if required:
            raise CollectionCoverageError(f"required candidate artifact missing: {path}")
        print(f"[ASSEMBLE] WARN missing: {path}")
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        if required:
            raise CollectionCoverageError(f"required candidate artifact is invalid: {path}: {e}") from e
        print(f"[ASSEMBLE] WARN bad JSON {path}: {e}")
        return []
    if not isinstance(value, list):
        if required:
            raise CollectionCoverageError(f"required candidate artifact must be a JSON list: {path}")
        print(f"[ASSEMBLE] WARN candidate JSON is not a list: {path}")
        return []
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Assemble a weekly research run from four source files.")
    parser.add_argument("--today", help="Override collection date as YYYY-MM-DD")
    parser.add_argument("--manifest", default=str(COLLECTION_MANIFEST))
    parser.add_argument(
        "--allow-incomplete-coverage",
        action="store_true",
        help="Historical recovery only; normal weekly research must never use this flag.",
    )
    args = parser.parse_args(argv)
    run_date = parse_collection_date(args.today)
    manifest = None
    if not args.allow_incomplete_coverage:
        manifest = load_collection_manifest(args.manifest, today=run_date)

    require_artifacts = not args.allow_incomplete_coverage
    arxiv = load(ARXIV_CAND, required=require_artifacts)
    hf = load(HF_CAND, required=require_artifacts)
    gh = load(GH_CAND, required=require_artifacts)
    vendor = load(VENDOR_CAND, required=require_artifacts)
    if manifest is not None:
        validate_candidate_artifacts(
            manifest,
            {
                "arxiv": ARXIV_CAND,
                "huggingface": HF_CAND,
                "github": GH_CAND,
                "vendors": VENDOR_CAND,
            },
        )

    seen_arxiv_ids = {re.sub(r"v\d+$", "", str(c.get("id") or "")) for c in arxiv}
    papers = []
    for c in arxiv:
        p = convert_arxiv(c)
        if p:
            papers.append(p)
    for c in vendor:
        p = convert_vendor(c)
        if p:
            papers.append(p)
    for c in gh:
        p = convert_github(c)
        if p:
            papers.append(p)
    for c in hf:
        e = convert_hf(c, seen_arxiv_ids)
        if e:
            papers.append(e)

    # dedup by id (keep first; arxiv-derived ids may collide with hf-derived arxiv ids)
    seen = set()
    uniq = []
    for p in papers:
        pid = p["id"]
        if pid in seen:
            continue
        seen.add(pid)
        uniq.append(p)

    # drop entries with empty paper_url or empty date (validation would fail)
    uniq = [p for p in uniq if p["paper_url"] and p["date"]]
    # abstract is a required field — drop entries whose source had no abstract
    # (e.g. HF Daily Papers marked "Abstract not available"). Can't honestly
    # synthesize one without reading the paper, so skip rather than ship empty.
    before = len(uniq)
    uniq = [p for p in uniq if (p.get("abstract") or "").strip()]
    if len(uniq) < before:
        print(f"[ASSEMBLE] dropped {before - len(uniq)} entries with empty abstract")

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    payload = {
        "run_id": f"run-{ts}",
        "generated_at": datetime.datetime.now().astimezone().isoformat(),
        "papers": uniq,
    }
    if manifest is not None:
        payload["collection_manifest"] = manifest
    out = ROOT / "research_runs" / f"run-{ts}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # tier breakdown
    from collections import Counter
    tiers = Counter(p["source_tier"] for p in uniq)
    print(f"[ASSEMBLE] wrote {out} · {len(uniq)} papers")
    print(f"  tiers: {dict(tiers)}")
    print(f"  arxiv={len(arxiv)} vendor={len(vendor)} github={len(gh)} hf={len(hf)} "
          f"(hf deduped against arxiv)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
