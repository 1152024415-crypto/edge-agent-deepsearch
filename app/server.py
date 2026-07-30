#!/usr/bin/env python3
"""HTTP API and page routes for the edge agent research display server."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import threading
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
from app import weeks as weeks_mod
from app import build as build_app
from app.page import INDEX_HTML

DEPLOY_SERVER = "http://127.0.0.1:8001"
DEPLOY_DEBOUNCE_SECONDS = 10.0

_deploy_timer: threading.Timer | None = None
_deploy_lock = threading.Lock()
_deploy_running = False


def _deploy_to_ghpages() -> None:
    """Build site/ via build.py then push to gh-pages via a temp worktree.

    Runs in a background thread. Failures print a warning and never raise.
    The temp worktree keeps the master working tree untouched (no checkout
    switching on the main repo).
    """
    try:
        # Auto-refresh github trending BEFORE build so each publish gets a
        # fresh top20 (was manual — gate caught staleness but didn't auto-fix).
        # Runs in the deploy thread; failures are non-fatal (stale trending
        # is better than no deploy).
        subprocess.run(
            [sys.executable, str(ROOT / "agent" / "refresh_trending.py")],
            cwd=str(ROOT), capture_output=True, text=True, timeout=180,
        )
        build = subprocess.run(
            [sys.executable, str(ROOT / "app" / "build.py"),
             "--server", DEPLOY_SERVER],
            cwd=str(ROOT), capture_output=True, text=True, timeout=60,
        )
        if build.returncode != 0:
            print(f"[DEPLOY] build.py failed: {build.stderr.strip()}", flush=True)
            return
        site_dir = ROOT / "site"
        if not site_dir.exists():
            print("[DEPLOY] site/ missing after build", flush=True)
            return
        subprocess.run(
            ["git", "fetch", "origin", "gh-pages"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=30,
        )
        with tempfile.TemporaryDirectory(prefix="gh-pages-deploy-") as tmp:
            tmp_path = Path(tmp)
            wt = subprocess.run(
                ["git", "worktree", "add", "--detach",
                 str(tmp_path), "origin/gh-pages"],
                cwd=str(ROOT), capture_output=True, text=True, timeout=30,
            )
            if wt.returncode != 0:
                print(f"[DEPLOY] worktree add failed: {wt.stderr.strip()}", flush=True)
                return
            try:
                for item in tmp_path.iterdir():
                    if item.name == ".git":
                        continue
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                for item in site_dir.iterdir():
                    target = tmp_path / item.name
                    if item.is_dir():
                        shutil.copytree(item, target)
                    else:
                        shutil.copy2(item, target)
                subprocess.run(
                    ["git", "add", "-A"], cwd=str(tmp_path),
                    capture_output=True, text=True, timeout=30,
                )
                diff = subprocess.run(
                    ["git", "diff", "--cached", "--quiet"],
                    cwd=str(tmp_path), capture_output=True, text=True, timeout=30,
                )
                if diff.returncode == 0:
                    print("[DEPLOY] no changes to push", flush=True)
                    return
                subprocess.run(
                    ["git", "commit", "-m",
                     "auto deploy: refresh GitHub Pages snapshot"],
                    cwd=str(tmp_path), capture_output=True, text=True, timeout=30,
                )
                push = subprocess.run(
                    ["git", "push", "origin", "HEAD:gh-pages"],
                    cwd=str(tmp_path), capture_output=True, text=True, timeout=60,
                )
                if push.returncode != 0:
                    print(f"[DEPLOY] push failed: {push.stderr.strip()}", flush=True)
                else:
                    print("[DEPLOY] pushed site/ to gh-pages", flush=True)
            finally:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(tmp_path)],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=30,
                )
    except Exception as exc:
        print(f"[DEPLOY] warning: {exc}", flush=True)


def _run_deploy() -> None:
    """Guard: skip if a previous deploy is still running."""
    global _deploy_running
    with _deploy_lock:
        if _deploy_running:
            print("[DEPLOY] previous deploy still running, skipping", flush=True)
            return
        _deploy_running = True
    try:
        _deploy_to_ghpages()
    finally:
        with _deploy_lock:
            _deploy_running = False


def _trigger_deploy() -> None:
    """Debounced trigger: deploy runs DEPLOY_DEBOUNCE_SECONDS after last call."""
    global _deploy_timer
    with _deploy_lock:
        if _deploy_timer is not None:
            _deploy_timer.cancel()
        _deploy_timer = threading.Timer(DEPLOY_DEBOUNCE_SECONDS, _run_deploy)
        _deploy_timer.daemon = True
        _deploy_timer.start()


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
            manifest = weeks_mod.attach_hrefs(
                weeks_mod.read_manifest(), weeks_base="", runtime=True)
            html = INDEX_HTML.replace(
                "<script>",
                '<script>window.__WEEKS__ = '
                + json.dumps(manifest, ensure_ascii=False)
                + ';window.__WEEK_LABEL__ = null;'
                + 'window.__WEEKS_BASE__ = "";</script>\n    <script>',
                1)
            self.send_html(html)
            return
        if parsed.path == "/api/papers":
            params = parse_qs(parsed.query)
            sort = params.get("sort", ["score"])[0]
            self.send_json(200, {"papers": storage.list_papers(self.server.db_path, sort=sort)})
            return
        if parsed.path == "/api/weekly":
            wp = ROOT / "data" / "weekly_summary.json"
            if wp.exists():
                self.send_json(200, json.loads(wp.read_text(encoding="utf-8")))
            else:
                self.send_json(200, {"overview": "", "highlights": []})
            return
        if parsed.path == "/api/trending":
            tp = ROOT / "data" / "github_trending_top20.json"
            if tp.exists():
                self.send_json(200, {"items": json.loads(tp.read_text(encoding="utf-8"))})
            else:
                self.send_json(200, {"items": []})
            return
        if parsed.path == "/api/weeks":
            self.send_json(200, {"weeks": weeks_mod.read_manifest()})
            return
        if parsed.path.startswith("/week/"):
            label = parsed.path.rsplit("/", 1)[-1]
            rec = weeks_mod.read_archive(label)
            if rec is None:
                self.send_json(404, {"ok": False, "error": f"week {label} not found"})
                return
            manifest = weeks_mod.attach_hrefs(
                weeks_mod.read_manifest(), weeks_base="", runtime=True)
            page = build_app.render_page(
                INDEX_HTML, rec["papers"], rec["weekly"], rec["trending"],
                manifest, week_label=label, weeks_base="", runtime=True)
            self.send_html(page)
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
                _trigger_deploy()
                return
            if parsed.path == "/api/insights":
                self.send_json(200, storage.update_insight(self.server.db_path, payload))
                return
            if parsed.path == "/api/paper-detail":
                self.send_json(200, storage.update_detail(self.server.db_path, payload))
                _trigger_deploy()
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


def _tier_class(tier: str) -> str:
    return {
        "官方动态": "",
        "开源大项目": " oss",
        "公司项目": " company",
        "学校顶会": " school",
        "学校预印本": " school",
    }.get(tier or "", "")


def render_detail(paper: dict) -> str:
    tags = "".join(f'<span class="tag">{_esc(t)}</span>' for t in paper.get("tags") or [])
    official = '<span class="tier">官方动态</span>' if paper.get("source_tier") == "官方动态" else ""
    tier_badge = f'<span class="tier{_tier_class(paper.get("source_tier"))}">{_esc(paper.get("source_tier"))}</span>'
    open_badge = '<span class="open-badge">开源</span>' if paper.get("open_source") else ''
    vendors_raw = (paper.get("vendors") or "").strip()
    vendors_tag = f'<span class="vendor-tag">{_esc(vendors_raw)}</span>' if vendors_raw else ''
    tags_block = f'<div class="tags">{vendors_tag}{tags}</div>' if (vendors_tag or tags) else ''
    authors = paper.get("authors") or ""
    venue = paper.get("venue") or ""
    meta_bits = [b for b in (authors, venue) if b]
    meta_extra = f' · {_esc(" / ".join(meta_bits))}' if meta_bits else ''
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{_esc(paper.get("title"))}</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;font-family:-apple-system,"Segoe UI","Microsoft YaHei",Arial,sans-serif;background:#f7f3ea;color:#202621}} main{{max-width:820px;margin:0 auto;padding:20px}} a{{color:#8d3d30}} .back{{display:inline-block;margin-bottom:12px;text-decoration:none}} h1{{font-size:21px;margin:0 0 8px;line-height:1.35}} .meta{{color:#627066;font-size:13px;margin-bottom:12px}} .score{{font-weight:700;color:#8d3d30;font-size:17px}} .tier{{display:inline-block;padding:2px 7px;border:1px solid #8d3d30;color:#8d3d30;font-size:11px;font-weight:700;border-radius:3px}} .tier.oss{{border-color:#2e7d32;color:#2e7d32}} .tier.company{{border-color:#5a6b8d;color:#5a6b8d}} .tier.school{{border-color:#8a6d3b;color:#8a6d3b}} .open-badge{{display:inline-block;padding:2px 7px;border:1px solid #2e7d32;color:#2e7d32;font-size:11px;font-weight:700;border-radius:3px}} .tags{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:10px 0 14px}} .vendor-tag{{display:inline-block;padding:3px 10px 3px 8px;background:#fffdf7;border-left:3px solid #8d3d30;border-radius:0 4px 4px 0;font-size:12px;font-weight:600;color:#8d3d30}} .tag{{display:inline-block;padding:2px 9px;background:#eee7da;border-radius:11px;font-size:12px;color:#596258}} .field{{display:flex;margin-top:10px;gap:10px}} .label{{flex-shrink:0;width:78px;color:#627066;font-size:13px;font-weight:600}} .text{{color:#3f463f;font-size:14px;line-height:1.6}} .score-reason{{margin-top:12px;color:#4c554e;font-size:12px;line-height:1.5}} .source{{margin-top:18px}} .source a{{display:inline-block;padding:6px 14px;border:1px solid #8d3d30;border-radius:4px;text-decoration:none;font-size:13px}}
</style></head><body><main>
<a class="back" href="/">← 返回雷达</a>
<h1>{_esc(paper.get("title"))}</h1>
<div class="meta"><span class="score">{_esc(paper.get("score"))}</span> {tier_badge} {open_badge} {_esc(paper.get("date"))}{meta_extra}</div>
{tags_block}
<div class="field"><span class="label">这是什么</span><span class="text">{_esc(paper.get("abstract"))}</span></div>
<div class="field"><span class="label">有什么结果</span><span class="text">{_esc(paper.get("effects"))}</span></div>
<div class="field"><span class="label">怎么做到</span><span class="text">{_esc(paper.get("mechanism"))}</span></div>
<div class="score-reason">评分依据：{_esc(paper.get("score_reason") or "")}</div>
<div class="source"><a href="{_esc(paper.get("paper_url"))}" target="_blank" rel="noopener">查看原文 →</a></div>
</main></body></html>"""


def create_server(address=("127.0.0.1", 8000), db_path: str | Path = ROOT / "app" / "papers.sqlite"):
    return ResearchServer(address, Handler, Path(db_path))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the edge agent research display server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default=str(ROOT / "app" / "papers.sqlite"),
                        help="SQLite path; must match create_server default so published papers are visible")
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
