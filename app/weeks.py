"""Week archive / manifest / parse logic for the research-radar site.

A "week" is a frozen snapshot of one weekly cycle: the papers list, the
weekly summary (overview + highlights), and the trending list. This module
owns the data model and disk layout under ``data/weeks/``; both the static
builder (app.build) and the runtime server (app.server) call into it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEEKS_DIR = ROOT / "data" / "weeks"

_RANGE_RE = re.compile(r"(\d{2})-(\d{2})~(\d{2})-(\d{2})")


def parse_week_meta(overview: str, fallback_iso: str) -> dict:
    """Derive {label, title, range} from the weekly overview text.

    Parses the first ``MM-DD~MM-DD`` occurrence; year taken from
    ``fallback_iso`` (a YYYY-MM-DD string). If no range is found, falls
    back to ``fallback_iso`` for every field.
    """
    year = fallback_iso[:4]
    m = _RANGE_RE.search(overview or "")
    if not m:
        return {
            "label": fallback_iso,
            "title": fallback_iso,
            "range": {"start": fallback_iso, "end": fallback_iso},
        }
    sm, sd, em, ed = m.groups()
    start = f"{year}-{sm}-{sd}"
    end = f"{year}-{em}-{ed}"
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
