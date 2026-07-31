---
name: add-notes-content
description: Use when adding research notes (.md or .html) to the 调研笔记 page on the edge-agent radar site. Covers adding a collection, ingesting markdown/HTML files, building, and deploying to GitHub Pages.
---

# Add Notes Content (.md / .html)

## When to Use

When you need to add a research note (markdown or pre-built HTML) to the 调研笔记 (notes) page at `https://1152024415-crypto.github.io/edge-agent-deepsearch/notes.html`.

## Architecture

The notes system has 3 parts:

1. **`data/notes_sources.json`** — registry of note collections. Each entry: `{name, slug, source, desc}`. The `source` is a local directory path containing `.md` and/or `.html` files + `images/` or `assets/` subdirs.

2. **`agent/build_notes.py`** — ingests each collection: copies top-level `*.md` + `*.html` to `site/notes/<slug>/`, copies `images/` + `assets/` images (flat for .md, preserving subdir for .html), and renders `site/notes.html` from `app/notes_page.py` with the manifest inlined.

3. **`app/notes_page.py`** — the notes page template (HTML + CSS + JS). Renders markdown via marked.js + KaTeX + mermaid. For `.html` notes, loads in an `<iframe>` (HTML's own styles/JS render fully). Left sidebar (collapsible) shows collections + notes; right sidebar shows TOC (auto-built from H2/H3 for .md notes; shows "HTML 页面" for .html notes).

## How to Add a Note

### Step 1: Add Collection to `data/notes_sources.json`

```json
{
  "name": "Display Name",
  "slug": "kebab-slug",
  "source": "C:/path/to/source/dir",
  "desc": "Short description shown in sidebar"
}
```

The source dir should contain:
- `*.md` files (markdown notes — rendered by marked.js + KaTeX + mermaid)
- `*.html` files (self-contained HTML pages — loaded in iframe)
- `images/` or `assets/` subdir (images — copied flat for .md, preserving subdir for .html)
- `.obsidian/`, `.venv/`, `node_modules/` etc. are auto-skipped

### Step 2: Build

```bash
python agent/build_notes.py
```

This ingests all collections, copies files to `site/notes/<slug>/`, and renders `site/notes.html`.

### Step 3: Verify Locally

```bash
cd site && python -m http.server 8092
# Open http://127.0.0.1:8092/notes.html
# Click the new note → verify it renders (.md: markdown+KaTeX+mermaid; .html: iframe)
```

### Step 4: Deploy

```bash
git add data/notes_sources.json data/notes_manifest.json agent/build_notes.py app/notes_page.py
git commit -m "feat(notes): add <collection name> (<N> collections/<M> notes)"
git push origin master

# Deploy to gh-pages
git fetch origin gh-pages
TMP=$(mktemp -d) && git worktree add --detach "$TMP" origin/gh-pages
cp -r D:/proj/edge_agent/site/* "$TMP"/
cd "$TMP" && git add -A && git commit -m "deploy: notes add <collection name>" && git push origin HEAD:gh-pages
cd D:/proj/edge_agent && git worktree remove --force "$TMP"
```

### Step 5: Verify Live

Wait ~75s for GitHub Pages build, then:
```
https://1152024415-crypto.github.io/edge-agent-deepsearch/notes.html
```
Click the new note → verify it renders.

## .md vs .html Notes

| Feature | .md notes | .html notes |
|---|---|---|
| Rendering | marked.js + KaTeX ($...$) + mermaid (```mermaid) | iframe (HTML's own styles/JS) |
| TOC | Auto-built from H2/H3, click-to-scroll, current-section highlight | "HTML 页面" (no TOC) |
| Copy button | Copies raw markdown source | Disabled (LAST_RAW empty) |
| Image paths | Rewritten to `notes/<slug>/<basename>` (flat) | Preserved `assets/x.png` (subdir) |
| Title | First `# H1` in markdown | `<title>` tag in HTML |
| Sidebar collapse | ✓ | ✓ (same as .md) |

## Notes

- `build_notes.py` cleans `site/notes/<slug>/` before each ingest (rmtree + recreate) — stale files don't accumulate.
- `build_notes.py` only ingests TOP-LEVEL `*.md` and `*.html` (not recursive into subdirs). Subdirs like `deepspec/` with `.venv` are skipped.
- `assets/` is copied BOTH flat (for .md image rewrite) AND preserving subdir (for .html relative paths).
- The notes page supports: collapsible left sidebar, right TOC, KaTeX math (with protectMath to prevent marked.js mangling `$$`), mermaid diagrams, copy-raw-markdown button, HTML iframe notes.
- Gate `check_snn_page` / `check_waic_page` in `gate_release.py` ensures `site/snn.html` and `site/waic.html` exist. `site/notes.html` is checked by `check_links` (nav link resolves).
