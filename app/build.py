#!/usr/bin/env python3
"""Mirror the local display server (http://127.0.0.1:8001) into a static site/.

This produces a GitHub-Pages-deployable snapshot under ``site/``:

  /            -> site/index.html         (papers JSON inlined, links rewritten)
  /paper/<id>  -> site/paper/<id>.html    (back link rewritten to ../index.html)

The list page (app/page.py) normally fetches ``/api/papers`` at runtime; on a
static host there is no such API, so we inline the papers payload as
``window.__PAPERS__`` and replace the fetch with a read of that global. Detail
pages are already server-rendered HTML (app/server.py render_detail), so we
just mirror them and fix the back link.

Only this file is changed; app/page.py, app/server.py, app/storage.py are left
untouched. Run while the server is up on 127.0.0.1:8001.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path

SERVER = "http://127.0.0.1:8001"
ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def fetch_json(url: str):
    return json.loads(fetch_text(url))


def rewrite_index(html: str, papers_payload) -> str:
    """Inline papers data and rewrite /paper/<id> links to relative paths."""
    # 1) Inline the papers payload as a global; replace the runtime fetch +
    #    json parse with a read of that global so the list renders without API.
    inline = (
        '<script>window.__PAPERS__ = '
        + json.dumps(papers_payload, ensure_ascii=False)
        + ';</script>'
    )
    html = re.sub(
        r'const\s+res\s*=\s*await\s+fetch\("/api/papers"\)\s*;\s*'
        r'const\s+data\s*=\s*await\s+res\.json\(\)\s*;',
        'const data = window.__PAPERS__;',
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


def main() -> int:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "paper").mkdir(parents=True, exist_ok=True)

    print(f"[BUILD] mirroring {SERVER} -> {SITE}")
    papers_payload = fetch_json(f"{SERVER}/api/papers")
    papers = list(papers_payload.get("papers") or [])

    index_html = rewrite_index(fetch_text(f"{SERVER}/"), papers_payload)
    (SITE / "index.html").write_text(index_html, encoding="utf-8")
    print(f"[BUILD] index.html ({len(papers)} papers inlined)")

    for p in papers:
        pid = str(p.get("id") or "")
        if not pid:
            continue
        detail_html = rewrite_detail(fetch_text(f"{SERVER}/paper/{pid}"))
        (SITE / "paper" / f"{pid}.html").write_text(detail_html, encoding="utf-8")
        print(f"[BUILD] paper/{pid}.html")

    print(f"[BUILD] done: index.html + {len(papers)} detail page(s) under {SITE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
