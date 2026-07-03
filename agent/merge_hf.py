#!/usr/bin/env python3
"""Merge data/_hf_entries.json into the run, dedup by arxiv_id + normalized title."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def main() -> int:
    run_path = ROOT / "research_runs" / "run-20260627-real2.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))

    existing_arxiv = {x["id"].replace("arxiv-", "") for x in run["papers"] if x["id"].startswith("arxiv-")}
    existing_titles = {norm_title(x["title"]) for x in run["papers"]}

    hf_path = ROOT / "data" / "_hf_entries.json"
    if not hf_path.exists():
        print(f"missing {hf_path}")
        return 1
    hf = json.loads(hf_path.read_text(encoding="utf-8"))

    added = 0
    for e in hf:
        aid = e["id"].replace("arxiv-", "")
        if aid in existing_arxiv:
            continue
        if norm_title(e["title"]) in existing_titles:
            continue
        run["papers"].append(e)
        existing_arxiv.add(aid)
        existing_titles.add(norm_title(e["title"]))
        added += 1

    run_path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"merged {added} HF entries (of {len(hf)}); total now {len(run['papers'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
