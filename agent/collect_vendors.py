#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect official vendor dynamics (06-23..06-30) across ~21 vendors.

Robust discovery: robots.txt -> Sitemap: entries -> (recurse index) -> <url><loc><lastmod>.
Plus known-good RSS feeds. Filters by date window + edge-AI keywords, verifies alive.
Output: data/_vendors_collected.json
"""
import urllib.request, re, sys, json, time, gzip, io
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

DATE_FROM = datetime(2026,6,26,tzinfo=timezone.utc)
DATE_TO   = datetime(2026,7,4,tzinfo=timezone.utc)

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
  "Mistral":     ("https://mistral.ai", ["https://mistral.ai/sitemap.xml"]),
  "ModelBest":   ("https://modelbest.cn", ["https://modelbest.cn/sitemap.xml"]),
  "Qwen":        ("https://qwenlm.github.io", ["https://qwenlm.github.io/feed.xml","https://qwenlm.github.io/sitemap.xml"]),
  "Zhipu":       ("https://www.zhipuai.cn", ["https://www.zhipuai.cn/sitemap.xml","https://open.bigmodel.cn/sitemap.xml"]),
  "DeepSeek":    ("https://api-docs.deepseek.com", ["https://api-docs.deepseek.com/sitemap.xml","https://www.deepseek.com/sitemap.xml"]),
  "MiniMax":     ("https://www.minimax.io", ["https://www.minimax.io/sitemap.xml","https://www.minimaxi.com/sitemap.xml"]),
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

def collect_vendor(vendor, base, known):
    found=[]
    # 1) known feeds first
    for src in known:
        txt=fetch(src)
        items,_=extract_urls(txt)
        if items:
            sys.stderr.write(f"[{vendor}] FEED {src} -> {len(items)}\n")
            found=items; break
    # 2) robots.txt -> sitemap discovery
    if not found:
        robots=fetch(base+"/robots.txt")
        sm=find_sitemaps_in_robots(robots)
        # prefer news/blog sitemaps
        sm=sorted(sm, key=lambda u: 0 if any(k in u.lower() for k in ('news','blog','post','article')) else 1)
        for s in sm[:6]:
            txt=fetch(s)
            items,children=extract_urls(txt)
            if children:
                # sitemap index -> fetch news-y children
                kids=sorted(children, key=lambda u: 0 if any(k in u.lower() for k in ('news','blog','post','article','en')) else 1)
                for ch in kids[:4]:
                    ct=fetch(ch)
                    ci,_=extract_urls(ct)
                    if ci:
                        sys.stderr.write(f"[{vendor}] SITEMAP {ch} -> {len(ci)}\n")
                        found=ci; break
                if found: break
            if items:
                sys.stderr.write(f"[{vendor}] SITEMAP {s} -> {len(items)}\n")
                found=items; break
        if not found and sm:
            sys.stderr.write(f"[{vendor}] robots sitemaps found {len(sm)} but no usable urls\n")
        elif not found:
            sys.stderr.write(f"[{vendor}] NO robots/sitemap\n")
    if not found: return []
    res=[]
    for title,link,pub in found:
        dt=parse_date(pub)
        if not dt: continue
        if not (DATE_FROM<=dt<DATE_TO): continue
        hay=(title+' '+link).lower()
        if not any(k in hay for k in EDGE_KW): continue
        res.append({"vendor":vendor,"title":title or link,"url":link,"date":dt.strftime('%Y-%m-%d')})
    return res

def main():
    allr=[]
    for vendor,(base,known) in VENDORS.items():
        allr += collect_vendor(vendor, base, known)
        time.sleep(1)
    seen=set(); uniq=[]
    for r in allr:
        if r['url'] in seen: continue
        seen.add(r['url']); r['alive']=alive(r['url']); uniq.append(r)
    uniq.sort(key=lambda x:(x['date'],x['vendor']), reverse=True)
    json.dump(uniq, open("data/_vendors_collected.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"# collected {len(uniq)} vendor articles 06-23..06-30")
    for r in uniq:
        print(f"[{r['date']}] {r['vendor']:10} {'OK ' if r['alive'] else 'DEAD'} {r['title'][:58]}")
        print(f"      {r['url']}")

if __name__=="__main__": main()
