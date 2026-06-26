#!/usr/bin/env python3
"""Gate 3: every content/papers item must be within the current 7-day window."""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_common as gc


today = date.today()
cutoff_date = today - timedelta(days=7)


def parse_post_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)).date()


for p in gc.list_papers():
    fm = gc.read_frontmatter(p)
    if fm is None:
        continue
    raw_date = fm.get("date")
    if raw_date is None:
        gc.err(f"{p.name}: missing date")
        continue
    try:
        post_date = parse_post_date(raw_date)
    except ValueError:
        gc.err(f"{p.name}: invalid date {raw_date!r}")
        continue
    if post_date < cutoff_date or post_date > today:
        gc.err(f"{p.name}: date {post_date} outside window [{cutoff_date} .. {today}]")

gc.finish()
