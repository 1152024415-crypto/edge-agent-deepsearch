#!/usr/bin/env python3
"""Merge enriched fields (abstract/effects/score) from data/_enriched_*.json into the run JSON."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    run_path = ROOT / "research_runs" / "run-20260627-real2.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))

    enriched: dict[str, dict] = {}
    for n in (1, 2, 3, 4):
        p = ROOT / "data" / f"_enriched_{n}.json"
        if not p.exists():
            print(f"missing {p}")
            continue
        try:
            arr = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"{p}: invalid JSON: {e}")
            continue
        for item in arr:
            if isinstance(item, dict) and "id" in item:
                enriched[item["id"]] = item

    updated = 0
    for paper in run["papers"]:
        e = enriched.get(paper["id"])
        if not e:
            continue
        paper["abstract"] = e.get("abstract", paper["abstract"])
        paper["effects"] = e.get("effects", paper["effects"])
        rel = int(e.get("score_relevance", paper["score_relevance"]))
        con = int(e.get("score_contribution", paper["score_contribution"]))
        paper["score_relevance"] = rel
        paper["score_contribution"] = con
        paper["score"] = rel + con
        paper["score_reason"] = "精修（中文大白话+真实 effects+区分度分数）；affiliation 待核实"
        updated += 1

    run_path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"merged {updated}/{len(run['papers'])} papers; enriched pool={len(enriched)}")
    # score 分布
    from collections import Counter
    print("score 分布:", dict(Counter(p["score"] for p in run["papers"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
