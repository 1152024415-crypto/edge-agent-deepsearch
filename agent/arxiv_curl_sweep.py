#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Curl-based arXiv API sweep for in-window edge-AI papers.

Fetches many keyword queries via the arXiv Atom API (which DOES honor query
terms, unlike the MCP search_papers), parses entries, filters to the 7-day
window, dedups against the existing run, and writes candidates to a JSON file
for the scoring sub-agent.
"""
import json
import re
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "research_runs" / "_nodup_placeholder.json"  # nonexistent → no dedup (complete fresh re-sweep of the window)
OUT = ROOT / ".superpowers" / "sdd" / "arxiv_candidates.json"

WINDOW_LO = "2026-07-10"
WINDOW_HI = "2026-07-17"
CATS = "(cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.RO OR cat:cs.AR OR cat:cs.DC OR cat:cs.ET OR cat:cs.SY OR cat:cs.NE)"

# (label, search_query_fragment)  -- single words quoted, multi-word via AND
QUERIES = [
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


def curl(query):
    full = f"{query} AND {CATS}"
    sq = urllib.parse.quote(full, safe="")  # encode everything incl. quotes/parens/spaces
    url = (f"http://export.arxiv.org/api/query?search_query={sq}"
           f"&max_results=100&sortBy=submittedDate&sortOrder=descending")
    for attempt in range(4):
        try:
            r = subprocess.run(["curl", "-sL", "--max-time", "40", "-w", "\n%{http_code}", url],
                               capture_output=True, text=True, timeout=50)
        except Exception as e:
            print(f"  [ERR] {query}: {e}", file=sys.stderr)
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


def main():
    # pace: arxiv asks >=3s between requests
    import time as _t
    _t.sleep(60)  # initial cooldown for any active 429


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
        pub = (e.find("a:published", ns).text or "")[:10]  # YYYY-MM-DD
        summ = (e.find("a:summary", ns).text or "").strip().replace("\n", " ")
        summ = re.sub(r"\s+", " ", summ)
        authors = [a.find("a:name", ns).text for a in e.findall("a:author", ns) if a.find("a:name", ns) is not None]
        cats = [c.get("term") for c in e.findall("{http://arxiv.org/schemas/atom}category") or []]
        if not cats:
            cats = [l.get("href", "").split("=")[-1] for l in e.findall("a:link", ns) if l.get("title") == "pdf"]
        out.append({"id": aid, "title": title, "date": pub, "abstract": summ,
                    "authors": "; ".join(authors[:8]), "categories": cats})
    return out


def main():
    existing = set()
    if RUN.exists():
        d = json.loads(RUN.read_text(encoding="utf-8"))
        existing = {p["id"].replace("arxiv-", "") for p in d["papers"]}
        print(f"existing in run: {len(existing)} ids")

    seen = {}  # aid -> entry (dedup across queries)
    for label, q in QUERIES:
        xml = curl(q)
        entries = parse(xml)
        in_win = [e for e in entries if WINDOW_LO <= e["date"] <= WINDOW_HI]
        new = [e for e in in_win if e["id"] not in existing]
        for e in new:
            if e["id"] not in seen:
                seen[e["id"]] = e
        print(f"  {label:22s} total={len(entries):3d} in_win={len(in_win):3d} new={len(new):3d}")
        time.sleep(4)  # polite pacing for arxiv API

    cands = list(seen.values())
    cands.sort(key=lambda e: e["date"], reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cands, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n==> {len(cands)} unique in-window NEW candidates -> {OUT}")


if __name__ == "__main__":
    main()
