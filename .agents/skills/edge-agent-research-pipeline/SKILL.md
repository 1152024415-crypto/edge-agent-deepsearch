---
name: edge-agent-research-pipeline
description: Use when working in the edge_agent repository, onboarding a new code agent, running paper research, validating research_runs JSON, publishing results to the server, or deciding whether content belongs in the端侧 AI Agent论文雷达.
---

# Edge Agent Research Pipeline

## Overview

This project is an agent-driven radar for edge-side AI agents. The main code agent coordinates research subagents that broadly collect papers / official dynamics / open-source project updates via MCP, the main agent filters + scores + tags them, validates the structured results, publishes to the server, and the page refreshes from server data.

## First Read

When this skill triggers, read these files before editing or publishing:

1. `AGENTS.md`
2. `docs/harness.md`
3. `docs/agent-guide/main-agent-workflow.md`
4. `docs/agent-guide/research-prompt.md`
5. `docs/agent-guide/output-contract.md`
6. `docs/agent-guide/validation-rules.md`
7. `docs/references/mcp-setup.md`
8. `docs/site/api-contract.md`

## Schema (方案 B, must match code)

- 2-dimension score: `score` = `score_relevance`(0-10) + `score_contribution`(0-10), max 20.
- `source_tier` facet: `官方动态` / `公司项目` / `学校顶会` / `学校预印本` / `开源大项目` (replaces old source_type + is_major_vendor_official).
- `tags`: 1-8 tags from `data/tags.yaml` (multi-label, one work can carry many).
- `open_source`: bool facet.
- `date`: must be within the past 7 days; for arXiv URLs validate cross-checks the real submitted date.
- No `detail` / 6-segment deep analysis — the detail agent is discontinued. Detail page shows short summary + tags + source link.

## Quick Start: Run a Research Cycle

Follow these steps end to end. They mirror `docs/harness.md` section 3 and `AGENTS.md`. Do not skip.

1. **Read the strong-entry docs first** (see First Read above). Skipping these means missing the standard and fabricating dead links.
2. **Check the time window**: read `data/.last_run`. Only run if ≥7 days passed; if less, say "本周已调研" and stop. The collection window is the past 7 days.
3. **Spawn the research subagent**: the prompt must inject the full text of `docs/agent-guide/research-prompt.md` plus the hard constraints. **The main agent must not write its own simplified prompt.** The subagent collects broadly via arXiv MCP + HuggingFace MCP + GitHub MCP + websearch (see `docs/references/mcp-setup.md`). No hard quantity target — collect as many qualified items as there are (adaptive: broaden/rewrite a query if it returns too few). **The subagent must report per-vendor blog-check results** (which of the 18 vendors + model labs were checked, in-window posts found), not just "0 官方动态" — 0 requires evidence, not assertion.
4. **Save the output**: the main agent filters + scores + tags the candidates (not delegated) and saves all qualified papers as `research_runs/run-YYYYMMDD-HHMMSS.json` (no padding, no hard cap — the list is lightweight, just titles + short summary + tags). The subagent only produces JSON; it does not edit code, pages, or the server.
5. **Validate**: `python agent/validate_research_run.py research_runs/<run_id>.json`. Checks structure, 7-day window, 2-dim score sum, source_tier, tags taxonomy, official-domain / github-URL rules, HTTP dead links, **arXiv submitted-date cross-check**, and cross-run dedup warning.
6. **Spot-check**: before publishing, fetch every `source_tier=官方动态` and `source_tier=开源大项目` URL and compare page content vs title/abstract. Drop mismatches.
7. **Write the editorial weekly_summary**: `data/weekly_summary.json` is an **independent editorial product**, NOT a slice of the run. `highlights` must be editorial news (vendor blogs/dynamics/industry events with **external URLs**, ≥5). Do NOT fill highlights with `paper_id` links to the run's top papers — that duplicates the paper list. Write from the `官方动态` tier + judgment. If `官方动态` count is 0, you have NOT collected vendor blogs — go back to step 3 and collect them, or write per-vendor evidence to `data/weeks/<label>-no-vendor.md`.
8. **Start the server** (if not running): `python app/server.py --host 127.0.0.1 --port 8001`
9. **Publish**: `python agent/publish_results.py research_runs/<run_id>.json --server http://127.0.0.1:8001` (writes `data/.last_run_papers.json` for next-run dedup + triggers gh-pages deploy).
10. **See it on the page** (do NOT skip — assertIn tests don't catch functional regressions): open `http://127.0.0.1:8001/` (or the built `site/index.html`), and with chrome-devtools **click every link type** — row, weekly-highlight, week-switcher (both directions), back-link, notes — each must resolve to 200 content, not 404. Compare highlights to last week: are they editorial news (external URLs), or paper-list duplicates?
11. **Run the release gate** (hard blocker): `python app/gates/gate_all.py`. `gate_release.py` checks the built `site/` + `data/` for: __PAPERS__ contract (dict, no runtime injection), internal-link 200s (no 404 detail/week pages), editorial highlights (≥5 external URLs, not paper duplicates), and ≥1 官动态 (else per-vendor evidence file). **If gate_release FAILs, do not deploy.**
12. **Close the loop**: update `data/.last_run` to this research time (ISO 8601). Fold this week's mistakes into `AGENTS.md` lessons, `validation-rules.md`, and `research-prompt.md`.

## Project Boundaries

| Part | Responsibility |
|---|---|
| Main code agent | Spawn research agents, filter + score + tag candidates, save `research_runs/*.json`, validate, publish, verify |
| Research subagent | Collect broadly via MCP + websearch, return structured JSON only |
| Scripts | Validate and publish agent output deterministically |
| `app/server.py` | HTTP routes and server entry point |
| `app/storage.py` | SQLite paper storage and queries |
| `app/page.py` | HTML shell that refreshes from `/api/papers` |
| Static build | Fallback only; not the final deployment path |

## Hard Rules

- Broad collection via arXiv MCP + HuggingFace Daily Papers MCP + GitHub MCP + websearch (config: `docs/references/mcp-setup.md`, project-level `.mcp.json`).
- Topic boundary (B 档): edge-side AI; general techniques count only if the authors mention on-device/edge/mobile/embedded. Pure cloud work is excluded.
- Filter out pure GUI agents (screen-tap / GUI automation / screen parsing) unless there is notable non-GUI innovation.
- Open-source entries: only industry-recognized big projects in `docs/references/big-projects-whitelist.md`, with a `github.com` URL. No small repos.
- Official-vendor entries (`source_tier=官方动态`) must use an official domain; unofficial blogs / news / GitHub releases / social / secondary commentary are excluded.
- `date` must come from source metadata (arXiv submitted date); validate cross-checks arXiv URLs. Do not re-date old papers into the window.
- 7-day window; no old sample data to pad the page.
- `paper_url` must match the paper/official source title and abstract.
- `effects` must come from the source; write `未报告` if not reported.
- Every item: 1-8 tags from `data/tags.yaml`, one `source_tier`, 2-dim score summing to `score`.
- Page-facing `abstract`/`effects`/`mechanism`/`score_reason` must be short, readable Chinese.
- Research subagents do not edit code, docs, server files, or static pages.
- The server does not search the web; it only accepts validated research runs.
- No padding: if this week's quality content is thin, collect fewer items.
- The detail agent (6-segment deep analysis) is discontinued; do not spawn it. `detail-prompt.md` is removed.
- The full weekly loop lives in `docs/harness.md` section 3; this skill is the entry point, harness is the overview.

## Verification Before Completion

```powershell
python tests/test_research_pipeline.py
python tests/test_build.py
python app/gates/gate_all.py
git diff --check
```

Windows line-ending warnings from `git diff --check` are acceptable; whitespace errors are not.
