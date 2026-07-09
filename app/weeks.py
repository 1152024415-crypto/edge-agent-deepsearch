"""Week archive / manifest / parse logic for the research-radar site.

A "week" is a frozen snapshot of one weekly cycle: the papers list, the
weekly summary (overview + highlights), and the trending list. This module
owns the data model and disk layout under ``data/weeks/``; both the static
builder (app.build) and the runtime server (app.server) call into it.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Env-overridable so subprocess builds in tests can write to a tmp dir without
# touching the real committed archive under data/weeks/. Set EDGE_WEEKS_DIR.
WEEKS_DIR = Path(os.environ.get("EDGE_WEEKS_DIR") or (ROOT / "data" / "weeks"))

_RANGE_RE = re.compile(r"(\d{2})-(\d{2})~(\d{2})-(\d{2})")


def parse_week_meta(overview: str, fallback_iso: str) -> dict:
    """Derive {label, title, range} from the weekly overview text.

    Parses the first ``MM-DD~MM-DD`` occurrence; the year is disambiguated
    from ``fallback_iso`` (a YYYY-MM-DD string, typically today). If the start
    month-day is later in the year than fallback's month-day, start belongs to
    the previous year (e.g. a Dec-26~01-02 window read in January). If end's
    month-day is earlier than start's (a cross-year window), end belongs to the
    year after start. If no range is found, falls back to ``fallback_iso``.
    """
    year = int(fallback_iso[:4])
    today_md = (int(fallback_iso[5:7]), int(fallback_iso[8:10]))
    m = _RANGE_RE.search(overview or "")
    if not m:
        return {
            "label": fallback_iso,
            "title": fallback_iso,
            "range": {"start": fallback_iso, "end": fallback_iso},
        }
    sm, sd, em, ed = m.groups()
    start_md = (int(sm), int(sd))
    end_md = (int(em), int(ed))
    start_year = year - 1 if start_md > today_md else year
    end_year = start_year + 1 if end_md < start_md else start_year
    start = f"{start_year:04d}-{sm}-{sd}"
    end = f"{end_year:04d}-{em}-{ed}"
    title = f"{sm}-{sd}~{em}-{ed}"
    return {"label": start, "title": title, "range": {"start": start, "end": end}}


def archive_path(label: str) -> Path:
    return WEEKS_DIR / f"{label}.json"


def read_archive(label: str) -> dict | None:
    p = archive_path(label)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def write_archive(meta: dict, papers: list, weekly: dict, trending: dict) -> None:
    WEEKS_DIR.mkdir(parents=True, exist_ok=True)
    rec = {
        "label": meta["label"],
        "title": meta["title"],
        "range": meta["range"],
        "papers": papers,
        "weekly": weekly,
        "trending": trending,
    }
    archive_path(meta["label"]).write_text(
        json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")


def build_manifest(current_label: str) -> list[dict]:
    """Scan data/weeks/*.json, sort by range.start desc, mark current; persist."""
    WEEKS_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for p in sorted(WEEKS_DIR.glob("*.json")):
        if p.name == "manifest.json":
            continue
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        entries.append({
            "label": rec["label"],
            "title": rec.get("title") or rec["label"],
            "range": rec.get("range") or {"start": rec["label"], "end": rec["label"]},
            "current": rec["label"] == current_label,
        })
    entries.sort(key=lambda e: e["range"]["start"], reverse=True)
    (WEEKS_DIR / "manifest.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    return entries


def read_manifest() -> list[dict]:
    p = WEEKS_DIR / "manifest.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def attach_hrefs(manifest: list[dict], weeks_base: str, runtime: bool) -> list[dict]:
    """Add an `href` to each manifest entry for the switcher to navigate to."""
    out = []
    for e in manifest:
        if runtime:
            href = "/" if e.get("current") else f"/week/{e['label']}"
        else:
            href = weeks_base + "index.html" if e.get("current") else f"{weeks_base}week/{e['label']}.html"
        out.append({**e, "href": href})
    return out


_PAPERS_RE = re.compile(r"window\.__PAPERS__\s*=\s*(\[.*?\]);\s*window\.__WEEKLY__", re.S)
_WEEKLY_RE = re.compile(r"window\.__WEEKLY__\s*=\s*(\{.*?\});\s*window\.__TRENDING__", re.S)
_TRENDING_RE = re.compile(r"window\.__TRENDING__\s*=\s*(\{.*?\});</script>", re.S)


def extract_payloads_from_html(html: str) -> dict:
    """Pull the three inlined payloads back out of a built index.html (for backfill)."""
    def grab(rx, default):
        m = rx.search(html)
        if not m:
            return default
        try:
            return json.loads(m.group(1))
        except Exception:
            return default
    return {
        "papers": grab(_PAPERS_RE, []),
        "weekly": grab(_WEEKLY_RE, {"overview": "", "highlights": []}),
        "trending": grab(_TRENDING_RE, {"items": []}),
    }
