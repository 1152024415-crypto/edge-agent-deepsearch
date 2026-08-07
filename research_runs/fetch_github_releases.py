"""Collect GitHub releases for edge_agent radar.

Window: 2026-08-01 to 2026-08-07 (UTC).
Collects: whitelist 13+1 repos + model-vendor orgs' recent repos' releases.
Outputs: candidates-github.json
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "edge-agent-radar",
}

WINDOW_START = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 8, 7, 23, 59, 59, tzinfo=timezone.utc)


def gh_get(url, per_page=100):
    if "?" in url:
        url = url + f"&per_page={per_page}"
    else:
        url = url + f"?per_page={per_page}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="ignore")[:200]
        except Exception:
            pass
        print(f"  HTTP {e.code} for {url}: {body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  ERR for {url}: {e}", file=sys.stderr)
        return None


def in_window(dt_str):
    if not dt_str:
        return False
    # 2026-08-03T12:34:56Z
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return False
    return WINDOW_START <= dt <= WINDOW_END


def parse_dt(dt_str):
    return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


# (owner, repo, tier)
WHITELIST_REPOS = [
    ("ggml-org", "llama.cpp", "开源大项目"),
    ("pytorch", "executorch", "开源大项目"),
    ("mlc-ai", "mlc-llm", "开源大项目"),
    ("microsoft", "onnxruntime", "开源大项目"),
    ("alibaba", "MNN", "开源大项目"),
    ("Tencent", "ncnn", "开源大项目"),
    ("google-ai-edge", "mediapipe", "开源大项目"),
    ("google-ai-edge", "litert", "开源大项目"),
    ("apple", "coremltools", "开源大项目"),
    ("ml-explore", "mlx", "开源大项目"),
    ("openvinotoolkit", "openvino", "开源大项目"),
    ("PowerInfer", "PowerInfer", "开源大项目"),
    ("HKUDS", "nanobot", "开源大项目"),
    ("microsoft", "Orchard", "开源大项目"),
    # Rockchip RKLLM - try common repo
    ("rockchip-linux", "rknn-llm", "开源大项目"),
    ("rockchip-linux", "rknn_model_zoo", "开源大项目"),
]

# Model vendor orgs
MODEL_ORGS = [
    "deepseek-ai",
    "MoonshotAI",
    "zhipuai",
    "MiniMax-AI",
    "baai-zlab",
    "QwenLM",
    "OpenBMB",
    "mistralai",
    "meta-llama",
    "facebookresearch",
]


def get_releases(owner, repo, per_page=30):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    return gh_get(url, per_page=per_page) or []


def is_significant(rel):
    """Filter out CI/patch-only builds."""
    name = (rel.get("name") or "").lower()
    tag = (rel.get("tag_name") or "").lower()
    body = (rel.get("body") or "")[:200].lower()
    # llama.cpp daily build tags like b9823 / number-only
    if owner_repo_is_daily_build(tag):
        return False
    # draft or prerelease-only? keep prereleases if tag looks like a version
    return True


def owner_repo_is_daily_build(tag):
    # llama.cpp uses pure numeric or 'bNNNN' build tags
    if tag.isdigit():
        return True
    if tag.startswith("b") and tag[1:].isdigit():
        return True
    return False


def collect_releases_for_repo(owner, repo, tier):
    releases = get_releases(owner, repo)
    out = []
    for r in releases:
        pub = r.get("published_at") or r.get("created_at")
        if not in_window(pub):
            continue
        if not is_significant(r):
            continue
        tag = r.get("tag_name") or ""
        name = r.get("name") or tag
        html_url = r.get("html_url") or f"https://github.com/{owner}/{repo}/releases/tag/{tag}"
        body = (r.get("body") or "")[:400].replace("\n", " ").strip()
        out.append({
            "repo": f"{owner}/{repo}",
            "tag": tag,
            "date": pub,
            "release_url": html_url,
            "title": name,
            "summary": "",  # filled later / leave to main agent; we leave raw excerpt
            "summary_zh": body[:200],
            "tier": tier,
            "raw_body_excerpt": body,
        })
    return out


def collect_org(org):
    """List org repos sorted by pushed, check top N for releases in window."""
    url = f"https://api.github.com/orgs/{org}/repos?sort=pushed&direction=desc"
    repos = gh_get(url, per_page=50) or []
    out = []
    checked = 0
    for repo in repos[:15]:  # top 15 most recently pushed
        rname = repo.get("name")
        pushed = repo.get("pushed_at")
        if not pushed:
            continue
        try:
            pdt = parse_dt(pushed)
        except Exception:
            continue
        # Only check repos pushed within window or slightly before (releases may lag)
        if pdt < WINDOW_START - timedelta(days=7):
            continue
        checked += 1
        rels = get_releases(org, rname, per_page=10)
        for r in rels:
            pub = r.get("published_at") or r.get("created_at")
            if not in_window(pub):
                continue
            tag = r.get("tag_name") or ""
            name = r.get("name") or tag
            html_url = r.get("html_url") or f"https://github.com/{org}/{rname}/releases/tag/{tag}"
            body = (r.get("body") or "")[:400].replace("\n", " ").strip()
            out.append({
                "repo": f"{org}/{rname}",
                "tag": tag,
                "date": pub,
                "release_url": html_url,
                "title": name,
                "summary": "",
                "summary_zh": body[:200],
                "tier": "公司项目",
                "raw_body_excerpt": body,
            })
    print(f"  org {org}: checked {checked} repos, found {len(out)} releases in window", file=sys.stderr)
    return out


def main():
    all_candidates = []
    print("== Whitelist repos ==", file=sys.stderr)
    for owner, repo, tier in WHITELIST_REPOS:
        print(f"  {owner}/{repo}", file=sys.stderr)
        rels = collect_releases_for_repo(owner, repo, tier)
        for c in rels:
            print(f"    -> {c['tag']} @ {c['date']}", file=sys.stderr)
        all_candidates.extend(rels)
    print("== Model vendor orgs ==", file=sys.stderr)
    for org in MODEL_ORGS:
        print(f"  org {org}", file=sys.stderr)
        rels = collect_org(org)
        all_candidates.extend(rels)

    # dedupe by release_url
    seen = set()
    deduped = []
    for c in all_candidates:
        if c["release_url"] in seen:
            continue
        seen.add(c["release_url"])
        deduped.append(c)

    out_path = r"D:\proj\edge_agent\research_runs\candidates-github.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    print(f"\nTotal candidates: {len(deduped)}", file=sys.stderr)
    print(f"Written to: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
