import os, json, urllib.request
TOKEN = os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN')
def search(q):
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(q)}&per_page=5"
    req = urllib.request.Request(url, headers={"User-Agent":"edge-agent-research","Accept":"application/vnd.github+json"})
    if TOKEN: req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        for it in data.get("items", [])[:5]:
            print(f"  {it['full_name']} stars={it['stargazers_count']} pushed={it.get('pushed_at','')[:10]} archived={it.get('archived')}")
    except Exception as e:
        print("ERR", e)
import urllib.parse
print("=== snnTorch ===")
search("snnTorch in:name")
print("=== Lava neuromorphic intel ===")
search("lava neuromorphic intel in:name")
