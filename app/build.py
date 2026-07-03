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


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def fetch_json(url: str):
    return json.loads(fetch_text(url))


def rewrite_index(html: str, papers_payload, weekly_payload, trending_payload=None) -> str:
    """Inline papers + weekly + trending data and rewrite /paper/<id> links to relative paths."""
    # 1) Inline the payloads as globals; replace the runtime fetch +
    #    json parse with a read of that global so the list renders without API.
    inline = (
        '<script>window.__PAPERS__ = '
        + json.dumps(papers_payload, ensure_ascii=False)
        + ';window.__WEEKLY__ = '
        + json.dumps(weekly_payload, ensure_ascii=False)
        + ';window.__TRENDING__ = '
        + json.dumps(trending_payload or {"items": []}, ensure_ascii=False)
        + ';</script>'
    )
    html = re.sub(
        r'const\s+res\s*=\s*await\s+fetch\("/api/papers"\)\s*;\s*'
        r'const\s+data\s*=\s*await\s+res\.json\(\)\s*;',
        'const data = window.__PAPERS__;',
        html,
    )
    html = re.sub(
        r'const\s+wr\s*=\s*await\s+fetch\("/api/weekly"\)\s*;\s*'
        r'const\s+w\s*=\s*await\s+wr\.json\(\)\s*;',
        'const w = window.__WEEKLY__;',
        html,
    )
    # Inject the inline data script just before the page's first <script>.
    html = html.replace("<script>", inline + "\n    <script>", 1)
    # 2) Rewrite /paper/<id> links (including the JS template literal form
    #    href="/paper/${escapeAttr(p.id)}") to relative paper/<id>.html.
    html = re.sub(r'href="/paper/([^"]+)"', r'href="paper/\1.html"', html)
    return html


def rewrite_detail(html: str) -> str:
    """Fix the back link so detail pages return to the static index."""
    return html.replace('href="/"', 'href="../index.html"')


def mirror(server: str, site: Path = SITE) -> int:
    """Mirror ``server`` (root + /api/papers + /paper/<id>) into ``site``."""
    # NOTE: we intentionally do NOT rmtree the site — the paper/ archive is
    # preserved so that users still viewing last week's cached index (whose
    # links point at last week's paper ids) don't get 404s after this week's
    # deploy. New paper pages overwrite same-id pages; old ones persist as
    # an archive. Only index.html is overwritten each build.
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

    index_html = rewrite_index(fetch_text(f"{server}/"), papers_payload, weekly_payload, trending_payload)
    (site / "index.html").write_text(index_html, encoding="utf-8")
    print(f"[BUILD] index.html ({len(papers)} papers inlined)")

    for p in papers:
        pid = str(p.get("id") or "")
        if not pid:
            continue
        detail_html = rewrite_detail(fetch_text(f"{server}/paper/{pid}"))
        (site / "paper" / f"{pid}.html").write_text(detail_html, encoding="utf-8")
        print(f"[BUILD] paper/{pid}.html")

    print(f"[BUILD] done: index.html + {len(papers)} detail page(s) under {site}")
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
    args = parser.parse_args(argv)
    return mirror(args.server)


if __name__ == "__main__":
    sys.exit(main())
