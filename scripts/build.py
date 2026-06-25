#!/usr/bin/env python3
"""Build the static GitHub Pages view from content/posts/*.md.

The repo is a display surface. Agent-written posts remain the source of truth;
this script only renders them into a readable paper radar page.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_common as gc


REPO_WIKI_BASE = "https://github.com/1152024415-crypto/edge-agent-deepsearch/wiki"
REC_CLASS = {"纳入": "rec-yes", "纳入待复审": "rec-review", "排除": "rec-no"}


def fmt_date(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value or "")


def strip_frontmatter(text):
    match = re.match(r"^---[ \t]*\r?\n.*?\r?\n---[ \t]*\r?\n?", text, re.S)
    return text[match.end():] if match else text


def normalize_text(text):
    return re.sub(r"\n{3,}", "\n\n", text.strip())


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
    list_items = []
    paragraphs = []

    def flush_paragraphs():
        nonlocal paragraphs
        if paragraphs:
            escaped = html.escape(" ".join(paragraphs))
            blocks.append(f"<p>{escaped}</p>")
            paragraphs = []

    def flush_list():
        nonlocal list_items
        if list_items:
            items = "".join(f"<li>{html.escape(item)}</li>" for item in list_items)
            blocks.append(f"<ul>{items}</ul>")
            list_items = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraphs()
            flush_list()
            continue
        if line.startswith("- "):
            flush_paragraphs()
            list_items.append(line[2:].strip())
        else:
            flush_list()
            paragraphs.append(line)

    flush_paragraphs()
    flush_list()
    return "\n".join(blocks) or "<p>未报告</p>"


def field_block(label, content, class_name="field"):
    return f"""<section class="{class_name}">
  <h3>{html.escape(label)}</h3>
  <div class="field-body">{content}</div>
</section>"""


def link_block(label, url, text):
    if not url:
        return field_block(label, "<p>待补</p>", "field field-link")
    safe_url = html.escape(str(url), quote=True)
    safe_text = html.escape(text)
    return field_block(
        label,
        f'<p><a class="text-link" href="{safe_url}" target="_blank" rel="noopener">{safe_text}</a></p>',
        "field field-link",
    )


def render_card(fm, body):
    title = str(fm.get("title", "未命名论文"))
    date = fmt_date(fm.get("date"))
    source = str(fm.get("source_type", ""))
    authors = " / ".join(str(x) for x in (fm.get("authors") or []))
    vendors = " / ".join(str(x) for x in (fm.get("vendors") or [])) or "无"
    branches = " > ".join(str(x) for x in (fm.get("branches") or [])) or "未分类"
    score = fm.get("score", "NA")
    rec = str(fm.get("recommendation", ""))
    rec_class = REC_CLASS.get(rec, "")
    url = str(fm.get("url", ""))
    slug = str(fm.get("slug", ""))
    insight_person = str(fm.get("insight_person") or "待补")
    wiki_url = str(fm.get("wiki_url") or (f"{REPO_WIKI_BASE}/{slug}" if slug else ""))

    abstract = body_intro(body)
    mechanism = section_text(body, "工作原理")
    effects = section_text(body, "实际效果")

    return f"""<article class="paper-card">
  <div class="paper-rank">
    <span class="score-value">{html.escape(str(score))}</span>
    <span class="score-label">score</span>
  </div>
  <div class="paper-content">
    <div class="paper-kicker">
      <span>{html.escape(date)}</span>
      <span>{html.escape(source)}</span>
      <span>{html.escape(vendors)}</span>
      <span class="{rec_class}">{html.escape(rec)}</span>
    </div>
    {field_block("论文标题", f"<h2>{html.escape(title)}</h2>", "field field-title")}
    <div class="paper-meta">
      <span>{html.escape(authors)}</span>
      <span>{html.escape(branches)}</span>
    </div>
    <div class="field-grid">
      {field_block("论文摘要", render_markdown_text(abstract))}
      {field_block("论文效果", render_markdown_text(effects))}
      {field_block("工作原理", render_markdown_text(mechanism))}
      {field_block("洞察人", f"<p>{html.escape(insight_person)}</p>", "field field-compact")}
      {link_block("论文连接", url, "打开原文")}
      {link_block("wiki连接", wiki_url, "打开 wiki")}
    </div>
  </div>
</article>"""


def render_empty_state():
    return """<section class="empty-state">
  <h2>暂无论文条目</h2>
  <p>运行 agent 搜索并写入 content/posts/*.md 后，再执行 build。</p>
</section>"""


posts = gc.list_posts()
cards = []
for path in posts:
    fm = gc.read_frontmatter(path)
    if fm is None:
        continue
    body = strip_frontmatter(path.read_text(encoding="utf-8-sig"))
    cards.append((fmt_date(fm.get("date")), render_card(fm, body)))

cards.sort(key=lambda item: item[0], reverse=True)
cards_html = "\n".join(card for _, card in cards) if cards else render_empty_state()

html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>端侧 AI Agent 论文雷达</title>
<style>
  :root {{
    --paper: #f5f0e8;
    --ink: #20201d;
    --muted: #6e665c;
    --line: #d8cdbd;
    --panel: #fffaf0;
    --accent: #9b2f24;
    --accent-soft: #ead6cc;
    --olive: #4f6045;
    --focus: #1f5e83;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background:
      linear-gradient(90deg, rgba(32,32,29,.035) 1px, transparent 1px),
      linear-gradient(180deg, rgba(32,32,29,.03) 1px, transparent 1px),
      var(--paper);
    background-size: 32px 32px;
    color: var(--ink);
    font-family: "Noto Serif SC", Georgia, "Times New Roman", serif;
    line-height: 1.65;
  }}
  a {{ color: inherit; }}
  a:focus-visible {{
    outline: 3px solid var(--focus);
    outline-offset: 3px;
  }}
  .page-shell {{
    width: min(1180px, calc(100% - 32px));
    margin: 0 auto;
  }}
  header {{
    padding: 48px 0 28px;
    border-bottom: 2px solid var(--ink);
  }}
  .eyebrow {{
    margin: 0 0 12px;
    color: var(--accent);
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
  }}
  h1 {{
    max-width: 850px;
    margin: 0;
    font-size: 2.25rem;
    line-height: 1.12;
    letter-spacing: 0;
  }}
  .lede {{
    max-width: 760px;
    margin: 18px 0 0;
    color: var(--muted);
    font-size: 1rem;
  }}
  .toolbar {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 24px;
    color: var(--muted);
    font-size: .9rem;
  }}
  .tag {{
    border: 1px solid var(--line);
    background: rgba(255, 250, 240, .74);
    padding: 6px 10px;
  }}
  main {{
    display: grid;
    gap: 24px;
    padding: 30px 0 54px;
  }}
  .paper-card {{
    display: grid;
    grid-template-columns: 92px minmax(0, 1fr);
    gap: 22px;
    padding: 24px 0 30px;
    border-bottom: 1px solid var(--line);
  }}
  .paper-rank {{
    position: sticky;
    top: 18px;
    align-self: start;
    border-top: 3px solid var(--ink);
    padding-top: 10px;
  }}
  .score-value {{
    display: block;
    color: var(--accent);
    font-size: 2.15rem;
    font-weight: 700;
    line-height: 1;
  }}
  .score-label {{
    color: var(--muted);
    font-size: .78rem;
    text-transform: uppercase;
  }}
  .paper-content {{
    min-width: 0;
    background: rgba(255,250,240,.55);
    border-left: 6px solid var(--accent-soft);
    padding: 0 0 0 22px;
  }}
  .paper-kicker, .paper-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px 14px;
    color: var(--muted);
    font-size: .86rem;
  }}
  .paper-kicker span:not(:last-child)::after,
  .paper-meta span:not(:last-child)::after {{
    content: "/";
    margin-left: 14px;
    color: var(--line);
  }}
  .rec-yes {{ color: var(--olive); font-weight: 700; }}
  .rec-review {{ color: var(--accent); font-weight: 700; }}
  .rec-no {{ color: #7a1f1f; font-weight: 700; }}
  .field {{
    min-width: 0;
    padding-top: 14px;
  }}
  .field h3 {{
    margin: 0 0 7px;
    color: var(--accent);
    font-size: .78rem;
    letter-spacing: .06em;
  }}
  .field-title h3 {{ margin-bottom: 4px; }}
  .field-title h2 {{
    margin: 0;
    max-width: 900px;
    font-size: 1.38rem;
    line-height: 1.35;
    letter-spacing: 0;
  }}
  .field-body p {{
    margin: 0;
    color: var(--ink);
  }}
  .field-body ul {{
    margin: 0;
    padding-left: 1.1rem;
  }}
  .field-body li + li {{ margin-top: 4px; }}
  .field-grid {{
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 12px 28px;
    margin-top: 8px;
  }}
  .field-grid .field:first-child,
  .field-grid .field:nth-child(3) {{
    grid-column: 1 / -1;
  }}
  .field-compact,
  .field-link {{
    border-top: 1px solid var(--line);
  }}
  .text-link {{
    display: inline-flex;
    min-height: 44px;
    align-items: center;
    color: var(--focus);
    font-weight: 700;
    text-decoration-thickness: 1px;
    text-underline-offset: 4px;
  }}
  .empty-state {{
    padding: 42px 0;
    border-bottom: 1px solid var(--line);
  }}
  footer {{
    padding: 26px 0 40px;
    border-top: 2px solid var(--ink);
    color: var(--muted);
    font-size: .86rem;
  }}
  @media (max-width: 760px) {{
    .page-shell {{ width: min(100% - 24px, 1180px); }}
    header {{ padding-top: 34px; }}
    h1 {{ font-size: 1.72rem; }}
    .paper-card {{
      grid-template-columns: 1fr;
      gap: 10px;
      padding: 20px 0 28px;
    }}
    .paper-rank {{
      position: static;
      display: flex;
      align-items: baseline;
      gap: 8px;
      border-top: 2px solid var(--ink);
    }}
    .score-value {{ font-size: 1.6rem; }}
    .paper-content {{
      border-left: 0;
      padding-left: 0;
    }}
    .field-grid {{ grid-template-columns: 1fr; }}
    .field-grid .field:first-child,
    .field-grid .field:nth-child(3) {{
      grid-column: auto;
    }}
  }}
</style>
</head>
<body>
<div class="page-shell">
  <header>
    <p class="eyebrow">Edge Agent Literature Radar</p>
    <h1>端侧 AI Agent 论文雷达</h1>
    <p class="lede">按 agent 搜索结果生成的静态展示页，优先呈现论文标题、摘要、效果、工作原理、原文连接、洞察人和 wiki 连接。</p>
    <div class="toolbar" aria-label="页面统计">
      <span class="tag">{len(cards)} 篇条目</span>
      <span class="tag">GitHub Pages 静态展示</span>
      <span class="tag">来源：content/posts/*.md</span>
    </div>
  </header>
  <main>
    {cards_html}
  </main>
  <footer>edge_agent · 由 scripts/build.py 生成 · 搜索与判断由 agent 按 README 提示词完成</footer>
</div>
</body>
</html>"""

out = gc.ROOT / "site" / "index.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html_doc, encoding="utf-8")
print(f"[BUILD] {len(cards)} posts -> {out}")
