#!/usr/bin/env python3
"""Build the static GitHub Pages paper radar from content/papers/*.md."""
import html
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent / "gates"))
import gate_common as gc


REPO_WIKI_BASE = "https://github.com/1152024415-crypto/edge-agent-deepsearch/wiki"
REC_CLASS = {"纳入": "rec-yes", "纳入待复审": "rec-review", "排除": "rec-no"}


def build_today():
    value = os.environ.get("EDGE_AGENT_TODAY")
    if value:
        return datetime.fromisoformat(value).date()
    return date.today()


TODAY = build_today()
CUTOFF = TODAY - timedelta(days=7)


def fmt_date(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value or "")


def in_current_window(value):
    try:
        paper_date = datetime.fromisoformat(fmt_date(value)).date()
    except ValueError:
        return False
    return CUTOFF <= paper_date <= TODAY


def strip_frontmatter(text):
    match = re.match(r"^---[ \t]*\r?\n.*?\r?\n---[ \t]*\r?\n?", text, re.S)
    return text[match.end():] if match else text


def normalize_text(text):
    return re.sub(r"\n{3,}", "\n\n", str(text or "").strip())


def body_intro(body):
    before_heading = re.split(r"^##\s+", body, maxsplit=1, flags=re.M)[0]
    return normalize_text(before_heading) or "未报告"


def section_text(body, heading):
    pattern = rf"^##\s+{re.escape(heading)}\s*\r?\n(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, body, re.S | re.M)
    return normalize_text(match.group(1)) if match else "未报告"


def render_markdown_text(text):
    text = normalize_text(text)
    if not text:
        return "<p>未报告</p>"

    blocks = []
    items = []
    paragraphs = []

    def flush_paragraphs():
        nonlocal paragraphs
        if paragraphs:
            blocks.append(f"<p>{html.escape(' '.join(paragraphs))}</p>")
            paragraphs = []

    def flush_items():
        nonlocal items
        if items:
            blocks.append("<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>")
            items = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraphs()
            flush_items()
            continue
        if line.startswith("- "):
            flush_paragraphs()
            items.append(line[2:].strip())
        else:
            flush_items()
            paragraphs.append(line)

    flush_paragraphs()
    flush_items()
    return "\n".join(blocks) or "<p>未报告</p>"


def source_label(url):
    host = urlparse(str(url or "")).netloc.lower()
    if "arxiv.org" in host:
        return "arXiv"
    if "openreview.net" in host:
        return "OpenReview"
    if "aclanthology.org" in host:
        return "ACL"
    if "doi.org" in host:
        return "DOI"
    if "thecvf.com" in host or "openaccess.thecvf.com" in host:
        return "CVF"
    if "pmlr" in host:
        return "PMLR"
    if "ieee" in host:
        return "IEEE"
    if "acm.org" in host:
        return "ACM"
    return host.replace("www.", "") or "论文"


def paper_from_file(path):
    fm = gc.read_frontmatter(path)
    if fm is None or fm.get("source_type") != "学术论文":
        return None

    if not in_current_window(fm.get("date")):
        return None

    body = strip_frontmatter(path.read_text(encoding="utf-8-sig"))
    slug = str(fm.get("slug") or path.stem)
    url = str(fm.get("url") or "")
    wiki_url = str(fm.get("wiki_url") or (f"{REPO_WIKI_BASE}/{slug}" if slug else ""))
    return {
        "id": str(fm.get("id") or slug),
        "slug": slug,
        "title": str(fm.get("title") or "未命名论文"),
        "date": fmt_date(fm.get("date")),
        "score": int(fm.get("score") or 0),
        "source": source_label(url),
        "url": url,
        "wiki_url": wiki_url,
        "vendors": " / ".join(str(x) for x in (fm.get("vendors") or [])) or "无",
        "authors": " / ".join(str(x) for x in (fm.get("authors") or [])) or "未知作者",
        "branches": " > ".join(str(x) for x in (fm.get("branches") or [])) or "未分类",
        "recommendation": str(fm.get("recommendation") or ""),
        "review_hint": str(fm.get("review_hint") or "未填写"),
        "insight_person": str(fm.get("insight_person") or ""),
        "abstract_html": render_markdown_text(body_intro(body)),
        "effects_html": render_markdown_text(section_text(body, "实际效果")),
        "mechanism_html": render_markdown_text(section_text(body, "工作原理")),
        "contribution_html": render_markdown_text(section_text(body, "创新贡献")),
    }


def render_row(paper):
    paper_id = html.escape(paper["id"], quote=True)
    title = html.escape(paper["title"])
    rec = html.escape(paper["recommendation"])
    rec_class = REC_CLASS.get(paper["recommendation"], "")
    local_key = html.escape(f"edge-agent:insight:{paper['id']}", quote=True)
    insight = html.escape(paper["insight_person"] or "")
    wiki_url = html.escape(paper["wiki_url"], quote=True)
    paper_url = html.escape(paper["url"], quote=True)

    return f"""<article class="paper-item" data-paper-id="{paper_id}" data-score="{paper['score']}" data-date="{html.escape(paper['date'], quote=True)}" data-local-key="{local_key}">
  <div class="paper-row">
    <div class="score-cell" aria-label="分数">{paper['score']}</div>
    <div class="date-cell">{html.escape(paper['date'])}</div>
    <div class="title-cell">
      <button class="title-button" type="button" data-action="toggle-details" aria-expanded="false">
        <span class="title-text">{title}</span>
        <span class="expand-mark" aria-hidden="true">展开</span>
      </button>
      <div class="meta-line">{html.escape(paper['authors'])}</div>
    </div>
    <div class="source-cell">{html.escape(paper['source'])}</div>
    <div class="vendor-cell">{html.escape(paper['vendors'])}</div>
    <div class="rec-cell {rec_class}">{rec}</div>
    <div class="insight-cell">
      <label class="sr-only" for="insight-{paper_id}">洞察人</label>
      <input id="insight-{paper_id}" name="insight_person" data-field="insight_person" value="{insight}" placeholder="待补" autocomplete="off">
      <span class="sync-state" data-role="sync-state"></span>
    </div>
    <div class="link-cell"><a href="{paper_url}" target="_blank" rel="noopener">原文</a></div>
    <div class="wiki-cell">
      <label class="sr-only" for="wiki-{paper_id}">wiki连接</label>
      <input id="wiki-{paper_id}" name="wiki_url" data-field="wiki_url" value="{wiki_url}" placeholder="wiki URL" autocomplete="off">
      <a class="wiki-open" data-role="wiki-open" href="{wiki_url}" target="_blank" rel="noopener">打开</a>
    </div>
    <div class="save-cell">
      <button type="button" data-action="save-insight">保存</button>
    </div>
  </div>
  <div class="paper-details" hidden>
    <section>
      <h3>论文摘要</h3>
      {paper['abstract_html']}
    </section>
    <section>
      <h3>论文效果</h3>
      {paper['effects_html']}
    </section>
    <section>
      <h3>工作原理</h3>
      {paper['mechanism_html']}
    </section>
    <section>
      <h3>创新贡献</h3>
      {paper['contribution_html']}
    </section>
    <section>
      <h3>关注建议</h3>
      <p>{html.escape(paper['review_hint'])}</p>
    </section>
    <section>
      <h3>技术分支</h3>
      <p>{html.escape(paper['branches'])}</p>
    </section>
  </div>
</article>"""


def render_empty_state(total_files):
    return f"""<section class="empty-state">
  <h2>暂无可展示论文</h2>
  <p>当前扫描到 {total_files} 个内容文件，但没有通过本周论文过滤。</p>
  <p>展示字段：论文标题 / 论文摘要 / 论文效果 / 工作原理 / 论文连接 / 洞察人 / wiki连接。</p>
  <p>请让主 agent 读取 docs/agent-guide/main-agent-workflow.md，调度子 agent 生成 research_runs/*.json 后发布到服务器。</p>
</section>"""


all_files = gc.list_papers()
papers = [paper for paper in (paper_from_file(path) for path in all_files) if paper]
papers.sort(key=lambda item: (item["score"], item["date"]), reverse=True)
rows_html = "\n".join(render_row(paper) for paper in papers) if papers else render_empty_state(len(all_files))
paper_payload = json.dumps(
    [{"id": p["id"], "score": p["score"], "date": p["date"]} for p in papers],
    ensure_ascii=False,
)

html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>端侧 AI Agent 论文雷达</title>
<style>
  :root {{
    --bg: #f7f5ef;
    --panel: #fffdf7;
    --ink: #1f2420;
    --muted: #687069;
    --line: #d9d4c8;
    --line-strong: #a9a191;
    --accent: #8d2f24;
    --accent-soft: #f1ded8;
    --good: #35694d;
    --review: #8a5a16;
    --focus: #235a7c;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: "Segoe UI", "Noto Sans SC", system-ui, sans-serif;
    line-height: 1.45;
  }}
  a {{ color: var(--focus); text-decoration-thickness: 1px; text-underline-offset: 3px; }}
  a:focus-visible, button:focus-visible, input:focus-visible {{
    outline: 3px solid var(--focus);
    outline-offset: 2px;
  }}
  .page {{
    width: min(1440px, calc(100% - 28px));
    margin: 0 auto;
  }}
  header {{
    padding: 22px 0 14px;
    border-bottom: 2px solid var(--ink);
  }}
  .topline {{
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 18px;
    flex-wrap: wrap;
  }}
  h1 {{
    margin: 0;
    font-size: 1.65rem;
    line-height: 1.2;
    letter-spacing: 0;
  }}
  .status {{
    margin: 6px 0 0;
    color: var(--muted);
    font-size: .92rem;
  }}
  .controls {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .controls button, .save-cell button {{
    min-height: 36px;
    border: 1px solid var(--line-strong);
    background: var(--panel);
    color: var(--ink);
    padding: 6px 10px;
    font: inherit;
    cursor: pointer;
  }}
  .controls button[aria-pressed="true"] {{
    border-color: var(--accent);
    background: var(--accent-soft);
    color: var(--accent);
    font-weight: 700;
  }}
  main {{ padding: 14px 0 40px; }}
  .paper-table {{
    border: 1px solid var(--line-strong);
    background: var(--panel);
  }}
  .paper-head, .paper-row {{
    display: grid;
    grid-template-columns: 64px 98px minmax(280px, 1.9fr) 88px 132px 96px 150px 72px minmax(170px, .8fr) 72px;
    align-items: center;
    gap: 0;
  }}
  .paper-head {{
    position: sticky;
    top: 0;
    z-index: 2;
    background: #eee8dc;
    color: var(--muted);
    border-bottom: 1px solid var(--line-strong);
    font-size: .78rem;
    font-weight: 700;
  }}
  .paper-head > div, .paper-row > div {{
    min-width: 0;
    padding: 7px 8px;
    border-right: 1px solid var(--line);
  }}
  .paper-head > div:last-child, .paper-row > div:last-child {{ border-right: 0; }}
  .paper-item + .paper-item {{ border-top: 1px solid var(--line); }}
  .paper-row {{
    min-height: 48px;
    font-size: .9rem;
  }}
  .paper-item:nth-child(even) .paper-row {{ background: #fbf8f0; }}
  .score-cell {{
    color: var(--accent);
    font-weight: 800;
    font-size: 1.05rem;
    text-align: right;
  }}
  .date-cell, .source-cell, .vendor-cell, .rec-cell, .link-cell, .save-cell {{ white-space: nowrap; }}
  .title-cell {{ padding-top: 5px; padding-bottom: 5px; }}
  .title-button {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    width: 100%;
    min-height: 34px;
    border: 0;
    background: transparent;
    padding: 0;
    color: var(--ink);
    font: inherit;
    text-align: left;
    cursor: pointer;
  }}
  .title-text {{
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 700;
  }}
  .expand-mark {{
    color: var(--muted);
    font-size: .78rem;
    white-space: nowrap;
  }}
  .meta-line {{
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--muted);
    font-size: .78rem;
  }}
  .rec-yes {{ color: var(--good); font-weight: 700; }}
  .rec-review {{ color: var(--review); font-weight: 700; }}
  .rec-no {{ color: var(--accent); font-weight: 700; }}
  input {{
    width: 100%;
    min-height: 34px;
    border: 1px solid var(--line);
    background: #fffefa;
    color: var(--ink);
    padding: 5px 7px;
    font: inherit;
  }}
  .insight-cell {{
    display: grid;
    gap: 3px;
  }}
  .sync-state {{
    color: var(--review);
    font-size: .72rem;
    min-height: 1em;
  }}
  .wiki-cell {{
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 6px;
    align-items: center;
  }}
  .wiki-open {{ white-space: nowrap; }}
  .paper-details {{
    border-top: 1px solid var(--line);
    background: #fffaf0;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px 20px;
    padding: 14px 16px 18px 160px;
    font-size: .9rem;
  }}
  .paper-details section:nth-child(1),
  .paper-details section:nth-child(3) {{
    grid-column: span 2;
  }}
  .paper-details h3 {{
    margin: 0 0 5px;
    color: var(--accent);
    font-size: .78rem;
    letter-spacing: .05em;
  }}
  .paper-details p {{ margin: 0; }}
  .paper-details ul {{ margin: 0; padding-left: 1.1rem; }}
  .empty-state {{ padding: 28px; }}
  .sr-only {{
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }}
  footer {{
    padding: 18px 0 34px;
    color: var(--muted);
    font-size: .82rem;
  }}
  @media (max-width: 980px) {{
    .paper-table {{ border: 0; background: transparent; }}
    .paper-head {{ display: none; }}
    .paper-item {{
      border: 1px solid var(--line-strong);
      background: var(--panel);
      margin-bottom: 10px;
    }}
    .paper-item + .paper-item {{ border-top: 1px solid var(--line-strong); }}
    .paper-row {{
      display: grid;
      grid-template-columns: 54px minmax(0, 1fr) 72px;
      gap: 0;
      align-items: start;
    }}
    .date-cell, .source-cell, .vendor-cell, .rec-cell, .insight-cell,
    .link-cell, .wiki-cell, .save-cell {{
      border-top: 1px solid var(--line);
    }}
    .title-cell {{ grid-column: span 2; }}
    .source-cell, .vendor-cell, .rec-cell, .link-cell, .save-cell {{ white-space: normal; }}
    .insight-cell, .wiki-cell {{ grid-column: span 3; }}
    .paper-details {{
      grid-template-columns: 1fr;
      padding: 12px;
    }}
    .paper-details section:nth-child(1),
    .paper-details section:nth-child(3) {{
      grid-column: auto;
    }}
  }}
</style>
</head>
<body>
<div class="page">
  <header>
    <div class="topline">
      <div>
        <h1>端侧 AI Agent 论文雷达</h1>
        <p class="status">{len(papers)} 篇论文 · 默认按分数降序 · 数据来自 content/papers/*.md</p>
      </div>
      <div class="controls" aria-label="排序控件">
        <button type="button" data-sort="score" data-direction="desc" aria-pressed="true">分数 ↓</button>
        <button type="button" data-sort="date" data-direction="desc" aria-pressed="false">日期 ↓</button>
      </div>
    </div>
  </header>
  <main>
    <section class="paper-table" aria-label="论文列表">
      <div class="paper-head" aria-hidden="true">
        <div>分数</div>
        <div>日期</div>
        <div>论文标题</div>
        <div>来源</div>
        <div>厂商/机构</div>
        <div>推荐</div>
        <div>洞察人</div>
        <div>论文连接</div>
        <div>wiki连接</div>
        <div>操作</div>
      </div>
      {rows_html}
    </section>
  </main>
  <footer>GitHub Pages 静态展示阶段：洞察人 / wiki 保存会先尝试 POST /api/insights，失败后写入本地浏览器存储并标记“本地未同步”。</footer>
</div>
<script type="application/json" id="paper-data">{html.escape(paper_payload)}</script>
<script>
(() => {{
  const table = document.querySelector(".paper-table");
  const sortButtons = Array.from(document.querySelectorAll("[data-sort]"));
  const rows = () => Array.from(document.querySelectorAll(".paper-item"));

  function setActiveSort(activeButton) {{
    sortButtons.forEach((button) => button.setAttribute("aria-pressed", String(button === activeButton)));
  }}

  function sortRows(key, direction) {{
    const sign = direction === "asc" ? 1 : -1;
    const sorted = rows().sort((a, b) => {{
      if (key === "score") {{
        return (Number(a.dataset.score) - Number(b.dataset.score)) * sign;
      }}
      return String(a.dataset.date).localeCompare(String(b.dataset.date)) * sign;
    }});
    sorted.forEach((row) => table.appendChild(row));
  }}

  sortButtons.forEach((button) => {{
    button.addEventListener("click", () => {{
      const current = button.dataset.direction || "desc";
      const next = button.getAttribute("aria-pressed") === "true"
        ? (current === "desc" ? "asc" : "desc")
        : "desc";
      button.dataset.direction = next;
      button.textContent = `${{button.dataset.sort === "score" ? "分数" : "日期"}} ${{next === "desc" ? "↓" : "↑"}}`;
      setActiveSort(button);
      sortRows(button.dataset.sort, next);
    }});
  }});

  function rowPayload(row) {{
    return {{
      paper_id: row.dataset.paperId,
      insight_person: row.querySelector('[data-field="insight_person"]').value.trim(),
      wiki_url: row.querySelector('[data-field="wiki_url"]').value.trim(),
    }};
  }}

  function applyLocal(row) {{
    const raw = localStorage.getItem(row.dataset.localKey);
    if (!raw) return;
    try {{
      const payload = JSON.parse(raw);
      row.querySelector('[data-field="insight_person"]').value = payload.insight_person || "";
      row.querySelector('[data-field="wiki_url"]').value = payload.wiki_url || "";
      row.querySelector('[data-role="sync-state"]').textContent = "本地未同步";
      updateWikiLink(row);
    }} catch (_) {{}}
  }}

  function updateWikiLink(row) {{
    const input = row.querySelector('[data-field="wiki_url"]');
    const link = row.querySelector('[data-role="wiki-open"]');
    const value = input.value.trim();
    link.href = value || "#";
    link.textContent = value ? "打开" : "待补";
  }}

  rows().forEach((row) => {{
    applyLocal(row);
    updateWikiLink(row);
    row.querySelectorAll("[data-field]").forEach((input) => {{
      input.addEventListener("input", () => updateWikiLink(row));
    }});
  }});

  table.addEventListener("click", async (event) => {{
    const toggle = event.target.closest('[data-action="toggle-details"]');
    if (toggle) {{
      const item = toggle.closest(".paper-item");
      const details = item.querySelector(".paper-details");
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!expanded));
      toggle.querySelector(".expand-mark").textContent = expanded ? "展开" : "收起";
      details.hidden = expanded;
      return;
    }}

    const save = event.target.closest('[data-action="save-insight"]');
    if (!save) return;
    const row = save.closest(".paper-item");
    const state = row.querySelector('[data-role="sync-state"]');
    const payload = rowPayload(row);
    state.textContent = "保存中";
    try {{
      const response = await fetch("/api/insights", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(payload),
      }});
      if (!response.ok) throw new Error("not synced");
      state.textContent = "已同步";
      localStorage.removeItem(row.dataset.localKey);
    }} catch (_) {{
      localStorage.setItem(row.dataset.localKey, JSON.stringify(payload));
      state.textContent = "本地未同步";
    }}
    updateWikiLink(row);
  }});
}})();
</script>
</body>
</html>"""

out = gc.ROOT / "site" / "index.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html_doc, encoding="utf-8")
print(f"[BUILD] {len(papers)} papers -> {out}")
