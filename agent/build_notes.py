#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the research-notes page: ingest markdown collections into site/notes/.

Reads data/notes_sources.json (list of {name, slug, source, desc}). For each
collection, copies its *.md + image files into site/notes/<slug>/, extracts a
title (first H1) per note, and renders site/notes.html from app/notes_page.py
with the manifest inlined. Re-run after editing sources or adding a collection.
"""
import json
import os
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


def html_title(html_path: Path) -> str:
    """Extract <title> from an HTML file; fall back to filename stem."""
    try:
        import re
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"<title[^>]*>([^<]+)</title>", text, re.I)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return html_path.stem


def ingest_collection(coll: dict) -> dict:
    src = Path(coll["source"])
    slug = coll["slug"]
    dest = SITE / "notes" / slug
    # Clean dest before ingest so stale files from a previous (possibly
    # broken) build don't accumulate — e.g. a run that picked up an unrelated
    # subproject's .md leaves hundreds of junk files that bloat the deploy and
    # slow the Pages build.
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)
    notes = []
    if not src.exists():
        print(f"[NOTES] WARN source missing: {src}")
        return {**coll, "notes": []}
    # Notes = top-level *.md; images = images/ OR assets/ subdir (recursive
    # within) + top-level image files. Do NOT descend into arbitrary subdirs —
    # a note source dir may hold an unrelated subproject (e.g. DSpark's
    # deepspec/ with its own .venv + hundreds of .md) which would pollute the
    # collection and crash on Windows symlinks. assets/ is Obsidian's default
    # image dir (e.g. AMD note's slide webp). os.walk not needed here — rglob
    # under a known image dir is safe.
    SKIP_DIRS = {".venv", ".git", "node_modules", "__pycache__"}
    # Optional per-file whitelist: if coll has "files", only ingest those;
    # otherwise ingest all top-level *.md + *.html.
    files_whitelist = coll.get("files")
    if files_whitelist:
        note_files = sorted(p for p in src.glob("*") if p.name in files_whitelist and p.suffix.lower() in (".md", ".html"))
    else:
        note_files = sorted(list(src.glob("*.md")) + list(src.glob("*.html")))
    img_files = []
    for img_dir_name in ("images", "assets"):
        img_dir = src / img_dir_name
        if img_dir.is_dir():
            img_files += sorted(p for p in img_dir.rglob("*") if p.is_file())
    img_files += sorted(p for p in src.glob("*") if p.is_file() and p.suffix.lower() in IMG_EXT)
    for p in note_files:
        shutil.copy2(p, dest / p.name)
        if p.suffix.lower() == ".html":
            notes.append({"title": html_title(p), "file": p.name, "type": "html"})
        else:
            notes.append({"title": note_title(p), "file": p.name, "type": "md"})
    for p in img_files:
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            shutil.copy2(p, dest / p.name)
        except OSError:
            pass  # skip inaccessible files (broken symlinks under images/)
    # Also copy assets/ preserving subdir so HTML notes' relative paths
    # (e.g. assets/x.png) resolve. The flat copies above are for md notes
    # (notes_page rewrites img src to basename); HTML pages in an iframe
    # resolve relative to their own location (dest/xxx.html → dest/assets/x.png).
    for img_dir_name in ("images", "assets"):
        img_dir = src / img_dir_name
        if img_dir.is_dir():
            dest_img = dest / img_dir_name
            if dest_img.exists():
                shutil.rmtree(dest_img, ignore_errors=True)
            shutil.copytree(img_dir, dest_img, dirs_exist_ok=True)
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
