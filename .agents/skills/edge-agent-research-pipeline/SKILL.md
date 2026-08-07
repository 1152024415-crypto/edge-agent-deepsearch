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
- `recommendation`: automatic collection always writes `纳入`; only the main agent may promote an item to `推荐` after reading the source.
- `title_zh`: automatic collection writes an empty string; required as a short Chinese project/content name when `recommendation=推荐`.
- `recommendation_reason`: required readable Chinese when `recommendation=推荐`; explains why a reader should prioritize it.
- `edge_agent_scope`: automatic collection writes `待核实`; before publish the main agent must set `手机` / `PC` / `其他端侧` / `非端侧Agent` after reading the source.
- `edge_agent_evidence`: required readable Chinese for a verified direct edge agent; states which planning/memory/tool/action loop runs on which device.
- `date`: must be within the past 7 days; for arXiv URLs validate cross-checks either the real submitted date or the latest revision date declared by `arxiv_date_basis`. Updated old papers additionally require a Chinese `arxiv_revision_note` describing a substantive change found by comparing versions; cosmetic revisions are excluded.
- No `detail` / 6-segment deep analysis — the detail agent is discontinued. Detail page shows short summary + tags + source link.

## Quick Start: Run a Research Cycle

**最快速入口**：新 agent 收到「调研本周的内容」时，先读本 skill，然后运行：

```bash
bash agent/run_weekly.sh
```

脚本自动完成：设 token → 起 server → arXiv sweep → 检查候选文件 → attest → assemble → validate → publish → build → gate → 部署 gh-pages → 输出本地 + GitHub 两个 URL。

**需要 agent 智能的步骤**（脚本会暂停并打印指令）：
1. 派 3 个采集子 agent（HF/GitHub/vendor）→ 写 4 个候选 JSON
2. 派翻译子 agent → 英文 abstract 翻中文
3. 主 agent 策展推荐 → 手选推荐 + 写 recommendation_reason

子 agent 完成后重新跑 `bash agent/run_weekly.sh` 即可继续后续步骤。

**完整步骤**（和 `docs/harness.md` section 3 + `AGENTS.md` 一致，不许跳）：

1. **Read the strong-entry docs first** (see First Read above). Skipping these means missing the standard and fabricating dead links.
2. **Check the time window**: read `data/.last_run`. Only run if ≥7 days passed; if less, say "本周已调研" and stop. The collection window is the past 7 days.
3. **Spawn the research subagent**: inject the full `research-prompt.md`. Collect broadly through arXiv MCP + HuggingFace MCP + GitHub MCP + websearch. Keep direct edge work and adjacent AI inference/deployment work even when its contribution is ordinary; novelty controls score/recommendation, not collection. Only remove out-of-window, completely unrelated, untrusted, mismatched, or duplicate items. The subagent must report checks for all 24 canonical vendor/model-lab sources.
4. **Complete and attest the collection manifest**: all collectors update `research_runs/collection-manifest.json`. It must cover exactly seven calendar dates, every HF date, arXiv broad sweeps with pagination that naturally reaches the end of the window, GitHub trending and whitelist releases separately, and a successful official-source check for every canonical vendor/model lab. After the four final candidate JSON files exist, run `python agent/attest_candidates.py` to bind their paths, counts, file SHA-256 hashes, per-record fingerprints, and stable original title+URL+source-date identities. Every assembled paper must retain a unique `candidate_source` + `candidate_ref`; a candidate cannot be reused, and the final original title/URL/date must match that exact attested record. A `candidate_source=github` item is always `source_tier=开源大项目` and its URL must resolve to a project in the big-project whitelist. Missing/unreachable coverage, artifact mismatches, or broken lineage block assembly, validation, and publishing.
5. **Save and curate the output**: the main agent confirms final filtering + scores + tags + affiliation evidence and saves every qualified item (no cap). Automatic collection keeps `recommendation=纳入`, `title_zh=""`, and `edge_agent_scope=待核实`, and never auto-adds `方向:端侧agent`. The main agent classifies every item before validation. A genuine on-device agent has an agent loop whose critical part actually runs on a device; every such item must be recommended, ordered phone first, PC second, then robot/vehicle/IoT and other devices.
6. **Validate**: `python agent/validate_research_run.py research_runs/<run_id>.json`. The CLI validates the collection manifest before the content contract, 7-day window, links, arXiv date and dedup checks.
7. **Spot-check**: before publishing, fetch every `source_tier=官方动态` and `source_tier=开源大项目` URL and compare page content vs title/abstract. Drop mismatches.
8. **Write the editorial weekly_summary**: `data/weekly_summary.json` is an **independent editorial product**, NOT a slice of the run. `highlights` must be editorial news (vendor blogs/dynamics/industry events with **external URLs**, ≥5). Do NOT fill highlights with `paper_id` links to the run's top papers — that duplicates the paper list. Write from the `官方动态` tier + judgment. If `官方动态` count is 0, you have NOT collected vendor blogs — go back to step 3 and collect them, or write per-vendor evidence to `data/weeks/<label>-no-vendor.md`.
9. **Start the server** (if not running): set `EDGE_PUBLISH_TOKEN` to a strong shared secret, then run `python app/server.py --host 127.0.0.1 --port 8001`.
10. **Publish**: set the same `EDGE_PUBLISH_TOKEN`, then run `python agent/publish_results.py research_runs/<run_id>.json --server http://127.0.0.1:8001` (writes `data/.last_run_papers.json` for next-run dedup + triggers gh-pages deploy).
11. **See it on the page** (do NOT skip — assertIn tests don't catch functional regressions): open `http://127.0.0.1:8001/` (or the built `site/index.html`), and with chrome-devtools **click every link type** — row, weekly-highlight, week-switcher (both directions), back-link, notes — each must resolve to 200 content, not 404. Compare highlights to last week: are they editorial news (external URLs), or paper-list duplicates?
12. **Run the release gate** (hard blocker): `python app/gates/gate_all.py`. `gate_release.py` checks the built `site/` + `data/` for: __PAPERS__ contract, completed edge-agent classification, mandatory recommendation/evidence/tag/relevance for every genuine on-device agent, readable Chinese recommendation copy, internal-link 200s, editorial highlights, and vendor coverage. **If gate_release FAILs, do not deploy.**
13. **Close the loop**: update `data/.last_run` to this research time (ISO 8601). Fold this week's mistakes into `AGENTS.md` lessons, `validation-rules.md`, and `research-prompt.md`.

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
- Broad collection boundary: include direct edge/on-device work plus AI inference/deployment techniques with clear transfer value to constrained devices. Relevant quantization, pruning, cache, benchmark, runtime, and cloud-serving work stays in the complete collection at an appropriately lower relevance/contribution score; it is normally not recommended. Completely unrelated work is excluded.
- The inclusive window contains exactly seven calendar dates and is computed dynamically; hard-coded dates are forbidden.
- `research_runs/collection-manifest.json` is mandatory and is embedded in the run. Four-source coverage plus candidate path/count/hash/record attestation and run lineage must pass in the assembler, publish client, and server. All write APIs require the shared `EDGE_PUBLISH_TOKEN`, so anonymous direct POSTs cannot bypass the trusted publisher. `--allow-incomplete-coverage` is for local historical recovery only.
- `source_tier=公司项目` requires both `vendors` and a live, authoritative `affiliation_evidence_url` (arXiv PDF, OpenReview/Scholar profile, or recognized proceedings page), with every declared vendor explained separately in `score_reason`. A GitHub repo/release is never affiliation evidence and stays `开源大项目`; without first-party affiliation evidence, keep the research item as `学校预印本` until verified.
- Filter out pure GUI agents (screen-tap / GUI automation / screen parsing) unless there is notable non-GUI innovation.
- Open-source entries: only industry-recognized big projects in `docs/references/big-projects-whitelist.md`, with a `github.com` URL. No small repos.
- Official-vendor entries (`source_tier=官方动态`) must use an official domain; unofficial blogs / news / GitHub releases / social / secondary commentary are excluded.
- `date` must come from source metadata. New arXiv papers use `submitted`; old papers recalled by `updated` are publishable only after the main agent compares versions and records a substantive experiment/method/data/code/conclusion change in `arxiv_revision_note`. Cosmetic revisions are dropped. Do not re-date old papers into the window.
- 7-day window; no old sample data to pad the page.
- `paper_url` must match the paper/official source title and abstract.
- `effects` must come from the source; write `未报告` if not reported.
- Every item: 1-8 tags from `data/tags.yaml`, one `source_tier`, 2-dim score summing to `score`.
- Page-facing `title_zh`/`abstract`/`effects`/`mechanism`/`score_reason`/`recommendation_reason` must be short, readable Chinese and contain no internal workflow markers. Abstracts must be complete sentences, not ellipsis-truncated source fragments. A recommended `title_zh` is a name (2+ CJK, at most 40 characters), not a copied abstract. `score_reason` explains relevance/contribution to readers and must never substitute for recommendation copy or expose pipeline status.
- Automatic converters never set `推荐` from keywords. The main agent curates priority items after reading sources and writes `recommendation_reason` for each one.
- A genuine edge agent requires both an agent loop and device-side execution evidence. Phone is the highest priority, PC is second, and other devices remain fully collected and recommended. Cloud agents merely accessed from a phone/PC, ordinary edge inference/quantization/cache/detection, and cloud-side agent training infrastructure are `非端侧Agent` and cannot use `方向:端侧agent`.
- Research subagents do not edit code, docs, server files, or static pages.
- The server does not search the web; it only accepts validated research runs.
- No padding with unrelated or untrusted content, but do not delete relevant low-contribution items merely to make the list look curated. Collection maximizes coverage; recommendation manages attention.
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
