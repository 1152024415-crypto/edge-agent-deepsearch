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
