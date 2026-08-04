import os, json, time, urllib.request, urllib.error
TOKEN = os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN')
repos = [
    ("fangwei123456","spikingjelly","SpikingJelly"),
    ("snf-lab","snnTorch","snnTorch"),
    ("BindsNET","bindsnet","BindsNET"),
    ("brian-team","brian2","Brian2"),
    ("intel","neuromorphic","Lava"),
    ("norse","norse","Norse"),
    ("synsense","sinabs","Sinabs"),
    ("nest","nest-simulator","NEST"),
]
out = []
for owner, repo, name in repos:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    req = urllib.request.Request(url, headers={
        "User-Agent":"edge-agent-research",
        "Accept":"application/vnd.github+json",
    })
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            out.append({
                "name": name,
                "full_name": data.get("full_name"),
                "stargazers_count": data.get("stargazers_count"),
                "pushed_at": (data.get("pushed_at") or "")[:10],
                "language": data.get("language"),
                "license": (data.get("license") or {}).get("spdx_id") if data.get("license") else None,
                "archived": bool(data.get("archived")),
                "description": data.get("description"),
            })
            print(f"OK {owner}/{repo} stars={data.get('stargazers_count')} pushed={data.get('pushed_at')}")
            break
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code} {owner}/{repo} attempt {attempt+1}")
            if e.code in (429, 403):
                time.sleep(30)
            else:
                time.sleep(5)
        except Exception as e:
            print(f"ERR {owner}/{repo}: {e}")
            time.sleep(5)
    time.sleep(3)
json.dump(out, open("research_runs/tmp/gh_frameworks.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("DONE")
