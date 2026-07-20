#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the WAIC insight page: copy the curated markdown into site/waic/ and
render site/waic.html from app.waic_page.WAIC_HTML (client-side fetches the md).

Re-run after editing data/waic-insight.md.
Override paths via WAIC_SRC (the .md) and WAIC_SITE (the site/ dir) for tests.
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEFAULT_SRC = ROOT / "data" / "waic-insight.md"
DEFAULT_SITE = ROOT / "site"


def main() -> int:
    src = Path(os.environ.get("WAIC_SRC") or DEFAULT_SRC)
    site = Path(os.environ.get("WAIC_SITE") or DEFAULT_SITE)
    if not src.exists():
        print(f"[WAIC] WARN source missing: {src}")
        return 1
    site.mkdir(parents=True, exist_ok=True)
    (site / "waic").mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, site / "waic" / "WAIC-insight.md")
    from app.waic_page import WAIC_HTML
    (site / "waic.html").write_text(WAIC_HTML, encoding="utf-8")
    print(f"[WAIC] wrote site/waic.html + site/waic/WAIC-insight.md (src {src.stat().st_size}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
