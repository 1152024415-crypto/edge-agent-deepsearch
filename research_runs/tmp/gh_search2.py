import os, json, urllib.request, urllib.parse
TOKEN = os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN')
def search(q):
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(q)}&per_page=8"
    req = urllib.request.Request(url, headers={"User-Agent":"edge-agent-research","Accept":"application/vnd.github+json"})
    if TOKEN: req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        for it in data.get("items", [])[:8]:
            print(f"  {it['full_name']} stars={it['stargazers_count']} pushed={it.get('pushed_at','')[:10]} archived={it.get('archived')} desc={(it.get('description') or '')[:80]}")
    except Exception as e:
        print("ERR", e)
print("=== lava neuromorphic ===")
search("lava neuromorphic")
print("=== lava framework intel ===")
search("lava framework intel")
