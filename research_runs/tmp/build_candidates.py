import json, re
from collections import Counter

KEYWORDS = [
    'on-device','edge','mobile','embedded','NPU','agent','quantiz','KV cache',
    'speculative decoding','spiking','SNN','neuromorphic','TinyML','IoT','federated',
    'efficient inference','lightweight','small language model','SLM','VLM','multimodal',
    'LLM deployment','model compression','pruning','distillation','MoE','long context',
    'tool use','reasoning'
]
KW_LOWER = [k.lower() for k in KEYWORDS]
SNN_KW_LOWER = ['spiking','snn','neuromorphic']

def get_authors(p):
    names = []
    for a in p.get('paper', {}).get('authors', []):
        n = a.get('name') or (a.get('user', {}) or {}).get('fullname')
        if n:
            names.append(n)
    return names

def abstract_2sent(s):
    if not s:
        return ''
    s = s.strip()
    parts = re.split(r'(?<=[\.!\?])\s+', s)
    return ' '.join(parts[:2])

def get_votes(p):
    v = p.get('paper', {}).get('upvotes')
    if v is None:
        v = p.get('upvotes')
    return v

records = []
for d in ['0727', '0728', '0729']:
    with open(f'D:/proj/edge_agent/research_runs/tmp/hf_{d}.json', encoding='utf-8') as f:
        data = json.load(f)
    date = '2026-07-' + d[2:]
    for p in data:
        paper = p.get('paper', {})
        pid = paper.get('id') or p.get('id')
        title = paper.get('title') or p.get('title', '')
        summary = paper.get('summary') or p.get('summary', '') or ''
        votes = get_votes(p)
        authors = get_authors(p)
        paper_url = f'https://arxiv.org/abs/{pid}' if pid else ''
        rec = {'id': pid,'title': title,'abstract': abstract_2sent(summary),'authors': authors,'date': date,'paper_url': paper_url,'votes': votes}
        records.append(rec)

def is_relevant(rec):
    text = (rec['title'] + ' ' + rec['abstract']).lower()
    for k in KW_LOWER:
        if k in text:
            return True, k
    if rec['votes'] and rec['votes'] > 30:
        return True, 'high_votes'
    return False, None

def is_excluded(rec):
    t = rec['title'].lower()
    if 'gui' in t and ('automat' in t or 'click' in t or 'screen' in t):
        return True
    return False

candidates = []
for r in records:
    rel, kw = is_relevant(r)
    if not rel:
        continue
    if is_excluded(r):
        continue
    r['match_reason'] = kw
    candidates.append(r)

print(f'Total raw records: {len(records)}')
print(f'Candidates after filter: {len(candidates)}')
dayc = Counter(r['date'] for r in candidates)
for d in sorted(dayc):
    print(f'  {d}: {dayc[d]}')

top = sorted(candidates, key=lambda x: x['votes'] or 0, reverse=True)[:10]
print('\nTOP 10 by votes:')
for r in top:
    print(f"  [{r['votes']}] {r['date']} {r['title']} | {r['paper_url']}")

snn = [r for r in candidates if any(k in (r['title'] + ' ' + r['abstract']).lower() for k in SNN_KW_LOWER)]
print(f'\nSNN/spiking/neuromorphic hits: {len(snn)}')
for r in snn:
    print(f"  {r['date']} {r['title']} | {r['paper_url']}")

with open('D:/proj/edge_agent/research_runs/candidates-hf.json', 'w', encoding='utf-8') as f:
    json.dump(candidates, f, ensure_ascii=False, indent=2)
print('\nWROTE: D:/proj/edge_agent/research_runs/candidates-hf.json')
