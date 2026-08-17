#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Curl-based arXiv API sweep for in-window edge-AI papers.

Fetches many keyword queries via the arXiv Atom API (which DOES honor query
terms, unlike the MCP search_papers), parses entries, filters to the 7-day
window, dedups against the existing run, and writes candidates to a JSON file
for the scoring sub-agent.
"""
import argparse
import json
import re
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

from research_collection import (
    REQUIRED_ARXIV_SWEEPS,
    candidate_artifact_attestation,
    collection_window,
    parse_collection_date,
    update_source_coverage,
)

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "research_runs" / "_nodup_placeholder.json"  # nonexistent → no dedup (complete fresh re-sweep of the window)
OUT = ROOT / ".superpowers" / "sdd" / "arxiv_candidates.json"
MANIFEST = ROOT / "research_runs" / "collection-manifest.json"
CATS = "(cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.RO OR cat:cs.AR OR cat:cs.DC OR cat:cs.ET OR cat:cs.SY OR cat:cs.NE)"

# (label, search_query_fragment)  -- single words quoted, multi-word via AND
# Broad category sweeps (no keyword filter, catch ALL recent papers by date)
# + specific keyword queries for edge-AI topics.
QUERIES = [
    # Broad category sweeps — catch all recent papers, not just keyword-matched.
    # This prevents missing relevant papers (small models, efficient inference, etc.)
    # whose abstracts don't contain "on-device" or "edge" explicitly.
    ("cs.AI-broad", "cat:cs.AI"),
    ("cs.LG-broad", "cat:cs.LG"),
    ("cs.CL-broad", "cat:cs.CL"),
    ("cs.RO-broad", "cat:cs.RO"),
    ("cs.AR-broad", "cat:cs.AR"),
    ("cs.DC-broad", "cat:cs.DC"),
    ("cs.ET-broad", "cat:cs.ET"),
    ("cs.SY-broad", "cat:cs.SY"),
    ("cs.NE-broad", "cat:cs.NE"),
    # Specific edge-AI keyword queries (catch explicitly edge papers)
    ("on-device", 'abs:"on-device"'),
    ("edge-computing", 'abs:"edge computing"'),
    ("edge-LLM", "(abs:edge AND abs:LLM)"),
    ("mobile-LLM", "(abs:mobile AND abs:LLM)"),
    ("on-device-LLM", 'abs:"on-device LLM"'),
    ("NPU", "abs:NPU"),
    ("FPGA-LLM", "(abs:FPGA AND (abs:transformer OR abs:LLM OR abs:inference))"),
    ("in-memory-compute", '(abs:"compute-in-memory" OR abs:"in-memory computing")'),
    ("quantization-edge", "(abs:quantization AND (abs:mobile OR abs:edge OR abs:efficient OR abs:LLM))"),
    ("KV-cache", 'abs:"KV cache"'),
    ("speculative", 'abs:"speculative decoding"'),
    ("SLM", '(abs:"small language model" OR abs:"small LLM")'),
    ("federated-edge", "(abs:federated AND (abs:edge OR abs:mobile OR abs:IoT OR abs:raspberry))"),
    ("efficient-inference", "(abs:efficient AND abs:inference)"),
    ("TinyML", "abs:TinyML"),
    ("edge-agent", 'abs:"edge agent"'),
    ("pruning-edge", "(abs:pruning AND (abs:edge OR abs:mobile OR abs:efficient))"),
    ("neuromorphic", "abs:neuromorphic"),
    ("SNN", '(abs:"spiking neural network" OR abs:"spiking neuron" OR abs:"spike-based")'),
]


def query_specs(only_updates: bool = False) -> list[tuple[str, str, str, str]]:
    submitted = [(label, query, "submittedDate", "submitted") for label, query in QUERIES]
    updated = [("recent-updates", CATS, "lastUpdatedDate", "updated")]
    return updated if only_updates else submitted + updated


class PaginationLimitError(RuntimeError):
    """Raised when a query is still returning in-window rows at the safety limit."""


def build_api_url(
    query: str,
    start: int = 0,
    page_size: int = 100,
    sort_by: str = "submittedDate",
) -> str:
    normalized_query = query.strip()
    is_category_sweep = normalized_query == CATS or bool(
        re.fullmatch(r"cat:[A-Za-z0-9.-]+", normalized_query)
    )
    full = normalized_query if is_category_sweep else f"{normalized_query} AND {CATS}"
    sq = urllib.parse.quote(full, safe="")  # encode everything incl. quotes/parens/spaces
    return (
        f"https://export.arxiv.org/api/query?search_query={sq}"
        f"&start={start}&max_results={page_size}"
        f"&sortBy={sort_by}&sortOrder=descending"
    )


def curl_url(url: str) -> str:
    for attempt in range(4):
        try:
            r = subprocess.run(["curl", "-sL", "--max-time", "40", "-w", "\n%{http_code}", url],
                               capture_output=True, text=True, timeout=50)
        except Exception as e:
            print(f"  [ERR] {url}: {e}", file=sys.stderr)
            time.sleep(10)
            continue
        body = r.stdout
        m = re.search(r"\n(\d{3})$", body)
        code = m.group(1) if m else "???"
        if m:
            body = body[: m.start()]
        if code == "200" and body.strip():
            return body
        if code == "429":
            wait = 30 * (attempt + 1)
            print(f"  [429] rate-limited, waiting {wait}s (attempt {attempt+1})", file=sys.stderr)
            time.sleep(wait)
            continue
        print(f"  [HTTP {code}] empty/err, retry in 10s", file=sys.stderr)
        time.sleep(10)
    return ""


def parse(xml_text):
    out = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for e in root.findall("a:entry", ns):
        id_el = e.find("a:id", ns)
        if id_el is None:
            continue
        m = re.search(r"arxiv\.org/abs/([^v]+)", id_el.text or "")
        if not m:
            continue
        aid = m.group(1)
        title = (e.find("a:title", ns).text or "").strip().replace("\n", " ")
        title = re.sub(r"\s+", " ", title)
        published_el = e.find("a:published", ns)
        updated_el = e.find("a:updated", ns)
        pub = ((published_el.text if published_el is not None else "") or "")[:10]
        updated = ((updated_el.text if updated_el is not None else "") or "")[:10]
        summ = (e.find("a:summary", ns).text or "").strip().replace("\n", " ")
        summ = re.sub(r"\s+", " ", summ)
        authors = [a.find("a:name", ns).text for a in e.findall("a:author", ns) if a.find("a:name", ns) is not None]
        cats = [c.get("term") for c in e.findall("{http://arxiv.org/schemas/atom}category") or []]
        if not cats:
            cats = [l.get("href", "").split("=")[-1] for l in e.findall("a:link", ns) if l.get("title") == "pdf"]
        out.append({"id": aid, "title": title, "date": pub,
                    "published_date": pub, "updated_date": updated or pub,
                    "date_basis": "submitted", "abstract": summ,
                    "authors": "; ".join(authors[:8]), "categories": cats})
    return out


def fetch_query_page(
    query: str,
    start: int,
    page_size: int,
    sort_by: str = "submittedDate",
) -> list[dict]:
    xml = curl_url(build_api_url(query, start=start, page_size=page_size, sort_by=sort_by))
    if not xml:
        raise RuntimeError(f"arXiv request failed for query={query!r}, start={start}")
    try:
        ET.fromstring(xml)
    except ET.ParseError as exc:
        raise RuntimeError(
            f"arXiv returned malformed XML for query={query!r}, start={start}"
        ) from exc
    return parse(xml)


def collect_query_pages(
    query: str,
    fetch_page,
    window_start: date,
    window_end: date,
    page_size: int = 100,
    max_pages: int = 20,
) -> list[dict]:
    """Fetch every in-window page instead of silently truncating at 100 rows."""
    collected: list[dict] = []
    for page_number in range(max_pages):
        start = page_number * page_size
        entries = fetch_page(query, start, page_size)
        if not entries:
            break
        for entry in entries:
            raw_date = str(entry.get("date") or "")[:10]
            if window_start.isoformat() <= raw_date <= window_end.isoformat():
                collected.append(entry)
        oldest = min((str(entry.get("date") or "")[:10] for entry in entries), default="")
        if len(entries) < page_size or (oldest and oldest < window_start.isoformat()):
            break
        time.sleep(4)  # arXiv requests at least a 3-second interval
    else:
        raise PaginationLimitError(
            f"arXiv pagination limit reached for {query!r}; increase --max-pages and retry"
        )
    return collected


def main(argv=None):
    parser = argparse.ArgumentParser(description="Collect a complete seven-day arXiv candidate set.")
    parser.add_argument("--today", help="Override collection date as YYYY-MM-DD")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument(
        "--only-updates",
        action="store_true",
        help="Merge only the lastUpdatedDate sweep into an already-complete candidate artifact.",
    )
    parser.add_argument("--manifest", default=str(MANIFEST))
    args = parser.parse_args(argv)
    run_date = parse_collection_date(args.today)
    window_start, window_end, _ = collection_window(run_date)

    existing = set()
    if RUN.exists():
        d = json.loads(RUN.read_text(encoding="utf-8"))
        existing = {p["id"].replace("arxiv-", "") for p in d["papers"]}
        print(f"existing in run: {len(existing)} ids")

    previous_coverage = {}
    if args.only_updates and Path(args.manifest).exists():
        try:
            previous_manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
            previous_coverage = previous_manifest.get("sources", {}).get("arxiv", {})
        except (OSError, json.JSONDecodeError):
            previous_coverage = {}
    seen = {}
    if args.only_updates and OUT.exists():
        try:
            seen = {entry["id"]: entry for entry in json.loads(OUT.read_text(encoding="utf-8"))}
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            seen = {}
    completed_queries = list(previous_coverage.get("queries_completed") or [])
    failed_queries = list(previous_coverage.get("queries_failed") or [])
    pages_fetched = int(previous_coverage.get("pages_fetched") or 0)
    # The lastUpdatedDate sweep catches meaningful revisions of older papers.
    for label, q, sort_by, date_basis in query_specs(args.only_updates):
        page_counter = 0

        def counted_fetch(query, start, page_size):
            nonlocal page_counter, pages_fetched
            entries = fetch_query_page(query, start, page_size, sort_by=sort_by)
            for entry in entries:
                if date_basis == "updated":
                    entry["date"] = entry.get("updated_date") or entry.get("date") or ""
                    entry["date_basis"] = "updated"
            page_counter += 1
            pages_fetched += 1
            return entries

        try:
            in_win = collect_query_pages(
                q,
                fetch_page=counted_fetch,
                window_start=window_start,
                window_end=window_end,
                page_size=args.page_size,
                max_pages=args.max_pages,
            )
        except RuntimeError as exc:
            print(f"  [ERR] {label}: {exc}", file=sys.stderr)
            failed_queries.append(label)
            continue
        if label not in completed_queries:
            completed_queries.append(label)
        failed_queries = [failed for failed in failed_queries if failed != label]
        new = [e for e in in_win if e["id"] not in existing]
        for e in new:
            if e["id"] not in seen:
                seen[e["id"]] = e
        print(f"  {label:22s} pages={page_counter:2d} in_win={len(in_win):4d} new={len(new):4d}")
        time.sleep(4)  # polite pacing for arxiv API

    cands = list(seen.values())
    cands.sort(key=lambda e: e["date"], reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cands, ensure_ascii=False, indent=2), encoding="utf-8")
    status = "complete" if not failed_queries and REQUIRED_ARXIV_SWEEPS.issubset(completed_queries) else "incomplete"
    update_source_coverage(
        args.manifest,
        "arxiv",
        {
            "status": status,
            "queries_completed": completed_queries,
            "queries_failed": failed_queries,
            "pages_fetched": pages_fetched,
            "candidate_count": len(cands),
            **candidate_artifact_attestation(OUT, "arxiv"),
        },
        today=run_date,
    )
    print(
        f"\n==> {len(cands)} unique candidates in {window_start}..{window_end} -> {OUT}; "
        f"coverage={status}"
    )
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
