import os, json, urllib.request, urllib.error
TOKEN = os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN')
url = "https://api.github.com/repos/lava-nc/lava"
req = urllib.request.Request(url, headers={"User-Agent":"edge-agent-research","Accept":"application/vnd.github+json"})
if TOKEN: req.add_header("Authorization", f"Bearer {TOKEN}")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    out = {
        "name":"Lava",
        "full_name": data.get("full_name"),
        "stargazers_count": data.get("stargazers_count"),
        "pushed_at": (data.get("pushed_at") or "")[:10],
        "language": data.get("language"),
        "license": (data.get("license") or {}).get("spdx_id") if data.get("license") else None,
        "archived": bool(data.get("archived")),
        "description": data.get("description"),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    json.dump([out], open("research_runs/tmp/gh_lava.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
except Exception as e:
    print("ERR", e)
