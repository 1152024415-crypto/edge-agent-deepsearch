#!/usr/bin/env python3
"""Release gate — runs over the BUILT site/ + data/ artifacts, BEFORE deploy.

Catches the failure modes that shipped before by operating on real artifacts
(not the legacy frontmatter content dir, which is empty for this project):

1. contract   — __PAPERS__ must be a {"papers":[...]} dict (page.py reads
                 data.papers); no runtime server globals (window.__WEEKS__ = ...)
                 leaked into the static page.
2. links 200   — every inlined paper id + manifest past week has a built
                 site/paper/<id>.html / site/week/<label>.html (no 404s).
3. editorial   — weekly_summary highlights must be editorial news (≥5 external
                 URLs), not paper-list duplicates; paper_id highlights must resolve.
4. vendor tier — current week must have ≥1 官方动态 (vendor blogs collected);
                 0 is a process alarm requiring per-vendor evidence on disk.
5. edge agents — every item is source-reviewed; genuine on-device agents are
                 recommended and their device scope/tag/evidence agree.
6. layout       — recommendations, editorial brief, complete library and
                 community radar and unverified discovery remain separate; the complete library
                 must not remove recommended items.
7. community    — all five social/forum sources have coverage evidence, the
                 static snapshot matches data/community_radar.json, and
                 discussion URLs never masquerade as formal research sources.

Use: python app/gates/gate_release.py [--root DIR]
Pre-deploy, after `python app/build.py`. Exit 0 = ship; 1 = blocked.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import community  # noqa: E402

MIN_EXTERNAL_HIGHLIGHTS = 5
MIN_CHINESE_CHARS = 8
CJK_RE = re.compile(r"[\u3400-\u9fff]")
INTERNAL_PLACEHOLDER_RE = re.compile(
    r"auto[- ]?converted|待核实|待后续补|精修.{0,12}待补|votes\s*=|"
    r"自动初评|主\s*Agent|待复核",
    re.IGNORECASE,
)
ALLOWED_EDGE_AGENT_SCOPES = {"手机", "PC", "其他端侧", "非端侧Agent"}
DIRECT_EDGE_AGENT_SCOPES = {"手机", "PC", "其他端侧"}
DIRECT_EDGE_AGENT_TAG = "方向:端侧agent"

_PAPERS_RE = re.compile(r"window\.__PAPERS__\s*=\s*(.+?);\s*window\.__WEEKLY__", re.S)
_COMMUNITY_RE = re.compile(
    r"window\.__COMMUNITY__\s*=\s*(\{.*?\});\s*window\.__WEEKS__", re.S)
# render_page inlines with NO spaces around '=': `window.__WEEKS__=[`. The server.py
# `/` route injects WITH spaces: `window.__WEEKS__ = [`. The space-form is the runtime
# injection that must NOT survive into a static page (render_page strips it).
_SERVER_INJECT_RE = re.compile(r"window\.__WEEKS__\s+=\s+\[")
_STATIC_PAPERS_FIRST = "let data=window.__PAPERS__||null;"
_STATIC_COMMUNITY_FIRST = "let data=window.__COMMUNITY__||null;"
_OLD_RECOMMENDATION_EXCLUSION_RE = re.compile(
    r"visible\(\)\.filter\(\s*p\s*=>\s*!isRecommended\(p\)\s*\)"
)


def _err(errors, msg):
    errors.append(msg)


def check_contract(root: Path, errors: list) -> None:
    idx = root / "site" / "index.html"
    if not idx.exists():
        _err(errors, "site/index.html missing — run app/build.py first")
        return
    html = idx.read_text(encoding="utf-8")
    m = _PAPERS_RE.search(html)
    if not m:
        _err(errors, "site/index.html: window.__PAPERS__ not found — build inlining broken")
    else:
        try:
            val = json.loads(m.group(1))
            if not (isinstance(val, dict) and isinstance(val.get("papers"), list)):
                _err(errors, "site/index.html: __PAPERS__ must be a {\"papers\":[...]} dict "
                             "(page.py reads data.papers; a bare list renders 0 signals)")
        except Exception as e:
            _err(errors, f"site/index.html: __PAPERS__ not valid JSON ({e})")
    # server injects `window.__WEEKS__ = [...]` (space-form); render_page must strip it.
    # NB: render_page's own inline is `window.__WEEKS__=[` (no spaces), so the space-form
    # only appears if the server's runtime block leaked through.
    if _SERVER_INJECT_RE.search(html):
        _err(errors, "site/index.html: runtime server globals (window.__WEEKS__ = ...) leaked "
                     "into static page — render_page must strip the server injection block")
    if _STATIC_PAPERS_FIRST not in html:
        _err(errors, "site/index.html: 静态页面没有优先读取 inlined __PAPERS__；GitHub Pages 会误请求不存在的 /api/papers")
    if _STATIC_COMMUNITY_FIRST not in html:
        _err(errors, "site/index.html: 静态页面没有优先读取 inlined __COMMUNITY__；历史周或 GitHub Pages 会丢失社区快照")


def check_editorial_layout(root: Path, errors: list) -> None:
    """Keep editorial ranking, complete coverage and discovery semantically separate."""
    idx = root / "site" / "index.html"
    if not idx.exists():
        return  # check_contract reports the missing build artifact
    html = idx.read_text(encoding="utf-8")
    ordered_ids = ["recommendations", "weekly", "all-research", "source-map", "community", "discovery"]
    positions = {}
    for section_id in ordered_ids:
        position = html.find(f'id="{section_id}"')
        if position < 0:
            label = "发现线索" if section_id == "discovery" else section_id
            _err(errors, f"site/index.html: missing editorial layout section {label} ({section_id})")
        positions[section_id] = position
    if all(positions[section_id] >= 0 for section_id in ordered_ids):
        actual = [positions[section_id] for section_id in ordered_ids]
        if actual != sorted(actual):
            _err(errors, "site/index.html: editorial layout order must be 推荐 → 本周判断 → 完整资料库 → 来源构成 → 社区雷达 → GitHub 发现线索")
    if _OLD_RECOMMENDATION_EXCLUSION_RE.search(html):
        _err(errors, "site/index.html: 完整资料库仍在排除推荐条目；推荐只能作为上方编辑视图，不能从完整收录移除")


def _papers_from_index(root: Path) -> list[dict]:
    idx = root / "site" / "index.html"
    if not idx.exists():
        return []
    m = _PAPERS_RE.search(idx.read_text(encoding="utf-8"))
    if not m:
        return []
    try:
        val = json.loads(m.group(1))
        papers = val.get("papers", []) if isinstance(val, dict) else val
        return [p for p in papers if isinstance(p, dict)]
    except Exception:
        return []


def _paper_ids_from_index(root: Path) -> list:
    return [p.get("id") for p in _papers_from_index(root) if p.get("id")]


def check_community_radar(root: Path, errors: list) -> None:
    """Community leads are complete, frozen and visibly outside formal research."""
    data_path = root / "data" / "community_radar.json"
    if not data_path.exists():
        _err(errors, "data/community_radar.json missing — 社区雷达不能静默跳过来源覆盖")
        return
    try:
        raw = json.loads(data_path.read_text(encoding="utf-8"))
        expected = community.validate_community(raw, today=date.today())
    except (OSError, json.JSONDecodeError, community.CommunityValidationError) as exc:
        _err(errors, f"data/community_radar.json 校验失败（window/coverage/items）：{exc}")
        return

    index = root / "site" / "index.html"
    if not index.exists():
        return
    html = index.read_text(encoding="utf-8")
    match = _COMMUNITY_RE.search(html)
    if not match:
        _err(errors, "site/index.html: window.__COMMUNITY__ missing — 静态社区快照未构建")
        return
    try:
        actual = community.validate_community(json.loads(match.group(1)), today=date.today())
    except (json.JSONDecodeError, community.CommunityValidationError) as exc:
        _err(errors, f"site/index.html: __COMMUNITY__ 无效：{exc}")
        return
    if actual != expected:
        _err(errors, "site/index.html: __COMMUNITY__ 与 data/community_radar.json 不一致 — 构建可能使用了旧社区数据")

    community_urls = {item["url"] for item in expected["items"]}
    social_hosts = {"x.com", "twitter.com", "reddit.com", "www.reddit.com", "news.ycombinator.com"}
    for paper in _papers_from_index(root):
        paper_url = str(paper.get("paper_url") or "").strip()
        host = (urlparse(paper_url).hostname or "").lower()
        if paper_url in community_urls or host in social_hosts:
            pid = paper.get("id") or "<missing-id>"
            _err(errors, f"{pid}: 社区讨论链接不得作为正式周报 paper_url；应回链一手材料后再收录")


def _has_readable_chinese(value) -> bool:
    return len(CJK_RE.findall(str(value or ""))) >= MIN_CHINESE_CHARS


def check_recommendation_readability(root: Path, errors: list) -> None:
    """Current built recommendations must be curated Chinese reader copy."""
    papers = _papers_from_index(root)
    if not papers:
        return  # the contract gate reports missing/broken paper data
    for paper in papers:
        pid = paper.get("id") or "<missing-id>"
        score_reason = str(paper.get("score_reason") or "")
        if INTERNAL_PLACEHOLDER_RE.search(score_reason):
            _err(errors, f"{pid}: score_reason 含内部占位/流程标记")
    recommendations = [p for p in papers if p.get("recommendation") == "推荐"]
    if not recommendations:
        _err(errors, "当前周有内容但没有推荐条目 — 发布前至少人工精选 1 条并填写中文推荐理由")
        return
    for paper in recommendations:
        pid = paper.get("id") or "<missing-id>"
        title_zh = str(paper.get("title_zh") or "").strip()
        abstract = str(paper.get("abstract") or "")
        reason = str(paper.get("recommendation_reason") or "")
        if len(CJK_RE.findall(title_zh)) < 2 or len(title_zh) > 40:
            _err(errors, f"{pid}: title_zh 缺失或不是 40 字以内的简短中文项目名")
        elif INTERNAL_PLACEHOLDER_RE.search(title_zh):
            _err(errors, f"{pid}: title_zh 含内部占位/流程标记")
        elif title_zh == abstract.strip():
            _err(errors, f"{pid}: title_zh 不能直接复用项目介绍 abstract")
        if not _has_readable_chinese(abstract):
            _err(errors, f"{pid}: 推荐条目的 abstract 必须是可直接阅读的中文摘要")
        elif INTERNAL_PLACEHOLDER_RE.search(abstract):
            _err(errors, f"{pid}: abstract 含内部占位/流程标记")
        if not _has_readable_chinese(reason):
            _err(errors, f"{pid}: recommendation_reason 缺失或不是可直接阅读的中文理由")
        elif INTERNAL_PLACEHOLDER_RE.search(reason):
            _err(errors, f"{pid}: recommendation_reason 含内部占位/流程标记")


def check_edge_agent_classification(root: Path, errors: list) -> None:
    """Block keyword promotion and missed recommendations in the built artifact."""
    for paper in _papers_from_index(root):
        pid = paper.get("id") or "<missing-id>"
        scope = str(paper.get("edge_agent_scope") or "").strip()
        evidence = str(paper.get("edge_agent_evidence") or "").strip()
        tags = paper.get("tags") if isinstance(paper.get("tags"), list) else []
        if scope == "待核实":
            _err(errors, f"{pid}: edge_agent_scope=待核实，不可发布")
            continue
        if scope not in ALLOWED_EDGE_AGENT_SCOPES:
            _err(errors, f"{pid}: edge_agent_scope 缺失或非法")
            continue
        if scope in DIRECT_EDGE_AGENT_SCOPES:
            if paper.get("recommendation") != "推荐":
                _err(errors, f"{pid}: 真正端侧 Agent（{scope}）必须进入推荐区")
            if DIRECT_EDGE_AGENT_TAG not in tags:
                _err(errors, f"{pid}: 真正端侧 Agent 缺少 {DIRECT_EDGE_AGENT_TAG} 标签")
            if not _has_readable_chinese(evidence):
                _err(errors, f"{pid}: 真正端侧 Agent 缺少可读的 edge_agent_evidence 中文证据")
            try:
                relevance = int(paper.get("score_relevance"))
            except (TypeError, ValueError):
                relevance = -1
            if relevance < 8:
                _err(errors, f"{pid}: 真正端侧 Agent 的 score_relevance 必须为 8-10")
        else:
            if DIRECT_EDGE_AGENT_TAG in tags:
                _err(errors, f"{pid}: 非端侧 Agent 不得使用 {DIRECT_EDGE_AGENT_TAG} 标签")
            if evidence:
                _err(errors, f"{pid}: 非端侧 Agent 的 edge_agent_evidence 必须为空")


def check_arxiv_revision_evidence(root: Path, errors: list) -> None:
    """An arXiv update date is recall evidence, not proof of a weekly event."""
    for paper in _papers_from_index(root):
        if paper.get("arxiv_date_basis") != "updated":
            continue
        pid = paper.get("id") or "<missing-id>"
        note = str(paper.get("arxiv_revision_note") or "")
        if not _has_readable_chinese(note):
            _err(errors, f"{pid}: arXiv 更新稿缺少可读的 arxiv_revision_note 实质变化说明")


def check_links(root: Path, errors: list) -> None:
    paper_dir = root / "site" / "paper"
    for pid in _paper_ids_from_index(root):
        if not (paper_dir / f"{pid}.html").exists():
            _err(errors, f"site/paper/{pid}.html missing — row + highlight links to it would 404")
    # past-week archive pages must exist
    manifest = _read_json(root / "data" / "weeks" / "manifest.json", default=[])
    for e in manifest:
        if e.get("current"):
            continue
        label = e.get("label")
        if label and not (root / "site" / "week" / f"{label}.html").exists():
            _err(errors, f"site/week/{label}.html missing — switcher link to that week would 404")
    for nav in ("index.html", "notes.html"):
        if not (root / "site" / nav).exists():
            _err(errors, f"site/{nav} missing — nav link would 404")


def check_highlights(root: Path, errors: list) -> None:
    ws = _read_json(root / "data" / "weekly_summary.json", default=None)
    if ws is None:
        _err(errors, "data/weekly_summary.json missing")
        return
    hl = ws.get("highlights", []) or []
    external = [h for h in hl if h.get("url")]
    if len(external) < MIN_EXTERNAL_HIGHLIGHTS:
        _err(errors, f"weekly_summary highlights: only {len(external)} external-news URL(s) "
                     f"(need ≥{MIN_EXTERNAL_HIGHLIGHTS}). Highlights must be EDITORIAL news "
                     f"(vendor blogs/dynamics), not paper-list duplicates of the run.")
    paper_dir = root / "site" / "paper"
    for h in hl:
        pid = h.get("paper_id")
        if (not h.get("url")) and pid:
            if not (paper_dir / f"{pid}.html").exists():
                _err(errors, f"highlight paper_id {pid} → site/paper/{pid}.html missing (404)")


def check_vendor_tier(root: Path, errors: list) -> None:
    manifest = _read_json(root / "data" / "weeks" / "manifest.json", default=[])
    current = next((e for e in manifest if e.get("current")), None)
    if not current:
        _err(errors, "manifest: no current week entry — run app/build.py")
        return
    label = current["label"]
    arch = _read_json(root / "data" / "weeks" / f"{label}.json", default=None)
    if arch is None:
        _err(errors, f"data/weeks/{label}.json missing — current week archive not built")
        return
    papers = arch.get("papers", []) or []
    vendor_n = sum(1 for p in papers if p.get("source_tier") == "官方动态")
    if vendor_n == 0:
        ev = root / "data" / "weeks" / f"{label}-no-vendor.md"
        if not ev.exists():
            _err(errors, f"0 官方动态 in {label} — vendor blogs not collected. research-prompt "
                         f"mandates 18-vendor + model-lab blog search. Either collect them, or "
                         f"acknowledge per-vendor evidence at data/weeks/{label}-no-vendor.md.")


def check_trending_freshness(root: Path, errors: list) -> None:
    """github_trending_top20.json must be refreshed within 7 days of deploy.

    Catches the 07-15 regression: the run + weekly_summary were refreshed but
    data/github_trending_top20.json was left at 07-03 (12 days stale), so the
    page's trending section showed two-week-old repos. mtime > 7 days = FAIL.
    """
    import os
    import time
    tp = root / "data" / "github_trending_top20.json"
    if not tp.exists():
        _err(errors, "data/github_trending_top20.json missing — run agent/collect_github_trending.py "
                     "before deploy (trending section would be empty/stale)")
        return
    age_sec = time.time() - tp.stat().st_mtime
    if age_sec > 7 * 86400:
        import datetime
        days_old = int(age_sec // 86400)
        _err(errors, f"data/github_trending_top20.json is {days_old}d old (>7d) — trending section "
                     f"shows stale repos. Run agent/collect_github_trending.py to refresh.")


def check_snn_page(root: Path, errors: list) -> None:
    """site/snn.html must exist — the SNN insight page nav link points at it."""
    if not (root / "site" / "snn.html").exists():
        _err(errors, "site/snn.html missing — run agent/build_snn.py (SNN 洞察 nav 链接会 404)")


def check_waic_page(root: Path, errors: list) -> None:
    """site/waic.html must exist — the WAIC insight page nav link points at it."""
    if not (root / "site" / "waic.html").exists():
        _err(errors, "site/waic.html missing — run agent/build_waic.py (WAIC 洞察 nav 链接会 404)")


def _read_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def run_all(root: Path) -> list:
    errors = []
    check_contract(root, errors)
    check_editorial_layout(root, errors)
    check_community_radar(root, errors)
    check_edge_agent_classification(root, errors)
    check_arxiv_revision_evidence(root, errors)
    check_recommendation_readability(root, errors)
    check_links(root, errors)
    check_highlights(root, errors)
    check_vendor_tier(root, errors)
    check_trending_freshness(root, errors)
    check_snn_page(root, errors)
    check_waic_page(root, errors)
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Pre-deploy release gate over site/ + data/.")
    ap.add_argument("--root", default=str(ROOT), help="Project root (default: repo root)")
    args = ap.parse_args(argv)
    errors = run_all(Path(args.root))
    if errors:
        print(f"[FAIL] gate_release: {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[OK] gate_release passed — contract/links/editorial/vendor-tier all clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
