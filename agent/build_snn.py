#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the SNN insight page: copy the curated markdown into site/snn/ and
render site/snn.html from app.snn_page.SNN_HTML (client-side fetches the md).

Re-run after editing data/snn-insight.md.
Override paths via SNN_SRC (the .md) and SNN_SITE (the site/ dir) for tests.
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEFAULT_SRC = ROOT / "data" / "snn-insight.md"
DEFAULT_SITE = ROOT / "site"


def main() -> int:
    src = Path(os.environ.get("SNN_SRC") or DEFAULT_SRC)
    site = Path(os.environ.get("SNN_SITE") or DEFAULT_SITE)
    if not src.exists():
        print(f"[SNN] WARN source missing: {src}")
        return 1
    site.mkdir(parents=True, exist_ok=True)
    (site / "snn").mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, site / "snn" / "SNN-insight.md")
    from app.snn_page import SNN_HTML
    (site / "snn.html").write_text(SNN_HTML, encoding="utf-8")
    print(f"[SNN] wrote site/snn.html + site/snn/SNN-insight.md (src {src.stat().st_size}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
