#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Refresh data/github_trending_top20.json in one step.

Runs collect_github_trending (fetches trending + search API → _github_trending.json)
then converts to the top20 file the page reads. Called by the deploy flow
(server _deploy_to_ghpages) so trending auto-refreshes on each publish —
no longer relies on the main agent manually running it when the gate fails.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))

import collect_github_trending  # noqa: E402

collect_github_trending.main()  # writes data/_github_trending.json

src = ROOT / "data" / "_github_trending.json"
d = json.loads(src.read_text(encoding="utf-8"))
items = [x for x in d if x.get("source") == "search" and x.get("stars")]
items.sort(key=lambda x: x["stars"], reverse=True)
out = [
    {
        "rank": i + 1,
        "repo": x["repo"],
        "url": x["url"],
        "total": str(x["stars"]) + "★",
        "week": str(x["stars"]),
        "desc": x["desc"][:140],
    }
    for i, x in enumerate(items[:20])
]
dest = ROOT / "data" / "github_trending_top20.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[TRENDING] refreshed top20 -> {dest} · {len(out)} items, first: {out[0]['repo'] if out else 'NONE'}")
