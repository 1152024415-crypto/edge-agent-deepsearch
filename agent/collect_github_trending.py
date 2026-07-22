#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect端侧 AI-related GitHub repos created/trending this week.

Two sources:
1. github.com/trending?since=weekly (HTML, multiple languages) — parse repos + descriptions.
2. api.github.com/search/repositories (created:>DATE + edge keywords, sort=stars) — uses
   GITHUB_PERSONAL_ACCESS_TOKEN env var if set (avoids rate limit).
Filter for端侧 AI relevance, output data/_github_trending.json with repo + stars + url + created.
Reusable each week — change DATE_FROM and keywords as needed.
"""
import urllib.request, urllib.parse, re, sys, json, time, os
from datetime import datetime, timezone

DATE_FROM = "2026-07-08"  # created:> this date

EDGE_KW = [
  "on-device","on device","edge","mobile","npu","embedded","mcu","iot","llm","agent",
  "inference","quantiz","speculat","distill","moe","attention","kv-cache","kv cache",
  "serving","vllm","sglang","llama.cpp","llama-cpp","executorch","mlc","tensorrt","tflite",
  "onnx","wasm","webgpu","rag","tiny","slm","small model","efficient","accelerat",
  "dspark","deepspec","jetson","raspberry","federated","lora","peft","bitnet","ternary",
  "gemma","minicpm","qwen","coreml","mlx","neural-engine","copilot","phi-","llama",
  "deepseek","xdna","ascend","rknn","hexagon","snapdragon",
]

UA = "Mozilla/5.0 (compatible: edge-agent-github-collector/1.0)"
TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN","")

def fetch(url, timeout=25, headers=None):
    h = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    if TOKEN: h["Authorization"] = f"Bearer {TOKEN}"
    if headers: h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace"), r.status
    except urllib.error.HTTPError as e:
        return "", e.code
    except Exception:
        return "", 0

def parse_trending(html):
    """Return [(full_name, desc)] from trending HTML."""
    out=[]
    for art in re.finditer(r'<article[^>]*>(.*?)</article>', html, re.S):
        body=art.group(1)
        m=re.search(r'<h2[^>]*>\s*<a[^>]*href="(/[^"]+)"', body)
        if not m: continue
        full=m.group(1).strip('/')
        dm=re.search(r'<p[^>]*>(.*?)</p>', body, re.S)
        desc=re.sub(r'<[^>]+>','',(dm.group(1) if dm else '')).strip()
        desc=re.sub(r'\s+',' ',desc)
        out.append((full,desc))
    return out

def search_api(query, per_page=30):
    q=f"{query} created:>{DATE_FROM}"
    url=f"https://api.github.com/search/repositories?{urllib.parse.urlencode({'q':q,'sort':'stars','order':'desc','per_page':per_page})}"
    txt,st=fetch(url)
    if not txt: return []
    try:
        d=json.loads(txt)
        return [(it['full_name'], it.get('description','') or '', it.get('stargazers_count',0),
                 it.get('html_url',''), it.get('created_at','')[:10]) for it in d.get('items',[])]
    except: return []

def main():
    repos={}  # full_name -> {desc, stars, url, created, source}
    # 1) trending
    for lang in ["","/python","/c","/c%2B%2B","/rust","/jupyter-notebook","/swift","/typescript"]:
        url=f"https://github.com/trending{lang}?since=weekly"
        html,st=fetch(url)
        if not html: continue
        for full,desc in parse_trending(html):
            if full not in repos:
                repos[full]={"desc":desc,"stars":None,"url":f"https://github.com/{full}","created":None,"source":"trending"}
        time.sleep(1)
    # 2) search API for端侧 keywords created this week
    for q in ['on-device LLM','edge AI inference','mobile LLM agent','NPU inference',
              'speculative decoding','local LLM engine','edge device agent','llama.cpp executorch']:
        for full,desc,stars,url,created in search_api(q):
            if full not in repos or repos[full]['stars'] is None:
                repos[full]={"desc":desc,"stars":stars,"url":url,"created":created,"source":"search"}
        time.sleep(2)
    # filter端侧 relevance
    out=[]
    for full,r in repos.items():
        hay=(full+' '+r['desc']).lower()
        if not any(k in hay for k in EDGE_KW): continue
        out.append({"repo":full,"desc":r['desc'][:140],"stars":r['stars'],"url":r['url'],"created":r['created'],"source":r['source']})
    out.sort(key=lambda x:(x['stars'] or 0), reverse=True)
    json.dump(out, open("data/_github_trending.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"# {len(out)}端侧-AI repos (trending + created>{DATE_FROM})")
    for r in out[:40]:
        print(f"  {str(r['stars'] or '?'):>4}★ [{r['source']}] {r['repo']}  -- {r['desc'][:60]}")
        print(f"      {r['url']}")

if __name__=="__main__":
    main()
