#!/usr/bin/env python3
"""Release gate — runs over the BUILT site/ + data/ artifacts, BEFORE deploy.

Catches the failure modes that shipped before by operating on real artifacts
(not the legacy frontmatter content dir, which is empty for this project):

1. contract   — __PAPERS__ must be a {"papers":[...]} dict (page.py reads
                 data.papers); no runtime server globals (window.__WEEKS__ = ...)
                 leaked into the static page.
2. links 200   — every inlined paper id + manifest past week has a built
                 site/paper/<id>.html / site/week/<label>.html (no 404s).
3. editorial   — weekly_summary highlights must be editorial news (≥5 external
                 URLs), not paper-list duplicates; paper_id highlights must resolve.
4. vendor tier — current week must have ≥1 官方动态 (vendor blogs collected);
                 0 is a process alarm requiring per-vendor evidence on disk.

Use: python app/gates/gate_release.py [--root DIR]
Pre-deploy, after `python app/build.py`. Exit 0 = ship; 1 = blocked.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MIN_EXTERNAL_HIGHLIGHTS = 5

_PAPERS_RE = re.compile(r"window\.__PAPERS__\s*=\s*(.+?);\s*window\.__WEEKLY__", re.S)
# render_page inlines with NO spaces around '=': `window.__WEEKS__=[`. The server.py
# `/` route injects WITH spaces: `window.__WEEKS__ = [`. The space-form is the runtime
# injection that must NOT survive into a static page (render_page strips it).
_SERVER_INJECT_RE = re.compile(r"window\.__WEEKS__\s+=\s+\[")


def _err(errors, msg):
    errors.append(msg)


def check_contract(root: Path, errors: list) -> None:
    idx = root / "site" / "index.html"
    if not idx.exists():
        _err(errors, "site/index.html missing — run app/build.py first")
        return
    html = idx.read_text(encoding="utf-8")
    m = _PAPERS_RE.search(html)
    if not m:
        _err(errors, "site/index.html: window.__PAPERS__ not found — build inlining broken")
    else:
        try:
            val = json.loads(m.group(1))
            if not (isinstance(val, dict) and isinstance(val.get("papers"), list)):
                _err(errors, "site/index.html: __PAPERS__ must be a {\"papers\":[...]} dict "
                             "(page.py reads data.papers; a bare list renders 0 signals)")
        except Exception as e:
            _err(errors, f"site/index.html: __PAPERS__ not valid JSON ({e})")
    # server injects `window.__WEEKS__ = [...]` (space-form); render_page must strip it.
    # NB: render_page's own inline is `window.__WEEKS__=[` (no spaces), so the space-form
    # only appears if the server's runtime block leaked through.
    if _SERVER_INJECT_RE.search(html):
        _err(errors, "site/index.html: runtime server globals (window.__WEEKS__ = ...) leaked "
                     "into static page — render_page must strip the server injection block")


def _paper_ids_from_index(root: Path) -> list:
    idx = root / "site" / "index.html"
    if not idx.exists():
        return []
    m = _PAPERS_RE.search(idx.read_text(encoding="utf-8"))
    if not m:
        return []
    try:
        val = json.loads(m.group(1))
        return [p.get("id") for p in (val.get("papers", []) if isinstance(val, dict) else val)
                if isinstance(p, dict) and p.get("id")]
    except Exception:
        return []


def check_links(root: Path, errors: list) -> None:
    paper_dir = root / "site" / "paper"
    for pid in _paper_ids_from_index(root):
        if not (paper_dir / f"{pid}.html").exists():
            _err(errors, f"site/paper/{pid}.html missing — row + highlight links to it would 404")
    # past-week archive pages must exist
    manifest = _read_json(root / "data" / "weeks" / "manifest.json", default=[])
    for e in manifest:
        if e.get("current"):
            continue
        label = e.get("label")
        if label and not (root / "site" / "week" / f"{label}.html").exists():
            _err(errors, f"site/week/{label}.html missing — switcher link to that week would 404")
    for nav in ("index.html", "notes.html"):
        if not (root / "site" / nav).exists():
            _err(errors, f"site/{nav} missing — nav link would 404")


def check_highlights(root: Path, errors: list) -> None:
    ws = _read_json(root / "data" / "weekly_summary.json", default=None)
    if ws is None:
        _err(errors, "data/weekly_summary.json missing")
        return
    hl = ws.get("highlights", []) or []
    external = [h for h in hl if h.get("url")]
    if len(external) < MIN_EXTERNAL_HIGHLIGHTS:
        _err(errors, f"weekly_summary highlights: only {len(external)} external-news URL(s) "
                     f"(need ≥{MIN_EXTERNAL_HIGHLIGHTS}). Highlights must be EDITORIAL news "
                     f"(vendor blogs/dynamics), not paper-list duplicates of the run.")
    paper_dir = root / "site" / "paper"
    for h in hl:
        pid = h.get("paper_id")
        if (not h.get("url")) and pid:
            if not (paper_dir / f"{pid}.html").exists():
                _err(errors, f"highlight paper_id {pid} → site/paper/{pid}.html missing (404)")


def check_vendor_tier(root: Path, errors: list) -> None:
    manifest = _read_json(root / "data" / "weeks" / "manifest.json", default=[])
    current = next((e for e in manifest if e.get("current")), None)
    if not current:
        _err(errors, "manifest: no current week entry — run app/build.py")
        return
    label = current["label"]
    arch = _read_json(root / "data" / "weeks" / f"{label}.json", default=None)
    if arch is None:
        _err(errors, f"data/weeks/{label}.json missing — current week archive not built")
        return
    papers = arch.get("papers", []) or []
    vendor_n = sum(1 for p in papers if p.get("source_tier") == "官方动态")
    if vendor_n == 0:
        ev = root / "data" / "weeks" / f"{label}-no-vendor.md"
        if not ev.exists():
            _err(errors, f"0 官方动态 in {label} — vendor blogs not collected. research-prompt "
                         f"mandates 18-vendor + model-lab blog search. Either collect them, or "
                         f"acknowledge per-vendor evidence at data/weeks/{label}-no-vendor.md.")


def check_trending_freshness(root: Path, errors: list) -> None:
    """github_trending_top20.json must be refreshed within 7 days of deploy.

    Catches the 07-15 regression: the run + weekly_summary were refreshed but
    data/github_trending_top20.json was left at 07-03 (12 days stale), so the
    page's trending section showed two-week-old repos. mtime > 7 days = FAIL.
    """
    import os
    import time
    tp = root / "data" / "github_trending_top20.json"
    if not tp.exists():
        _err(errors, "data/github_trending_top20.json missing — run agent/collect_github_trending.py "
                     "before deploy (trending section would be empty/stale)")
        return
    age_sec = time.time() - tp.stat().st_mtime
    if age_sec > 7 * 86400:
        import datetime
        days_old = int(age_sec // 86400)
        _err(errors, f"data/github_trending_top20.json is {days_old}d old (>7d) — trending section "
                     f"shows stale repos. Run agent/collect_github_trending.py to refresh.")


def check_snn_page(root: Path, errors: list) -> None:
    """site/snn.html must exist — the SNN insight page nav link points at it."""
    if not (root / "site" / "snn.html").exists():
        _err(errors, "site/snn.html missing — run agent/build_snn.py (SNN 洞察 nav 链接会 404)")


def check_waic_page(root: Path, errors: list) -> None:
    """site/waic.html must exist — the WAIC insight page nav link points at it."""
    if not (root / "site" / "waic.html").exists():
        _err(errors, "site/waic.html missing — run agent/build_waic.py (WAIC 洞察 nav 链接会 404)")


def _read_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def run_all(root: Path) -> list:
    errors = []
    check_contract(root, errors)
    check_links(root, errors)
    check_highlights(root, errors)
    check_vendor_tier(root, errors)
    check_trending_freshness(root, errors)
    check_snn_page(root, errors)
    check_waic_page(root, errors)
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Pre-deploy release gate over site/ + data/.")
    ap.add_argument("--root", default=str(ROOT), help="Project root (default: repo root)")
    args = ap.parse_args(argv)
    errors = run_all(Path(args.root))
    if errors:
        print(f"[FAIL] gate_release: {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[OK] gate_release passed — contract/links/editorial/vendor-tier all clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
