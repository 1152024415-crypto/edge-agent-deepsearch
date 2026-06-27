---
name: edge-agent-research-pipeline
description: Use when working in the edge_agent repository, onboarding a new code agent, running paper research, validating research_runs JSON, publishing results to the server, or deciding whether content belongs in the端侧 AI Agent论文雷达.
---

# Edge Agent Research Pipeline

## Overview

This project is an agent-driven paper radar for edge-side AI agents. The main code agent coordinates research subagents, validates their structured paper results, publishes accepted results to the server, and verifies that the display refreshes from server data.

## First Read

When this skill triggers, read these files before editing or publishing:

1. `AGENTS.md`
2. `docs/agent-guide/main-agent-workflow.md`
3. `docs/agent-guide/research-prompt.md`
4. `docs/agent-guide/output-contract.md`
5. `docs/agent-guide/validation-rules.md`
6. `docs/agent-guide/detail-prompt.md`
7. `docs/site/api-contract.md`

## Quick Start: Run a Research Cycle

Follow these 11 steps end to end to run one research cycle and see it on the page. They mirror `docs/harness.md` section 3 and the `AGENTS.md` workflow. Do not skip steps.

1. **Read the strong-entry docs first**: `AGENTS.md` → `docs/harness.md` → this SKILL. Also read `docs/agent-guide/research-prompt.md`, `output-contract.md`, and `validation-rules.md`. Skipping these means missing the standard and fabricating dead links.

2. **Check the time window**: read the last-research timestamp in `data/.last_run`. Only run if ≥7 days have passed; if less than 7 days, say "本周已调研" and stop. This prevents duplicate runs and passing off old runs as this week's.

3. **Spawn the research subagent**: the prompt must inject the full text of `docs/agent-guide/research-prompt.md` plus the hard constraints (major-vendor first, official-domain whitelist, 7-day window, three-way category, keywords, no padding, plain-language summary). **The main agent must not write its own simplified prompt**; a simplified prompt lets the subagent drop the standard and fabricate 404 links.

4. **Save the output**: the subagent returns 10 to 20 structured paper JSON items; the main agent saves it as `research_runs/run-YYYYMMDD-HHMMSS.json`. The subagent only produces JSON; it does not edit code, pages, or the server.

5. **Validate**: run `python agent/validate_research_run.py research_runs/<run_id>.json`. This checks structure, the 7-day window, the 5-dimension score sum, and HTTP dead links; 404 and unreachable URLs are blocked automatically. If validation fails, fix or drop the bad items. **No padding**: if you cannot find an official URL, drop it; if major-vendor content is thin, collect fewer items.

6. **Spot-check major-vendor items**: before publishing, fetch every URL with `is_major_vendor_official=true` and compare the page content against the title and abstract. A URL that opens is not the same as a URL whose content matches; drop mismatches.

7. **Start the server** (if not running):

   ```powershell
   python app/server.py --host 127.0.0.1 --port 8001
   ```

8. **Publish**:

   ```powershell
   python agent/publish_results.py research_runs/<run_id>.json --server http://127.0.0.1:8001
   ```

9. **See it on the page**: open `http://127.0.0.1:8001/` in a browser. Papers and official updates are split into two tabs, with major-vendor official entries sorted first; click a title to open the detail page. After publish the detail page shows "整理中" until the detail agent runs. The server's `GET /api/papers` returns only the latest run.

10. **(Optional) Spawn the detail agent**: the prompt must inject the full text of `docs/agent-guide/detail-prompt.md`; it produces a 6-segment detail (research background / contributions / method / experiments / edge-agent significance / limitations) for each paper and writes it via `POST /api/paper-detail`. Once done, the detail page refreshes to show the full analysis.

11. **Close the loop**: update `data/.last_run` to this research time (ISO 8601, e.g. `2026-06-26T15:00:00+08:00`). Fold this week's mistakes into `AGENTS.md` lessons, `docs/agent-guide/validation-rules.md`, and `research-prompt.md`; rely on the repo, not memory. Finally run `python tests/test_research_pipeline.py`, `python tests/test_build.py`, and `python app/gates/gate_all.py` to confirm the harness is healthy.

## Project Boundaries

| Part | Responsibility |
|---|---|
| Main code agent | Spawn research agents, save `research_runs/*.json`, validate, publish, verify |
| Research subagent | Search/read papers and return structured JSON only |
| Detail subagent (optional) | Fetch paper sources and produce 6-segment detail per paper via `detail-prompt.md` |
| Scripts | Validate and publish agent output deterministically |
| `app/server.py` | HTTP routes and server entry point |
| `app/storage.py` | SQLite paper storage and queries |
| `app/page.py` | HTML shell that refreshes from `/api/papers` |
| Static build | Fallback only; not the final deployment path |

## Main Workflow

1. Ask research subagents for 10 to 20 recent real papers or official major-vendor updates using `docs/agent-guide/research-prompt.md`.
2. Save the result as `research_runs/run-YYYYMMDD-HHMMSS.json`.
3. Validate it:

```powershell
python agent/validate_research_run.py research_runs/run-YYYYMMDD-HHMMSS.json
```

4. Start the server if needed:

```powershell
python app/server.py --host 127.0.0.1 --port 8000
```

5. Publish accepted results:

```powershell
python agent/publish_results.py research_runs/run-YYYYMMDD-HHMMSS.json --server http://127.0.0.1:8000
```

6. Verify:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/papers
```

## Hard Rules

- Non-paper entries are allowed only when they are official major-vendor technical blogs or official product announcements.
- Unofficial blogs, news, GitHub releases, social posts, and secondary commentary are not allowed.
- Official major-vendor entries should sort before ordinary academic papers.
- Do not use old sample data to make the page look populated.
- Only accept papers from the current 7-day window.
- `paper_url` must match the paper or official source title and abstract/summary.
- `effects` must come from the paper or official source; write `未报告` if the source does not report effects.
- Every item must include Chinese-first `keywords` and one `category`: `应用`, `框架`, or `算法`.
- Page-facing `abstract`, `effects`, `mechanism`, and `score_reason` must be short, readable Chinese. Put long technical analysis in the wiki.
- Research subagents do not edit code, docs, server files, or static pages.
- The server does not search the web; it only accepts validated research runs.
- When spawning a research subagent, the prompt must inject the full text of `docs/agent-guide/research-prompt.md` plus the hard constraints. The main agent must not write its own simplified prompt; a simplified prompt lets the subagent drop the standard and fabricate dead links.
- `validate_research_run.py` runs HTTP dead-link checks on every `paper_url`; 404 or unreachable links are blocked automatically. Offline networks warn and skip, they do not fail.
- No padding: if this week's major-vendor official content is thin, collect fewer items. Do not pass academic papers off as major-vendor official, and do not pad with uncertain links.
- When spawning the detail agent, the prompt must inject the full text of `docs/agent-guide/detail-prompt.md`. The main agent must not write its own simplified prompt. Detail output must not contain English double quotes; they break JSON encoding.
- 调研 agent 搜索论文优先用 arXiv MCP（`search_papers`），websearch 补充大厂官网。
- The full weekly loop lives in `docs/harness.md` section 3; this skill is the entry point, harness is the overview.

## Verification Before Completion

Run these before claiming the repo is ready:

```powershell
python tests/test_research_pipeline.py
python tests/test_build.py
python app/gates/gate_all.py
git diff --check
```

Windows line-ending warnings from `git diff --check` are acceptable; whitespace errors are not.
