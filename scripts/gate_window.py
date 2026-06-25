#!/usr/bin/env python3
"""gate 3: 每条 post 的 date 在过去一周窗口内。

cutoff = last_run - 7d（读 data/.last_run；never 则 now - 7d）。
post.date 必须 >= cutoff 且 <= today。超期或未来日期均报错。
退出码 0=全部在窗口内，1=有越界。
"""
import sys
from datetime import datetime, timedelta, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_common as gc

now = datetime.now()
last_run_path = gc.ROOT / "data" / ".last_run"
last = last_run_path.read_text(encoding="utf-8").strip()
if last == "never":
    cutoff = now - timedelta(days=7)
else:
    try:
        cutoff = datetime.fromisoformat(last) - timedelta(days=7)
    except ValueError:
        gc.err(f"data/.last_run invalid timestamp: {last!r} (expected ISO or 'never')")
        cutoff = now - timedelta(days=7)

cutoff_date = cutoff.date()
today = now.date()

for p in gc.list_posts():
    fm = gc.read_frontmatter(p)
    if fm is None:
        continue
    d = fm.get("date")
    if d is None:
        gc.err(f"{p.name}: missing date")
        continue
    if isinstance(d, datetime):
        post_date = d.date()
    elif isinstance(d, date):
        post_date = d
    else:
        try:
            post_date = datetime.fromisoformat(str(d)).date()
        except ValueError:
            gc.err(f"{p.name}: invalid date {d!r}")
            continue
    if post_date < cutoff_date or post_date > today:
        gc.err(f"{p.name}: date {post_date} outside window [{cutoff_date} .. {today}]")

gc.finish()
