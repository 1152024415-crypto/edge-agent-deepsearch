#!/usr/bin/env python3
"""gate 4: frontmatter vendors 字段值在 data/vendors.yaml 白名单内。

vendors 为空允许（纯学术无大厂关联）；但出现非白名单值即报错（防瞎标）。
退出码 0=全部合规，1=有越界值。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_common as gc

vy = gc.read_vendors()
valid = gc.vendor_names(vy)

for p in gc.list_posts():
    fm = gc.read_frontmatter(p)
    if fm is None:
        continue
    vs = fm.get("vendors") or []
    for v in vs:
        if v not in valid:
            gc.err(f"{p.name}: vendor {v!r} not in whitelist (valid: {sorted(valid)})")

gc.finish()
