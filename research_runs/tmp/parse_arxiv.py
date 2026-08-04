import re, json, xml.etree.ElementTree as ET
ns = {"a":"http://www.w3.org/2005/Atom"}
tree = ET.parse("research_runs/tmp/arxiv_snn.xml")
root = tree.getroot()
entries = root.findall("a:entry", ns)
print("total entries:", len(entries))

# SNN strict criteria
snn_patterns = [
    r"spiking\s+neural\s+network",
    r"spikformer",
    r"spiking\s+transformer",
    r"spiking\s+neuron\s+model",
    r"\bsnn\b",
]
def is_snn(text):
    t = (text or "").lower()
    return any(re.search(p, t) for p in snn_patterns)

# date window
from datetime import date
start = date(2026,4,15)
end = date(2026,7,15)

out = []
for e in entries:
    id_e = e.find("a:id", ns)
    title_e = e.find("a:title", ns)
    pub_e = e.find("a:published", ns)
    sum_e = e.find("a:summary", ns)
    id_v = id_e.text.strip() if id_e is not None else ""
    title = (title_e.text or "").strip().replace("\n"," ") if title_e is not None else ""
    pub = (pub_e.text or "")[:10] if pub_e is not None else ""
    summary = (sum_e.text or "").strip().replace("\n"," ") if sum_e is not None else ""
    # date filter
    try:
        pd = date.fromisoformat(pub)
    except:
        continue
    if not (start <= pd <= end):
        continue
    # SNN filter: check title+summary
    if not is_snn(title + " " + summary):
        continue
    # extract arxiv id
    m = re.search(r"arxiv\.org/abs/([^/]+)$", id_v)
    aid = m.group(1) if m else id_v
    out.append({
        "arxiv_id": aid,
        "url": id_v,
        "title": title,
        "published": pub,
        "summary": summary,
    })

# sort by date desc
out.sort(key=lambda x: x["published"], reverse=True)
print("in window + SNN:", len(out))
json.dump(out, open("research_runs/tmp/arxiv_snn_filtered.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
for o in out[:25]:
    print(f"{o['published']} | {o['arxiv_id']} | {o['title'][:90]}")
