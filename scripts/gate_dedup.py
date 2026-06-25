#!/usr/bin/env python3
"""gate 2: index.json entries 与 content/posts/ 文件双向一一对应。

任一方向缺失即错误（index 有但无 post 文件 / post 有但 index 未收录）。
退出码 0=一致，1=不一致。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_common as gc

idx = gc.read_index()
entries = idx.get("entries", [])

idx_ids, idx_slugs = {}, {}
for e in entries:
    if e.get("id"):
        idx_ids[e["id"]] = e
    if e.get("slug"):
        idx_slugs[e["slug"]] = e

post_ids, post_slugs = {}, {}
for p in gc.list_posts():
    fm = gc.read_frontmatter(p)
    if fm is None:
        continue
    if fm.get("id"):
        post_ids[fm["id"]] = p.name
    if fm.get("slug"):
        post_slugs[fm["slug"]] = p.name

for _id, e in idx_ids.items():
    if _id not in post_ids:
        gc.err(f"index.json entry id={_id!r} (title={e.get('title')!r}) not found in any post")
for _id, fname in post_ids.items():
    if _id not in idx_ids:
        gc.err(f"post {fname} id={_id!r} not in index.json")
for slug, fname in post_slugs.items():
    if slug not in idx_slugs:
        gc.err(f"post {fname} slug={slug!r} not in index.json")
for slug, e in idx_slugs.items():
    if slug not in post_slugs:
        gc.err(f"index.json entry slug={slug!r} not found in any post")

gc.finish()
