# Readable Taxonomy Tabs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Chinese keywords, three product tabs, and human-readable summaries to the edge-agent radar.

**Architecture:** Extend the research run contract with `keywords` and `category`, keep the existing server-driven flow, and render the server page as a dense but readable radar table. The server continues to accept only validated research runs and the page still reads from `/api/papers`.

**Tech Stack:** Python validation scripts, SQLite storage, stdlib HTTP server, vanilla HTML/CSS/JS.

---

### Task 1: Documentation Contract

**Files:**
- Modify: `docs/product-specs/SPEC.md`
- Modify: `docs/agent-guide/output-contract.md`
- Modify: `docs/agent-guide/validation-rules.md`
- Modify: `docs/agent-guide/research-prompt.md`
- Modify: `docs/site/api-contract.md`
- Modify: `.agents/skills/edge-agent-research-pipeline/SKILL.md`

- [ ] Add `keywords: string[]` and `category: "应用" | "框架" | "算法"` to the research run contract.
- [ ] Require Chinese-first writing for `abstract`, `effects`, `mechanism`, `score_reason`, and `keywords`.
- [ ] Define the three tabs: 应用 for real user/device scenarios, 框架 for runtime/benchmark/system architecture, 算法 for RL/memory/distillation/UQ/planning/tool-use methods.
- [ ] Document that detailed technical explanation belongs in wiki, while the page fields should be short and easy to scan.

### Task 2: Validation And Storage

**Files:**
- Modify: `scripts/research_run.py`
- Modify: `server/storage.py`
- Modify: `scripts/test_research_pipeline.py`

- [ ] Make `keywords` and `category` required fields.
- [ ] Validate `category` against exactly `应用`, `框架`, `算法`.
- [ ] Validate `keywords` as 1 to 8 non-empty strings.
- [ ] Store keywords as JSON text in SQLite and return them as arrays from the API.
- [ ] Add tests for valid keywords/category, invalid category, empty keywords, and API round-trip.

### Task 3: Page Rendering

**Files:**
- Modify: `server/page.py`

- [ ] Replace the wide technical table with a readable table/list hybrid.
- [ ] Add tabs for `应用 / 框架 / 算法` with counts.
- [ ] Render `keywords` as compact chip labels.
- [ ] Rename visible sections to `这是什么`, `有什么结果`, `怎么做到的`.
- [ ] Keep editable `洞察人` and `wiki链接`.
- [ ] Preserve official-major-vendor-first sorting inside each tab.

### Task 4: Current Run Data

**Files:**
- Modify: `research_runs/run-20260626-current-window.json`

- [ ] Add Chinese keywords and category to each of the 12 current items.
- [ ] Rewrite page-facing `abstract`, `effects`, `mechanism`, and `score_reason` into short Chinese explanations.
- [ ] Validate and publish the updated run to the local server.

### Task 5: Verification

**Files:**
- No new files.

- [ ] Run `python scripts/validate_research_run.py research_runs/run-20260626-current-window.json`.
- [ ] Run `python scripts/test_research_pipeline.py`.
- [ ] Run `python scripts/test_build.py`.
- [ ] Run `python scripts/gate_all.py`.
- [ ] Run `git diff --check`.
- [ ] Verify `http://127.0.0.1:8001/api/papers` returns `keywords` arrays and `category` values.
