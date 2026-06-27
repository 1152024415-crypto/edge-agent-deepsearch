#!/usr/bin/env python3
"""HTTP API and page routes for the edge agent research display server."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "agent"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import research_run
from app import storage
from app.page import INDEX_HTML


class ResearchServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_cls, db_path: Path):
        self.db_path = Path(db_path)
        storage.init_db(self.db_path)
        super().__init__(server_address, handler_cls)


class Handler(BaseHTTPRequestHandler):
    server: ResearchServer

    def log_message(self, fmt, *args):
        return

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_html(INDEX_HTML)
            return
        if parsed.path == "/api/papers":
            params = parse_qs(parsed.query)
            sort = params.get("sort", ["score"])[0]
            self.send_json(200, {"papers": storage.list_papers(self.server.db_path, sort=sort)})
            return
        if parsed.path.startswith("/paper/"):
            paper_id = parsed.path.rsplit("/", 1)[-1]
            paper = storage.get_paper(self.server.db_path, paper_id)
            if paper is None:
                self.send_json(404, {"ok": False, "error": "paper not found"})
                return
            self.send_html(render_detail(paper))
            return
        self.send_json(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            payload = self.read_json()
            if parsed.path == "/api/research-runs":
                self.send_json(200, storage.upsert_run(self.server.db_path, payload))
                return
            if parsed.path == "/api/insights":
                self.send_json(200, storage.update_insight(self.server.db_path, payload))
                return
            if parsed.path == "/api/paper-detail":
                self.send_json(200, storage.update_detail(self.server.db_path, payload))
                return
            self.send_json(404, {"ok": False, "error": "not found"})
        except (json.JSONDecodeError, research_run.ValidationError) as exc:
            self.send_json(400, {"ok": False, "error": str(exc)})


def _esc(value) -> str:
    return (str(value or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _detail_to_html(detail_raw: str) -> str:
    """Render detail markdown (## headers + paragraphs) as styled HTML.

    ## 标题 -> bold subheading with left color bar; other lines grouped into
    paragraphs (single newlines become <br>, blank lines separate paragraphs).
    """
    lines = detail_raw.split("\n")
    parts: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("## "):
            parts.append(f'<div class="d-h">{_esc(line[3:].strip())}</div>')
            i += 1
            continue
        if line.startswith("# "):
            parts.append(f'<div class="d-h">{_esc(line[2:].strip())}</div>')
            i += 1
            continue
        para_lines = [line]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if not nxt or nxt.startswith("#"):
                break
            para_lines.append(nxt)
            i += 1
        para = _esc("\n".join(para_lines)).replace("\n", "<br>")
        parts.append(f'<p class="d-p">{para}</p>')
    return "".join(parts)


def render_detail(paper: dict) -> str:
    kws = "".join(f'<span class="kw">{_esc(k)}</span>' for k in paper.get("keywords") or [])
    detail_raw = paper.get("detail") or ""
    detail_html = _detail_to_html(detail_raw) if detail_raw.strip() else '<em>整理中，由后台 agent 生成后刷新可见</em>'
    official = '<span class="vendor-badge">官方大厂</span>' if paper.get("is_major_vendor_official") else ''
    open_badge = '<span class="open-badge">开源</span>' if (paper.get("score_open") or 0) > 0 else ''
    score_dims = (
        f'<div class="score-dims">契合{_esc(paper.get("score_relevance"))}'
        f'·厂商{_esc(paper.get("score_vendor"))}'
        f'·贡献{_esc(paper.get("score_contribution"))}'
        f'·质量{_esc(paper.get("score_quality"))}'
        f'·时效{_esc(paper.get("score_recency"))}'
        f'·开源{_esc(paper.get("score_open"))}</div>'
    )
    vendors_raw = (paper.get("vendors") or "").strip()
    vendors_tag = f'<span class="vendor-tag">{_esc(vendors_raw)}</span>' if vendors_raw else ''
    kw_inner = f'<div class="keywords">{kws}</div>' if kws else ''
    tags_block = f'<div class="tags">{vendors_tag}{kw_inner}</div>' if (vendors_tag or kw_inner) else ''
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{_esc(paper.get("title"))}</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;font-family:-apple-system,"Segoe UI","Microsoft YaHei",Arial,sans-serif;background:#f7f3ea;color:#202621}} main{{max-width:820px;margin:0 auto;padding:20px}} a{{color:#8d3d30}} .back{{display:inline-block;margin-bottom:12px;text-decoration:none}} h1{{font-size:22px;margin:0 0 8px}} .meta{{color:#627066;font-size:13px;margin-bottom:12px}} .score{{font-weight:700;color:#8d3d30;font-size:18px}} .vendor-badge{{display:inline-block;padding:2px 7px;border:1px solid #8d3d30;color:#8d3d30;font-size:11px;font-weight:700;border-radius:3px}} .open-badge{{display:inline-block;padding:2px 7px;border:1px solid #2e7d32;color:#2e7d32;font-size:11px;font-weight:700;border-radius:3px}} .score-dims{{color:#7a837a;font-size:12px;margin:6px 0 0}} .tags{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:10px 0 14px}} .vendor-tag{{display:inline-block;padding:3px 10px 3px 8px;background:#fffdf7;border-left:3px solid #8d3d30;border-radius:0 4px 4px 0;font-size:12px;font-weight:600;color:#8d3d30}} .keywords{{display:flex;flex-wrap:wrap;gap:5px}} .kw{{display:inline-block;padding:2px 9px;background:#eee7da;border-radius:11px;font-size:12px;color:#596258}} h2{{font-size:17px;margin:18px 0 8px;color:#202621}} .detail{{background:#fffdf7;border:1px solid #cfc6b4;border-radius:8px;padding:16px 18px;color:#3f463f;font-size:14px;line-height:1.7}} .d-h{{font-weight:700;font-size:15px;color:#202621;margin:16px 0 6px;padding-left:10px;border-left:3px solid #8d3d30}} .d-h:first-child{{margin-top:0}} .d-p{{margin:0 0 10px}} .d-p:last-child{{margin-bottom:0}} .source{{margin-top:16px}} .source a{{display:inline-block;padding:6px 14px;border:1px solid #8d3d30;border-radius:4px;text-decoration:none;font-size:13px}}
</style></head><body><main>
<a class="back" href="/">← 返回雷达</a>
<h1>{_esc(paper.get("title"))}</h1>
<div class="meta"><span class="score">{_esc(paper.get("score"))}</span> {official} {open_badge} {_esc(paper.get("date"))} · {_esc(paper.get("source_type"))}</div>
{score_dims}
{tags_block}
<h2>深度整理</h2>
<div class="detail">{detail_html}</div>
<div class="source"><a href="{_esc(paper.get("paper_url"))}" target="_blank" rel="noopener">查看论文原文 →</a></div>
</main></body></html>"""


def create_server(address=("127.0.0.1", 8000), db_path: str | Path = ROOT / "app" / "papers.sqlite"):
    return ResearchServer(address, Handler, Path(db_path))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the edge agent research display server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default=str(ROOT / "server" / "papers.sqlite"))
    args = parser.parse_args(argv)

    httpd = create_server((args.host, args.port), Path(args.db))
    print(f"Serving on http://{args.host}:{httpd.server_port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
