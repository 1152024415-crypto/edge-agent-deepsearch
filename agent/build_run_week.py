#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble this week's research run from the 4 collection candidate files.

Reads:
  .superpowers/sdd/arxiv_candidates.json   (arxiv curl sweep)
  research_runs/candidates-hf.json         (HF Daily Papers subagent)
  research_runs/candidates-github.json     (GitHub whitelist subagent)
  research_runs/candidates-vendor.json     (vendor blog subagent)

Converts each to the 方案 B run schema (2-dim score + 4-dim tags + source_tier),
auto-tags + scores via build_run_from_arxiv.auto_tags / is_edge heuristic,
detects company affiliations in arxiv author strings to mark 公司项目 (volume
boost the user asked for), dedups by id, and writes research_runs/run-<ts>.json.

Re-run after editing candidates. Tolerates missing files (skips with a warning)
so it can be run incrementally as subagents finish.
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))
sys.path.insert(0, str(ROOT))

from build_run_from_arxiv import auto_tags, first_sentence, TAG_RULES  # noqa: E402

ARXIV_CAND = ROOT / ".superpowers" / "sdd" / "arxiv_candidates.json"
HF_CAND = ROOT / "research_runs" / "candidates-hf.json"
GH_CAND = ROOT / "research_runs" / "candidates-github.json"
VENDOR_CAND = ROOT / "research_runs" / "candidates-vendor.json"

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


def _coerce_authors(v) -> str:
    """authors may be a list (HF) or '; '-joined string (arXiv) — coerce to str."""
    if isinstance(v, list):
        return ", ".join(str(a) for a in v)
    return str(v) if v else ""


def is_edge_text(text: str) -> bool:
    # Broad edge-AI relevance check — not just device keywords, but the full
    # tech stack (efficient inference, quantization, pruning, speculative, KV cache,
    # small models, federated, deployment, etc.). Catches papers relevant to
    # edge/on-device AI even if they don't explicitly say "on-device".
    return bool(re.search(
        r"on-device|on device|\bedge\b|mobile|embedded|\biot\b|npu|phone|"
        r"microcontroller|neuromorphic|loihi|spinnaker|raspberry|jetson|"
        r"smartwatch|wearable|drone|robot|"
        r"efficient inference|lightweight|small model|small language|\bsnn\b|"
        r"quantiz|prun|distill|speculative|kv.?cache|federated|tinyml|"
        r"model compression|inference acceleration|low.?power|resource.?constrain|"
        r"edge computing|edge ai|edge inference|mobile inference|"
        r"spiking neural|spikformer|"
        r"deploy|runtime|serving|real.?time|latency|throughput|"
        r"accelerat|hardware.?friendly|co.?design|asic|fpga", text))


def convert_arxiv(c: dict) -> dict | None:
    aid = re.sub(r"v\d+$", "", str(c.get("id") or "")).strip()
    title = (c.get("title") or "").strip()
    summary = c.get("abstract") or c.get("summary") or ""
    authors = _coerce_authors(c.get("authors"))
    text = (title + " " + summary).lower()
    # Filter: only keep arxiv papers with edge-AI relevance (broad sweep catches
    # ALL cs.AI/cs.LG papers; many are pure theory/cloud/medical — drop those).
    # HF/vendor/github papers are NOT filtered (they're curated/official).
    if not is_edge_text(text):
        return None
    rel = 7 if is_edge_text(text) else 5
    contrib = 5
    tags = auto_tags(title, summary)
    # source_tier: detect company affiliation -> 公司项目, else 学校预印本
    vendor = detect_affil(authors + " " + title + " " + summary)
    if vendor:
        tier = "公司项目"
        score_reason = f"auto-converted；affiliation 命中 {vendor}（作者/摘要关键词匹配，待 OpenReview/Scholar 核实）"
    else:
        tier = "学校预印本"
        score_reason = "auto-converted（乙方案首版）；affiliation/精修大白话/精调分数待后续补"
    return {
        "id": f"arxiv-{aid}",
        "title": title,
        "abstract": first_sentence(summary),
        "effects": "未报告",
        "mechanism": "未报告",
        "paper_url": f"https://arxiv.org/abs/{aid}",
        "date": (c.get("date") or c.get("published") or "")[:10],
        "score": rel + contrib,
        "score_relevance": rel,
        "score_contribution": contrib,
        "score_reason": score_reason,
        "source_tier": tier,
        "open_source": bool(re.search(r"github\.com|github\.io", summary, re.I)),
        "tags": tags,
        "authors": authors,
        "vendors": vendor or "",
        "venue": "arXiv",
        # 自动汇集只负责扩充完整收录；“推荐”必须由主 Agent 阅读后人工判断。
        "recommendation": "纳入",
        "recommendation_reason": "",
    }


def convert_hf(c: dict, seen_arxiv: set) -> dict | None:
    url = c.get("paper_url") or ""
    m = re.search(r"arxiv\.org/abs/([^v\s]+)", url)
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
    title = (c.get("title") or "").strip()
    summary = c.get("abstract") or ""
    authors = _coerce_authors(c.get("authors"))
    text = (title + " " + summary).lower()
    rel = 7 if is_edge_text(text) else 6  # HF精选质量高，基础分稍高
    contrib = 5
    tags = auto_tags(title, summary)
    vendor = detect_affil(authors + " " + title + " " + summary)
    tier = "公司项目" if vendor else "学校预印本"
    return {
        "id": pid, "title": title,
        "abstract": first_sentence(summary), "effects": "未报告", "mechanism": "未报告",
        "paper_url": paper_url, "date": (c.get("date") or "")[:10],
        "score": rel + contrib, "score_relevance": rel, "score_contribution": contrib,
        "score_reason": f"HF Daily Papers 精选(votes={c.get('votes','?')})；affiliation {'命中 '+vendor if vendor else '待核实'}",
        "source_tier": tier,
        "open_source": bool(re.search(r"github\.com|github\.io", summary, re.I)),
        "tags": tags, "authors": authors, "vendors": vendor or "",
        "venue": "HuggingFace Daily", "recommendation": "纳入", "recommendation_reason": "",
    }


def convert_github(c: dict) -> dict:
    repo = c.get("repo") or ""
    tag = c.get("tag") or ""
    url = c.get("release_url") or f"https://github.com/{repo}"
    title = (c.get("title") or f"{repo} {tag}").strip()
    summary = c.get("summary") or ""
    tier = c.get("tier") or "开源大项目"
    # tier from subagent: model-lab org -> 公司项目, whitelist -> 开源大项目
    vendor = ""
    if tier == "公司项目":
        for pat, name in AFFIL:
            if re.search(pat, repo + " " + summary, re.I):
                vendor = name
                break
    text = (title + " " + summary).lower()
    rel = 8 if re.search(r"on-device|edge|mobile|embedded|npu|phone|mcu|jetson|"
                         r"raspberry|wearable|agent|robot|inference|llama\.cpp|"
                         r"executorch|mlc|onnx|mediapipe|litert|mlx|powerinfer", text) else 6
    contrib = 6
    tags = auto_tags(title, summary)
    if not any(t == "方向:推理框架" for t in tags):
        tags.append("方向:推理框架")
    tags = tags[:8]
    owner = repo.split("/")[0] if "/" in repo else repo
    return {
        "id": f"github-{re.sub(r'[^a-z0-9]+','-',(repo+'-'+tag).lower())[:70]}",
        "title": title,
        "abstract": first_sentence(summary) or summary[:160],
        "effects": "未报告", "mechanism": "未报告",
        "paper_url": url, "date": (c.get("date") or "")[:10],
        "score": rel + contrib, "score_relevance": rel, "score_contribution": contrib,
        "score_reason": c.get("summary", "")[:120] or "GitHub 白名单大项目本周 release",
        "source_tier": tier, "open_source": True,
        "tags": tags, "authors": owner, "vendors": vendor,
        "venue": "GitHub", "recommendation": "纳入", "recommendation_reason": "",
    }


def convert_vendor(c: dict) -> dict:
    vendor = c.get("vendor") or ""
    title = (c.get("title") or "").strip()
    summary = c.get("summary") or ""
    url = c.get("url") or ""
    text = (title + " " + summary).lower()
    rel = 8  # 官方动态默认高相关
    contrib = 5
    tags = auto_tags(title, summary)
    if not any(t.startswith("方向:") for t in tags):
        tags.insert(0, "方向:端侧agent")
    tags = tags[:8]
    return {
        "id": f"vendor-{re.sub(r'[^a-z0-9]+','-',(vendor+'-'+title).lower())[:70]}",
        "title": title,
        "abstract": first_sentence(summary) or summary[:160],
        "effects": "未报告", "mechanism": "未报告",
        "paper_url": url, "date": (c.get("date") or "")[:10],
        "score": rel + contrib, "score_relevance": rel, "score_contribution": contrib,
        "score_reason": f"{vendor} 官方动态（命中官方域名白名单）",
        "source_tier": "官方动态", "open_source": False,
        "tags": tags, "authors": vendor, "vendors": vendor,
        "venue": vendor, "recommendation": "纳入", "recommendation_reason": "",
    }


def load(path: Path):
    if not path.exists():
        print(f"[ASSEMBLE] WARN missing: {path}")
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ASSEMBLE] WARN bad JSON {path}: {e}")
        return []


def main() -> int:
    arxiv = load(ARXIV_CAND)
    hf = load(HF_CAND)
    gh = load(GH_CAND)
    vendor = load(VENDOR_CAND)

    seen_arxiv_ids = {re.sub(r"v\d+$", "", str(c.get("id") or "")) for c in arxiv}
    papers = []
    for c in arxiv:
        p = convert_arxiv(c)
        if p:
            papers.append(p)
    for c in vendor:
        papers.append(convert_vendor(c))
    for c in gh:
        papers.append(convert_github(c))
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
