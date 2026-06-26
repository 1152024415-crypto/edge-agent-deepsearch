# GitHub Pages Paper Table Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the large card page with a high-density static GitHub Pages paper table.

**Architecture:** Keep the Python SSG. `scripts/build.py` reads `content/papers/*.md`, embeds paper data into the generated HTML, and ships a small vanilla JS controller for sorting, row expansion, and local insight edits.

**Tech Stack:** Python stdlib, YAML frontmatter helper, static HTML/CSS/vanilla JS.

---

### Task 1: Build Smoke Tests

**Files:**
- Modify: `scripts/test_build.py`

- [ ] Add assertions that the generated page includes sort buttons for score and date.
- [ ] Add assertions that the generated page renders a dense list/table container and paper rows.
- [ ] Add assertions that detail fields are present but can live in expandable rows.
- [ ] Add assertions that local insight editing controls are present.
- [ ] Run `python scripts/test_build.py` and verify it fails before changing `scripts/build.py`.

### Task 2: Static Page Rendering

**Files:**
- Modify: `scripts/build.py`

- [ ] Change rendering from large article cards to a compact table-like list.
- [ ] Default sort embedded data by `score` descending.
- [ ] Include row fields: score, date, title, source, vendors, recommendation, insight person, paper link, wiki link.
- [ ] Include expandable details: abstract, effects, mechanism, contribution, review hint.
- [ ] Filter non-paper entries out of the paper list so `source_type != 学术论文` does not appear on the paper page.

### Task 3: Client Interactions

**Files:**
- Modify: `scripts/build.py`

- [ ] Add vanilla JS for score/date sorting.
- [ ] Add row expand/collapse using buttons.
- [ ] Add insight person and wiki URL inputs.
- [ ] On save, try `POST /api/insights`; if unavailable, save to `localStorage`.
- [ ] Mark local-only saves as “本地未同步”.

### Task 4: Verification

**Files:**
- No new production files.

- [ ] Run `python scripts/test_build.py`.
- [ ] Run `python scripts/gate_all.py`.
- [ ] Run `git diff --check`.
- [ ] Verify in browser at desktop and mobile widths that the page shows multiple rows per screen and no horizontal overflow on mobile.
