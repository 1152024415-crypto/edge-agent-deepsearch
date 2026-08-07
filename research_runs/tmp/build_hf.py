import json, re, os

TMP = 'D:/proj/edge_agent/research_runs/tmp'
OUT = 'D:/proj/edge_agent/research_runs/candidates-hf.json'

# Window 2026-08-01 to 2026-08-07. 08-01 & 08-02 returned [] (weekend, no HF daily papers).
days = ['2026-08-01','2026-08-02','2026-08-03','2026-08-04','2026-08-05','2026-08-06','2026-08-07']

def first_two_sentences(s):
    if not s:
        return ''
    # Collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    # Split on sentence enders followed by space + capital, keep the terminator
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', s)
    two = parts[:2]
    return ' '.join(two)

# Exclusion keywords for pure GUI / medical / crypto (case-insensitive)
EXCL = {
    'gui': [r'\bGUI\b', r'\buser interface design\b', r'\bbutton layout\b'],
    'med': [r'\bclinical trial\b', r'\bpatient outcome\b', r'\bmedical imaging\b',
            r'\bradiology\b', r'\bpathology\b', r'\bdrug discovery\b',
            r'\bdisease diagnosis\b', r'\bsurgical\b', r'\bmedical\b'],
    'crypto': [r'\bcryptograph', r'\bcryptography\b', r'\bblockchain\b',
               r'\bzero[- ]knowledge\b', r'\bencryption\b', r'\bcipher\b'],
}
EXCL_PATS = {k: [re.compile(p, re.I) for p in v] for k,v in EXCL.items()}

def is_excluded(title, abstract):
    txt = (title or '') + ' ' + (abstract or '')
    # Only exclude if the paper is PRIMARILY about that domain: require a strong
    # domain signal in title, OR multiple domain hits across title+abstract.
    title_low = (title or '').lower()
    abs_low = (abstract or '').lower()
    # Medical: title contains medical term OR abstract has >=2 medical terms
    for p in EXCL_PATS['med']:
        if p.search(title): return 'medical'
    med_hits = sum(1 for p in EXCL_PATS['med'] if p.search(txt))
    if med_hits >= 3: return 'medical'
    # Crypto
    for p in EXCL_PATS['crypto']:
        if p.search(title): return 'crypto'
    crypto_hits = sum(1 for p in EXCL_PATS['crypto'] if p.search(txt))
    if crypto_hits >= 2: return 'crypto'
    # GUI - only exclude if title is explicitly about GUI
    for p in EXCL_PATS['gui']:
        if p.search(title): return 'gui'
    return None

records = []
dropped = []
per_day = {}
snn_hits = 0
SNN_RE = re.compile(r'\b(spike|spiking|SNN|neuromorphic|event[- ]?based (vision|camera))\b', re.I)

for d in days:
    fpath = os.path.join(TMP, 'hf_'+d.replace('-','')+'.json')
    if not os.path.exists(fpath):
        per_day[d] = 0
        continue
    data = json.load(open(fpath, encoding='utf-8'))
    per_day[d] = len(data)
    for item in data:
        p = item.get('paper', {}) or {}
        pid = p.get('id')
        title = (item.get('title') or p.get('title') or '').strip()
        summary = (item.get('summary') or p.get('summary') or '').strip()
        authors = []
        for a in (p.get('authors') or []):
            name = a.get('name') if isinstance(a, dict) else None
            if name:
                authors.append(name)
        votes = p.get('upvotes', 0) or 0
        paper_url = f'https://arxiv.org/abs/{pid}' if pid else ''
        abstract2 = first_two_sentences(summary)
        # exclusion
        reason = is_excluded(title, summary)
        if reason:
            dropped.append({'id': pid, 'title': title, 'reason': reason, 'date': d})
            continue
        if SNN_RE.search(title) or SNN_RE.search(summary):
            snn_hits += 1
        records.append({
            'id': pid,
            'title': title,
            'abstract': abstract2,
            'authors': authors,
            'date': d,
            'paper_url': paper_url,
            'votes': votes,
        })

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print('TOTAL candidates:', len(records))
print('Per-day (raw API count):')
for d in days:
    fpath = os.path.join(TMP, 'hf_'+d.replace('-','')+'.json')
    raw = 0
    if os.path.exists(fpath):
        raw = len(json.load(open(fpath, encoding='utf-8')))
    kept = sum(1 for r in records if r['date']==d)
    print(f'  {d}: raw={raw} kept={kept}')
print('Dropped:', len(dropped))
for dp in dropped:
    print('  -', dp['date'], dp['reason'], dp['id'], dp['title'][:80])
print('SNN hits:', snn_hits)
print()
print('=== Top 10 by votes ===')
top = sorted(records, key=lambda r: r['votes'], reverse=True)[:10]
for i, r in enumerate(top, 1):
    print(f'{i:2}. [{r["votes"]:4}] {r["date"]} {r["id"]} {r["title"][:85]}')
