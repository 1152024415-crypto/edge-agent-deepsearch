#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect official vendor dynamics across the canonical 24-source set.

Robust discovery: robots.txt -> Sitemap: entries -> (recurse index) -> <url><loc><lastmod>.
Plus known-good RSS feeds. The seven-date window is computed at runtime.
Output: data/_vendors_collected.json
"""
import argparse
import urllib.request, re, sys, json, time, gzip, io
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from research_collection import collection_window, parse_collection_date, update_source_coverage

# vendor -> (base_domain_for_robots, [known RSS/sitemap URLs to try first])
VENDORS = {
  "Apple":       ("https://www.apple.com", ["https://www.apple.com/newsroom/sitemap.xml","https://machinelearning.apple.com/feed/"]),
  "Samsung":     ("https://news.samsung.com", ["https://news.samsung.com/global/feed","https://semiconductor.samsung.com/feed/"]),
  "Huawei":      ("https://www.huawei.com", ["https://www.huawei.com/en/rss/news/","https://consumer.huawei.com/sitemap.xml"]),
  "Qualcomm":    ("https://www.qualcomm.com", ["https://www.qualcomm.com/sitemap.xml"]),
  "MediaTek":    ("https://www.mediatek.com", ["https://www.mediatek.com/sitemap.xml","https://neuropilot.mediatek.com/feed/"]),
  "Xiaomi":      ("https://www.mi.com", ["https://blog.mi.com/feed/","https://mimo.xiaomi.com/feed/"]),
  "OPPO":        ("https://www.oppo.com", ["https://www.oppo.com/sitemap.xml"]),
  "vivo":        ("https://www.vivo.com", ["https://www.vivo.com/sitemap.xml"]),
  "Honor":       ("https://www.honor.com", ["https://www.honor.com/sitemap.xml"]),
  "Google":      ("https://blog.google", ["https://blog.google/sitemap.xml","https://blog.google/feed/rss/","https://developers.googleblog.com/feed/"]),
  "Microsoft":   ("https://blogs.microsoft.com", ["https://blogs.microsoft.com/ai/feed/","https://blogs.microsoft.com/sitemap.xml","https://techcommunity.microsoft.com/gxcuf89792/sitemap.xml"]),
  "OpenAI":      ("https://openai.com", ["https://openai.com/news/rss.xml","https://openai.com/sitemap.xml"]),
  "Anthropic":   ("https://www.anthropic.com", ["https://www.anthropic.com/sitemap.xml"]),
  "Meta":        ("https://ai.meta.com", ["https://ai.meta.com/blog/feed/","https://ai.meta.com/sitemap.xml"]),
  "NVIDIA":      ("https://developer.nvidia.com", ["https://developer.nvidia.com/blog/feed/","https://developer.nvidia.com/sitemap.xml"]),
  "Mistral":     ("https://mistral.ai", ["https://mistral.ai/sitemap.xml"]),
  "ModelBest":   ("https://modelbest.cn", ["https://modelbest.cn/sitemap.xml"]),
  "Qwen":        ("https://qwenlm.github.io", ["https://qwenlm.github.io/feed.xml","https://qwenlm.github.io/sitemap.xml"]),
  "Zhipu":       ("https://www.zhipuai.cn", ["https://www.zhipuai.cn/sitemap.xml","https://open.bigmodel.cn/sitemap.xml"]),
  "DeepSeek":    ("https://api-docs.deepseek.com", ["https://api-docs.deepseek.com/sitemap.xml","https://www.deepseek.com/sitemap.xml"]),
  "Moonshot":    ("https://www.kimi.com", ["https://www.kimi.com/sitemap.xml"]),
  "MiniMax":     ("https://www.minimax.io", ["https://www.minimax.io/sitemap.xml","https://www.minimaxi.com/sitemap.xml"]),
  "Baichuan":    ("https://www.baichuan-ai.com", ["https://www.baichuan-ai.com/sitemap.xml"]),
  "StepFun":     ("https://www.stepfun.com", ["https://www.stepfun.com/sitemap.xml"]),
}

EDGE_KW = ["on-device","on device","edge","mobile","npu","embedded","mcu","iot","agent","llm","ai ","artificial intelligence","gemini","copilot","phi-","llama","minicpm","qwen","gauss","andes","bluelm","hyperai","milm","aisp","dimensity","snapdragon","hexagon","neuropilot","ascend","pangu","hiai","intelligen","model","reasoning","inference","genai","generative","speculat","quantiz","distill","小模型","端侧","边缘","大模型","智能体","推理","量化","deepseek","spark","flash","mla","gemma"]

UA = "Mozilla/5.0 (compatible; edge-agent-vendor-collector/1.0)"

def fetch(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            if url.endswith('.gz') or r.headers.get('Content-Type','').endswith('gzip'):
                raw = gzip.decompress(raw)
            return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""

def strip_ns(xml):
    # strip prefixed namespaces AND default xmlns so ET tags are plain (url/loc/lastmod)
    xml = re.sub(r'\sxmlns(:[a-zA-Z0-9._]+)?="[^"]*"', '', xml)
    return re.sub(r'<(/?)[a-zA-Z0-9._]*:', r'<\1', xml)

def parse_date(s):
    if not s: return None
    s=s.strip(); s=re.sub(r'(\+)(\d{2}):(\d{2})$', r'\1\2\3', s)
    for fmt in ('%a, %d %b %Y %H:%M:%S %Z','%Y-%m-%dT%H:%M:%S%z','%Y-%m-%dT%H:%M:%SZ','%Y-%m-%d %H:%M:%S','%Y-%m-%d'):
        try:
            d=datetime.strptime(s,fmt); return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except: continue
    m=re.search(r'(\d{4})-(\d{2})-(\d{2})',s)
    if m:
        try: return datetime(int(m[1]),int(m[2]),int(m[3]),tzinfo=timezone.utc)
        except: pass
    return None

def find_sitemaps_in_robots(txt):
    return [l.split(':',1)[1].strip() for l in txt.splitlines() if l.strip().lower().startswith('sitemap:')]

def extract_urls(txt):
    """From RSS/Atom/sitemap -> [(title,url,date)]. Also return child sitemap locs if index."""
    out=[]; children=[]
    if not txt or '<html' in txt[:300].lower() or '404' in txt[:400]: return out,children
    try: root=ET.fromstring(strip_ns(txt))
    except: return out,children
    for it in root.iter():
        tg=it.tag.lower()
        if tg in ('sitemap',):
            for c in it:
                if c.tag.lower()=='loc' and c.text: children.append(c.text.strip())
        if tg in ('item','entry','url'):
            title=link=pub=''
            for c in it:
                ct=c.tag.lower()
                if ct=='title': title=(c.text or '').strip()
                elif ct in ('loc','link'): link=c.get('href') or (c.text or '').strip()
                elif ct in ('pubdate','published','updated','date','lastmod','news:publication_date'): pub=(c.text or '').strip()
            if link: out.append((title,link,pub))
    seen=set(); uniq=[]
    for t,l,p in out:
        if l not in seen: seen.add(l); uniq.append((t,l,p))
    return uniq, children

def alive(url, timeout=12):
    for method in ('HEAD','GET'):
        try:
            req=urllib.request.Request(url,method=method,headers={"User-Agent":UA})
            with urllib.request.urlopen(req,timeout=timeout) as r: return r.status<400
        except urllib.error.HTTPError as exc:
            if method=='HEAD': continue
            return exc.code<400
        except Exception:
            if method=='HEAD': continue
            return True
    return False


def is_structured_source(txt):
    """True when a response is a parseable feed or sitemap, even with zero rows."""
    if not txt or '<html' in txt[:300].lower() or '404' in txt[:400]:
        return False
    try:
        root = ET.fromstring(strip_ns(txt))
    except ET.ParseError:
        return False
    return root.tag.lower() in {'rss', 'feed', 'urlset', 'sitemapindex'}


def collect_vendor(vendor, base, known, window_start, window_end):
    found=[]
    attempted=[]
    succeeded=[]

    def consume(src, txt):
        attempted.append(src)
        items, children = extract_urls(txt)
        if is_structured_source(txt):
            succeeded.append(src)
        if items:
            sys.stderr.write(f"[{vendor}] SOURCE {src} -> {len(items)}\n")
            found.extend(items)
        return children

    # 1) Aggregate every known official feed; one successful feed must not hide another.
    for src in known:
        txt=fetch(src)
        consume(src, txt)

    # 2) Also discover official sitemaps. Feeds and sitemaps are complementary.
    robots_url = base+"/robots.txt"
    robots=fetch(robots_url)
    attempted.append(robots_url)
    sm=find_sitemaps_in_robots(robots)
    sm=sorted(sm, key=lambda u: 0 if any(k in u.lower() for k in ('news','blog','post','article')) else 1)
    for s in sm[:6]:
        children = consume(s, fetch(s))
        kids=sorted(children, key=lambda u: 0 if any(k in u.lower() for k in ('news','blog','post','article','en')) else 1)
        for ch in kids[:4]:
            consume(ch, fetch(ch))

    # Deduplicate before applying the semantic/date filter.
    raw=[]; seen_urls=set()
    for title, link, pub in found:
        if link in seen_urls:
            continue
        seen_urls.add(link)
        raw.append((title, link, pub))
    res=[]
    for title,link,pub in raw:
        dt=parse_date(pub)
        if not dt: continue
        if not (window_start <= dt.date() <= window_end): continue
        hay=(title+' '+link).lower()
        if not any(k in hay for k in EDGE_KW): continue
        res.append({"vendor":vendor,"title":title or link,"url":link,"date":dt.strftime('%Y-%m-%d')})
    if res:
        status = "found"
    elif succeeded:
        status = "no_match"
    else:
        status = "unreachable"
    check = {
        "status": status,
        "sources_attempted": attempted,
        "sources_succeeded": sorted(set(succeeded)),
        "candidate_count": len(res),
    }
    return res, check

def main(argv=None):
    parser = argparse.ArgumentParser(description="Collect official vendor dynamics for the latest seven dates.")
    parser.add_argument("--today", help="Override collection date as YYYY-MM-DD")
    parser.add_argument("--manifest", default="research_runs/collection-manifest.json")
    args = parser.parse_args(argv)
    run_date = parse_collection_date(args.today)
    window_start, window_end, _ = collection_window(run_date)

    allr=[]
    vendor_checks={}
    for vendor,(base,known) in VENDORS.items():
        items, check = collect_vendor(vendor, base, known, window_start, window_end)
        allr += items
        vendor_checks[vendor] = check
        time.sleep(1)
    seen=set(); uniq=[]
    for r in allr:
        if r['url'] in seen: continue
        seen.add(r['url']); r['alive']=alive(r['url']); uniq.append(r)
    uniq.sort(key=lambda x:(x['date'],x['vendor']), reverse=True)
    json.dump(uniq, open("data/_vendors_collected.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    complete = all(check["status"] in {"found", "no_match"} for check in vendor_checks.values())
    update_source_coverage(
        args.manifest,
        "vendors",
        {
            "status": "complete" if complete else "incomplete",
            "vendors_checked": sorted(VENDORS),
            "vendor_checks": vendor_checks,
            "candidate_count": len(uniq),
        },
        today=run_date,
    )
    print(f"# collected {len(uniq)} vendor articles {window_start}..{window_end}")
    for r in uniq:
        print(f"[{r['date']}] {r['vendor']:10} {'OK ' if r['alive'] else 'DEAD'} {r['title'][:58]}")
        print(f"      {r['url']}")
    if not complete:
        failed = [vendor for vendor, check in vendor_checks.items() if check["status"] == "unreachable"]
        print(f"[VENDORS] incomplete official-source checks: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
