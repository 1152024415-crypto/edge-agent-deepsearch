#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the research-notes page: ingest markdown collections into site/notes/.

Reads data/notes_sources.json (list of {name, slug, source, desc}). For each
collection, copies its *.md + image files into site/notes/<slug>/, extracts a
title (first H1) per note, and renders site/notes.html from app/notes_page.py
with the manifest inlined. Re-run after editing sources or adding a collection.
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # for `from app.notes_page import NOTES_HTML`
SITE = ROOT / "site"
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp"}


def note_title(md_path: Path) -> str:
    try:
        for line in md_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if s.startswith("# "):
                return s[2:].strip()
    except Exception:
        pass
    return md_path.stem


def ingest_collection(coll: dict) -> dict:
    src = Path(coll["source"])
    slug = coll["slug"]
    dest = SITE / "notes" / slug
    dest.mkdir(parents=True, exist_ok=True)
    notes = []
    if not src.exists():
        print(f"[NOTES] WARN source missing: {src}")
        return {**coll, "notes": []}
    for p in sorted(src.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() == ".md":
            shutil.copy2(p, dest / p.name)
            notes.append({"title": note_title(p), "file": p.name})
        elif p.suffix.lower() in IMG_EXT:
            shutil.copy2(p, dest / p.name)
    print(f"[NOTES] {slug}: {len(notes)} note(s), images copied -> {dest}")
    return {"name": coll.get("name", slug), "slug": slug,
            "desc": coll.get("desc", ""), "notes": notes}


def render_notes_html(manifest):
    from app.notes_page import NOTES_HTML
    return NOTES_HTML.replace("window.__NOTES__ || []",
                              json.dumps(manifest, ensure_ascii=False))


def main():
    cfg = ROOT / "data" / "notes_sources.json"
    sources = json.loads(cfg.read_text(encoding="utf-8"))
    manifest = [ingest_collection(c) for c in sources]
    # drop empty collections (source missing) from manifest
    manifest = [c for c in manifest if c["notes"]]
    (ROOT / "data" / "notes_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "notes.html").write_text(render_notes_html(manifest), encoding="utf-8")
    total = sum(len(c["notes"]) for c in manifest)
    print(f"[NOTES] wrote site/notes.html · {len(manifest)} collection(s), {total} note(s)")


if __name__ == "__main__":
    main()
