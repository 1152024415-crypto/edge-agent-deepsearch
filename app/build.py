#!/usr/bin/env python3
"""Mirror a running display server into a static site/.

This produces a GitHub-Pages-deployable snapshot under ``site/``:

  /            -> site/index.html         (papers JSON inlined, links rewritten)
  /paper/<id>  -> site/paper/<id>.html    (back link rewritten to ../index.html)

The list page (app/page.py) normally fetches ``/api/papers`` at runtime; on a
static host there is no such API, so we inline the papers payload as
``window.__PAPERS__`` and replace the fetch with a read of that global. Detail
pages are already server-rendered HTML (app/server.py render_detail), so we
just mirror them and fix the back link.

Only this file is changed; app/page.py, app/server.py, app/storage.py are left
untouched. Run while the server is up, e.g. ``python app/build.py --server
http://127.0.0.1:8001``.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path

DEFAULT_SERVER = "http://127.0.0.1:8001"
ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

sys.path.insert(0, str(ROOT))
from app import weeks as weeks_mod  # noqa: E402  (weeks is also a param name)


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def fetch_json(url: str):
    return json.loads(fetch_text(url))


def render_page(html, papers, weekly, trending, weeks, week_label, weeks_base, runtime):
    """Inline all payloads + switcher globals into page.py's HTML, rewrite fetches
    to read globals, and rewrite /paper/<id> links to relative {weeks_base}paper/<id>.html.

    ``weeks`` already carries per-entry ``href`` (see app.weeks.attach_hrefs).
    ``week_label`` is this page's label, or None for the current-week page.
    """
    inline = (
        '<script>window.__PAPERS__='
        + json.dumps(papers, ensure_ascii=False)
        + ';window.__WEEKLY__='
        + json.dumps(weekly, ensure_ascii=False)
        + ';window.__TRENDING__='
        + json.dumps(trending, ensure_ascii=False)
        + ';window.__WEEKS__='
        + json.dumps(weeks, ensure_ascii=False)
        + ';window.__WEEK_LABEL__='
        + json.dumps(week_label, ensure_ascii=False)
        + ';window.__WEEKS_BASE__='
        + json.dumps(weeks_base, ensure_ascii=False)
        + ';</script>'
    )
    html = re.sub(
        r'const\s+res\s*=\s*await\s*fetch\("/api/papers"\)\s*;\s*'
        r'const\s+data\s*=\s*await\s*res\.json\(\)\s*;',
        'const data = window.__PAPERS__;',
        html,
    )
    html = re.sub(
        r'const\s+wr\s*=\s*await\s*fetch\("/api/weekly"\)\s*;\s*'
        r'const\s+w\s*=\s*await\s+wr\.json\(\)\s*;',
        'const w = window.__WEEKLY__;',
        html,
    )
    html = html.replace("<script>", inline + "\n    <script>", 1)
    # rewrite /paper/<id> links (incl. JS template-literal form) to relative
    # static paths — but only for static builds; runtime pages keep absolute
    # /paper/<id> links so they hit the live detail route.
    if not runtime:
        html = re.sub(r'href="/paper/([^"]+)"', r'href="' + weeks_base + r'paper/\1.html"', html)
        html = re.sub(r'href="notes\.html"', f'href="{weeks_base}notes.html"', html)
    return html


def rewrite_detail(html: str) -> str:
    """Fix the back link so detail pages return to the static index."""
    return html.replace('href="/"', 'href="../index.html"')


def mirror(server: str, site: Path = SITE) -> int:
    """Mirror server into site/: write current-week archive + manifest, render
    index.html (current) and site/week/<label>.html (each past week)."""
    # NOTE: we intentionally do NOT rmtree the site — the paper/ archive is
    # preserved so that users still viewing last week's cached index (whose
    # links point at last week's paper ids) don't get 404s after this week's
    # deploy. New paper pages overwrite same-id pages; old ones persist as
    # an archive. index.html is overwritten each build.
    site.mkdir(parents=True, exist_ok=True)
    (site / "paper").mkdir(parents=True, exist_ok=True)

    print(f"[BUILD] mirroring {server} -> {site}")
    papers_payload = fetch_json(f"{server}/api/papers")
    papers = list(papers_payload.get("papers") or [])
    try:
        weekly_payload = fetch_json(f"{server}/api/weekly")
    except Exception:
        weekly_payload = {"overview": "", "highlights": []}
    try:
        trending_payload = fetch_json(f"{server}/api/trending")
    except Exception:
        trending_payload = {"items": []}

    import datetime
    fallback_iso = datetime.date.today().isoformat()
    meta = weeks_mod.parse_week_meta(weekly_payload.get("overview", ""), fallback_iso)
    current_label = meta["label"]

    # 1) archive current week + manifest
    weeks_mod.write_archive(meta, papers, weekly_payload, trending_payload)
    manifest = weeks_mod.build_manifest(current_label)

    # Fetch the server-rendered index shell once; reused for index + past weeks.
    index_template = fetch_text(f"{server}/")

    # 2) render site/index.html (current) — weeks_base="" (root)
    index_html = render_page(
        index_template,
        papers, weekly_payload, trending_payload,
        weeks_mod.attach_hrefs(manifest, weeks_base="", runtime=False),
        week_label=None, weeks_base="", runtime=False,
    )
    (site / "index.html").write_text(index_html, encoding="utf-8")
    print(f"[BUILD] index.html ({len(papers)} papers, week={current_label})")

    # 3) render site/week/<label>.html for every PAST week
    for entry in manifest:
        if entry["current"]:
            continue
        rec = weeks_mod.read_archive(entry["label"])
        if not rec:
            continue
        (site / "week").mkdir(parents=True, exist_ok=True)
        page = render_page(
            index_template,
            rec["papers"], rec["weekly"], rec["trending"],
            weeks_mod.attach_hrefs(manifest, weeks_base="../", runtime=False),
            week_label=entry["label"], weeks_base="../", runtime=False,
        )
        (site / "week" / f"{entry['label']}.html").write_text(page, encoding="utf-8")
        print(f"[BUILD] week/{entry['label']}.html")

    # 4) detail pages (unchanged from before)
    for p in papers:
        pid = str(p.get("id") or "")
        if not pid:
            continue
        detail_html = rewrite_detail(fetch_text(f"{server}/paper/{pid}"))
        (site / "paper" / f"{pid}.html").write_text(detail_html, encoding="utf-8")

    print(f"[BUILD] done: index.html + {len(papers)} detail + "
          f"{sum(1 for e in manifest if not e['current'])} week archive page(s)")
    return 0


def backfill(site: Path = SITE) -> int:
    """One-time: extract the inlined payloads from an existing site/index.html
    into data/weeks/<label>.json so the first new-week build has a past week to render.
    """
    idx = site / "index.html"
    if not idx.exists():
        print("[BACKFILL] no site/index.html to backfill from — nothing to do")
        return 0
    html = idx.read_text(encoding="utf-8")
    payloads = weeks_mod.extract_payloads_from_html(html)
    import datetime
    fallback_iso = datetime.date.today().isoformat()
    meta = weeks_mod.parse_week_meta(
        payloads["weekly"].get("overview", ""), fallback_iso)
    weeks_mod.write_archive(meta, payloads["papers"], payloads["weekly"], payloads["trending"])
    weeks_mod.build_manifest(meta["label"])
    print(f"[BACKFILL] wrote data/weeks/{meta['label']}.json from existing index.html")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Mirror a running display server into a static site/."
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER,
        help=f"Display server base URL (default: {DEFAULT_SERVER}).",
    )
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Backfill data/weeks/ from an existing site/index.html (one-time).",
    )
    args = parser.parse_args(argv)
    if args.backfill:
        return backfill()
    return mirror(args.server)


if __name__ == "__main__":
    sys.exit(main())
