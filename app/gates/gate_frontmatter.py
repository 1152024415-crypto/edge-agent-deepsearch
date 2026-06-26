#!/usr/bin/env python3
"""gate 1: 校验 content/papers/*.md 的 frontmatter 符合 frontmatter.schema.json。

退出码 0=全部合规，1=有错误。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_common as gc
from jsonschema import Draft202012Validator

SCHEMA_PATH = gc.ROOT / "app" / "frontmatter.schema.json"
schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
validator = Draft202012Validator(schema)

DIM_KEYS = ("score_relevance", "score_vendor", "score_contribution", "score_quality", "score_recency")

from datetime import date as _date, datetime as _dt

posts = gc.list_posts()

for p in posts:
    fm = gc.read_frontmatter(p)
    if fm is None:
        gc.err(f"{p.name}: no frontmatter block (missing leading '---...---')")
        continue
    # yaml 把 2026-06-24 解析成 date 对象；jsonschema format 校验需 string，转回 ISO 字符串
    fm_norm = dict(fm)
    if isinstance(fm_norm.get("date"), (_date, _dt)):
        fm_norm["date"] = fm_norm["date"].isoformat()
    for e in validator.iter_errors(fm_norm):
        loc = "/".join(str(x) for x in e.absolute_path) or "(root)"
        gc.err(f"{p.name}: {e.message} (at {loc})")
    total = fm.get("score")
    parts = [fm.get(k, 0) or 0 for k in DIM_KEYS]
    if total is not None and sum(parts) != total:
        gc.err(f"{p.name}: score({total}) != sum of dimensions({sum(parts)})")

gc.finish()
