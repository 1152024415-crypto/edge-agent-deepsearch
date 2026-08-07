#!/usr/bin/env python3
"""Rebase human-edited weekly copy onto a freshly collected research run.

The fresh run remains authoritative for source URLs, dates, candidate lineage,
and the embedded collection manifest.  Reader-facing editorial fields can be
carried forward by stable paper id.  Direct edge-Agent status is always reset
and must be explicitly restored through the decisions file.
"""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime
from pathlib import Path


EDITORIAL_FIELDS = {
    "title_zh",
    "abstract",
    "effects",
    "mechanism",
    "score",
    "score_relevance",
    "score_contribution",
    "score_reason",
    "source_tier",
    "open_source",
    "tags",
    "authors",
    "vendors",
    "affiliation_evidence_url",
    "venue",
    "recommendation",
    "recommendation_reason",
}
DIRECT_TAG = "方向:端侧agent"
FALLBACK_TAG = "方向:高效推理"
DIRECT_SCOPES = {"手机", "PC", "其他端侧"}


def _normalize_edge_agent_fields(paper: dict) -> None:
    scope = str(paper.get("edge_agent_scope") or "非端侧Agent")
    tags = [tag for tag in paper.get("tags", []) if tag != DIRECT_TAG]
    if scope in DIRECT_SCOPES:
        tags.insert(0, DIRECT_TAG)
    else:
        scope = "非端侧Agent"
        paper["edge_agent_evidence"] = ""
    paper["edge_agent_scope"] = scope
    paper["tags"] = list(dict.fromkeys(tags))[:8] or [FALLBACK_TAG]


def rebase_curated_run(fresh: dict, previous: dict, decisions: dict) -> dict:
    fresh_by_id = {paper["id"]: paper for paper in fresh.get("papers", [])}
    previous_by_id = {paper["id"]: paper for paper in previous.get("papers", [])}
    drop_ids = set(decisions.get("drop_ids", []))
    selected_ids = [paper["id"] for paper in previous.get("papers", [])]
    selected_ids.extend(decisions.get("include_ids", []))
    selected_ids = list(dict.fromkeys(selected_ids))
    overrides = decisions.get("overrides", {})

    papers = []
    for paper_id in selected_ids:
        if paper_id in drop_ids or paper_id not in fresh_by_id:
            continue
        paper = copy.deepcopy(fresh_by_id[paper_id])
        previous_paper = previous_by_id.get(paper_id, {})
        for field in EDITORIAL_FIELDS:
            if field in previous_paper:
                paper[field] = copy.deepcopy(previous_paper[field])

        # A previous keyword hit is never evidence of a real direct edge Agent.
        paper["edge_agent_scope"] = "非端侧Agent"
        paper["edge_agent_evidence"] = ""
        paper.update(copy.deepcopy(overrides.get(paper_id, {})))
        _normalize_edge_agent_fields(paper)
        paper["score"] = int(paper["score_relevance"]) + int(paper["score_contribution"])
        papers.append(paper)

    result = {
        "run_id": decisions["run_id"],
        "generated_at": datetime.now().astimezone().isoformat(),
        "papers": papers,
    }
    if "collection_manifest" in fresh:
        result["collection_manifest"] = copy.deepcopy(fresh["collection_manifest"])
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fresh_run")
    parser.add_argument("previous_editorial_run")
    parser.add_argument("decisions")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    def load(path: str) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    fresh = load(args.fresh_run)
    previous = load(args.previous_editorial_run)
    decisions = load(args.decisions)
    result = rebase_curated_run(fresh, previous, decisions)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    previous_ids = {paper["id"] for paper in previous.get("papers", [])}
    fresh_ids = {paper["id"] for paper in fresh.get("papers", [])}
    missing = sorted(previous_ids - fresh_ids)
    print(f"rebased {len(result['papers'])} papers -> {out}")
    if missing:
        print(f"dropped {len(missing)} stale editorial ids not present in fresh collection")
        for paper_id in missing:
            print(f"  - {paper_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
