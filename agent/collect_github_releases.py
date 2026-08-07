#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect audited GitHub releases and major code drops for weekly research.

Release tags alone miss projects that publish a large initial codebase into an
older repository. This collector also inspects in-window commits and keeps only
substantive code drops, while preserving the same whitelist boundary.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from research_collection import (
    REQUIRED_GITHUB_PROJECTS,
    collection_window,
    parse_collection_date,
    update_source_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_runs" / "candidates-github.json"
UA = "edge-agent-github-release-collector/1.0"
TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")


def fetch_json(url: str, timeout: int = 30):
    headers = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def is_major_code_drop(commit: dict) -> bool:
    """A large first/public code event, not an ordinary maintenance commit."""
    files = commit.get("files") if isinstance(commit, dict) else None
    stats = commit.get("stats") if isinstance(commit, dict) else None
    additions = stats.get("additions", 0) if isinstance(stats, dict) else 0
    return isinstance(files, list) and len(files) >= 20 and int(additions or 0) >= 500


def find_major_code_drops(
    commits: list[dict],
    detail_fetch,
    *,
    max_inspected: int = 8,
    max_matches: int = 1,
) -> list[tuple[dict, dict]]:
    """Inspect a bounded prefix and stop once enough major events are found."""
    matches: list[tuple[dict, dict]] = []
    for item in commits[:max_inspected]:
        sha = str(item.get("sha") or "")
        if not sha:
            continue
        detail = detail_fetch(sha) or {}
        if is_major_code_drop(detail):
            matches.append((item, detail))
            if len(matches) >= max_matches:
                break
    return matches


def collect_project(repo: str, window_start: str, window_end: str) -> list[dict]:
    candidates: list[dict] = []
    releases = fetch_json(f"https://api.github.com/repos/{repo}/releases?per_page=100") or []
    for release in releases if isinstance(releases, list) else []:
        published = str(release.get("published_at") or release.get("created_at") or "")[:10]
        if not (window_start <= published <= window_end):
            continue
        candidates.append({
            "repo": repo,
            "tag": str(release.get("tag_name") or "release"),
            "title": str(release.get("name") or release.get("tag_name") or repo),
            "summary": str(release.get("body") or "")[:1200],
            "release_url": str(release.get("html_url") or f"https://github.com/{repo}/releases"),
            "date": published,
            "event_type": "release",
        })

    params = urllib.parse.urlencode({"since": f"{window_start}T00:00:00Z", "until": f"{window_end}T23:59:59Z", "per_page": 20})
    commits = fetch_json(f"https://api.github.com/repos/{repo}/commits?{params}") or []
    commit_items = commits if isinstance(commits, list) else []
    major_drops = find_major_code_drops(
        commit_items,
        lambda sha: fetch_json(f"https://api.github.com/repos/{repo}/commits/{sha}"),
    )
    for item, detail in major_drops:
        sha = str(item.get("sha") or "")
        commit_info = item.get("commit") if isinstance(item.get("commit"), dict) else {}
        author = commit_info.get("author") if isinstance(commit_info.get("author"), dict) else {}
        committed = str(author.get("date") or "")[:10]
        if not (window_start <= committed <= window_end):
            continue
        stats = detail.get("stats") if isinstance(detail.get("stats"), dict) else {}
        message = str(commit_info.get("message") or "Major code drop").splitlines()[0]
        candidates.append({
            "repo": repo,
            "tag": sha[:7],
            "title": f"{repo}: {message}",
            "summary": f"本周大规模公开代码：{len(detail.get('files') or [])} 个文件，新增 {int(stats.get('additions') or 0)} 行。",
            "release_url": str(item.get("html_url") or f"https://github.com/{repo}/commit/{sha}"),
            "date": committed,
            "event_type": "major_commit",
        })
    return candidates


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Collect whitelist GitHub releases and major code drops.")
    parser.add_argument("--today", help="Override collection date as YYYY-MM-DD")
    parser.add_argument("--manifest", default=str(ROOT / "research_runs" / "collection-manifest.json"))
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args(argv)
    run_date = parse_collection_date(args.today)
    start, end, _ = collection_window(run_date)

    all_candidates: list[dict] = []
    checked: list[str] = []
    for repo in sorted(REQUIRED_GITHUB_PROJECTS):
        all_candidates.extend(collect_project(repo, start.isoformat(), end.isoformat()))
        checked.append(repo)

    dedup = {}
    for candidate in all_candidates:
        dedup[(candidate["repo"], candidate["release_url"])] = candidate
    candidates = sorted(dedup.values(), key=lambda item: (item["date"], item["repo"]), reverse=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    update_source_coverage(
        args.manifest,
        "github",
        {
            "status": "complete",
            "candidate_count": len(candidates),
            "release_projects_checked": checked,
        },
        today=run_date,
    )
    print(f"# collected {len(candidates)} GitHub release/major-code candidates {start}..{end}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
