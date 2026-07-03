#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect on-device / edge AI papers from arXiv API over a date range."""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import time
import re
import sys
import json

CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.RO", "cs.DC", "cs.AR"]
CAT_GROUP = "(" + " OR ".join(f"cat:{c}" for c in CATEGORIES) + ")"

# Each entry: (label, search_query_terms_only_without_cat_group)
QUERIES = [
    ('q1_on_device', '(abs:"on-device" OR abs:"on-device LLM" OR abs:"on-device agent")'),
    ('q2_edge', '(abs:"edge" AND (abs:"LLM" OR abs:"inference" OR abs:"agent"))'),
    ('q3_mobile', '(abs:"mobile" AND (abs:"LLM" OR abs:"agent" OR abs:"inference"))'),
    ('q4_npu_embed', '(abs:"NPU" OR abs:"embedded" OR abs:"microcontroller")'),
    ('q5_quant', '(abs:"quantization" AND (abs:"LLM" OR abs:"transformer"))'),
    ('q6_kvcache', '(abs:"KV cache" OR abs:"key-value cache" OR abs:"key value cache" OR abs:"KV-cache")'),
    ('q7_specdec', '(abs:"speculative decoding")'),
    ('q8_slm', '(abs:"small language model" OR abs:"SLM" OR abs:"lightweight")'),
    ('q9_effinfer', '(abs:"efficient inference" AND abs:"LLM")'),
    ('q10_agentfed', '(abs:"agent memory" OR abs:"tool use" OR abs:"federated")'),
]

DATE_FROM = "2026-06-26"
DATE_TO = "2026-07-03"

ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARX_NS = "{http://arxiv.org/schemas/atom}"

def fetch(query_str, start=0, max_results=100):
    base = "http://export.arxiv.org/api/query"
    search_query = f"({query_str}) AND {CAT_GROUP}"
    params = {
        "search_query": search_query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "edge-radar/1.0 (research)"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            sys.stderr.write(f"  retry {attempt} for {query_str[:40]}: {e}\n")
            time.sleep(5)
    return ""

def parse(xml_text):
    out = []
    if not xml_text:
        return out
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        sys.stderr.write(f"  parse error: {e}\n")
        return out
    total = None
    opensearch = "{http://a9.com/-/spec/opensearch/1.1/}"
    tr = root.find(f"{opensearch}totalResults")
    if tr is not None:
        total = tr.text
    for e in root.findall(f"{ATOM_NS}entry"):
        arxiv_id_el = e.find(f"{ATOM_NS}id")
        arxiv_id = (arxiv_id_el.text if arxiv_id_el is not None else "").strip()
        arxiv_id = arxiv_id.replace("http://arxiv.org/abs/", "").strip()
        # strip version
        m = re.match(r"([\d\.v]+)", arxiv_id)
        # keep id with version for url, but dedupe on base id
        pub_el = e.find(f"{ATOM_NS}published")
        pub = (pub_el.text if pub_el is not None else "").strip()
        upd_el = e.find(f"{ATOM_NS}updated")
        title_el = e.find(f"{ATOM_NS}title")
        title = (title_el.text if title_el is not None else "").strip().replace("\n", " ")
        title = re.sub(r"\s+", " ", title)
        summ_el = e.find(f"{ATOM_NS}summary")
        summary = (summ_el.text if summ_el is not None else "").strip().replace("\n", " ")
        summary = re.sub(r"\s+", " ", summary)
        # authors
        authors = []
        for a in e.findall(f"{ATOM_NS}author"):
            nm = a.find(f"{ATOM_NS}name")
            if nm is not None:
                authors.append(nm.text.strip())
        # primary category
        pcat = ""
        pc = e.find(f"{ARX_NS}primary_category")
        if pc is not None:
            pcat = pc.get("term", "")
        out.append({
            "id": arxiv_id,
            "published": pub,
            "updated": upd_el.text if upd_el is not None else "",
            "title": title,
            "summary": summary,
            "authors": authors,
            "primary_cat": pcat,
        })
    return out, total

def date_str(d):
    # d like 2026-06-23T...
    return d[:10] if d else ""

def in_range(d):
    ds = date_str(d)
    return DATE_FROM <= ds <= DATE_TO

# ---- inclusion / exclusion heuristics ----
KEEP_KEYWORDS = [
    "on-device", "on device", "edge", "mobile", "npu", "embedded", "microcontroller",
    "quantiz", "kv cache", "key-value cache", "key value cache", "kv-cache",
    "speculative decoding", "small language model", "slm", "lightweight",
    "efficient inference", "pruning", "prune", "distill", "sparse", "attention",
    "low-rank", "low rank", "mobilebert", "edgebert", "mobilellm", "edge llm",
    "edge ai", "edge inference", "iot", "federated", "agent memory", "tool use",
    "tool-use", "model compression", "inference engine", "serving", "vllm",
    "tensorrt", "llama.cpp", "onnx", "tflite", "wasm", "edge device", "edge cloud",
    "hybrid", "energy", "latency", "throughput", "batch", "offload",
    "deepspeed", "speculative", "draft", "retrieval-augmented", "rag",
]

EXCLUDE_KEYWORDS = [
    # medical triage
    "medical triage", "clinical recall", "patient triage",
    # cryptography
    "cryptograph", "post-quantum crypt", "encryption", "blockchain",
    # face / dialogue generation
    "face recognition", "face hallucination", "talking head", "dialogue generation",
    # pure training theory
    # hpo automation
    "hyperparameter optimization", "autoML", "neural architecture search",
    # pure image/video generation
    "text-to-video", "text to video", "video generation", "image generation", "diffusion model",
    # world model
    "world model",
    # robot control (unless edge)
    # GUI agent
    "gui agent", "screen interaction", "ui automation", "mobile gui",
]

def keep_paper(p):
    text = (p["title"] + " " + p["summary"]).lower()
    # exclude hard off-topics
    ex_hit = [k for k in EXCLUDE_KEYWORDS if k in text]
    # if 2+ strong off-topic signals OR a strong single one, drop (with caveat)
    # We keep liberal: only drop on very clear off-topic
    strong_off = ["medical triage", "clinical recall", "patient triage",
                  "cryptograph", "post-quantum crypt", "blockchain",
                  "face recognition", "face hallucination", "talking head",
                  "hyperparameter optimization", "neural architecture search",
                  "text-to-video", "video generation", "world model",
                  "gui agent", "ui automation", "mobile gui"]
    for k in strong_off:
        if k in text:
            return False, ("off:"+k)
    # keep if any keep keyword present
    for k in KEEP_KEYWORDS:
        if k in text:
            return True, ("keep:"+k)
    # default: keep (liberal, since query already targeted)
    return True, ("liberal")

def main():
    all_papers = {}
    for label, q in QUERIES:
        sys.stderr.write(f"\n=== {label}: {q}\n")
        xml_text = fetch(q, start=0, max_results=100)
        results, total = parse(xml_text)
        if total is not None:
            sys.stderr.write(f"  totalResults={total}, fetched={len(results)}\n")
        else:
            sys.stderr.write(f"  fetched={len(results)}\n")
        added_in_range = 0
        for p in results:
            if in_range(p["published"]) or in_range(p["updated"]):
                ds = date_str(p["published"]) or date_str(p["updated"])
                if DATE_FROM <= ds <= DATE_TO:
                    if p["id"] not in all_papers:
                        all_papers[p["id"]] = p
                        added_in_range += 1
        sys.stderr.write(f"  in-range new added: {added_in_range}\n")
        time.sleep(4)

    sys.stderr.write(f"\n=== total in-range unique: {len(all_papers)}\n")

    # apply inclusion filter
    kept = []
    dropped = []
    for pid, p in all_papers.items():
        ok, reason = keep_paper(p)
        if ok:
            kept.append(p)
        else:
            dropped.append((p, reason))
    sys.stderr.write(f"kept={len(kept)} dropped={len(dropped)}\n")

    # sort by date desc
    kept.sort(key=lambda p: p["published"], reverse=True)

    # write JSON for inspection
    with open("D:/proj/edge_agent/data/_arxiv_collect.json", "w", encoding="utf-8") as f:
        json.dump({"kept": kept, "dropped": [{"id":p["id"],"title":p["title"],"reason":r,"published":p["published"]} for p,r in dropped]}, f, ensure_ascii=False, indent=2)

    # print compact list
    print(f"# TOTAL: {len(kept)}")
    for p in kept:
        ds = date_str(p["published"]) or date_str(p["updated"])
        title = p["title"][:80]
        url = f"https://arxiv.org/abs/{p['id']}"
        # direction guess
        dirs = guess_dirs(p)
        one = one_liner(p)
        print(f"{p['id']} | {ds} | {title} | {url} | {dirs} | {one}")

def guess_dirs(p):
    t = (p["title"] + " " + p["summary"]).lower()
    d = []
    if "quantiz" in t or "int8" in t or "int4" in t or "low-bit" in t: d.append("quantization")
    if "kv cache" in t or "key-value cache" in t or "key value cache" in t or "kv-cache" in t: d.append("kv-cache")
    if "speculative" in t: d.append("spec-decoding")
    if "pruning" in t or "prune" in t or "spars" in t: d.append("pruning/sparse")
    if "distill" in t: d.append("distillation")
    if "small language model" in t or " slm" in t or "lightweight" in t: d.append("small-model")
    if "on-device" in t or "on device" in t or "edge device" in t or "mobile" in t or "npu" in t or "embedded" in t or "microcontroller" in t: d.append("on-device/edge")
    if "federated" in t: d.append("federated")
    if "agent memory" in t or "tool use" in t or "tool-use" in t or "agent" in t: d.append("agent/tool")
    if "serving" in t or "vllm" in t or "inference engine" in t or "throughput" in t: d.append("serving")
    if "attention" in t and ("efficient" in t or "linear" in t or "sparse" in t or "flash" in t): d.append("efficient-attn")
    if not d: d.append("general-edge")
    # dedupe preserve order
    seen=set(); out=[]
    for x in d:
        if x not in seen:
            seen.add(x); out.append(x)
    return ",".join(out[:3])

def one_liner(p):
    s = p["summary"]
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > 110:
        s = s[:107] + "..."
    return s

if __name__ == "__main__":
    main()
