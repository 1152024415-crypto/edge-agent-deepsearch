"""Server-rendered shell for the paper radar page (signal-monitor terminal aesthetic)."""

INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RADAR · 端侧 AI Agent 信号</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *{box-sizing:border-box}
    :root{
      --bg:#eef1f3; --panel:#ffffff; --ink:#0b1a24; --muted:#5a6b78; --faint:#8a99a6;
      --rule:#d4dae0; --hair:#e3e8ec;
      --amber:#c2410c; --green:#15803d; --blue:#1d4ed8; --purple:#6d28d9; --slate:#64748b;
      --fx:#c2410c; --app:#15803d; --hw:#1d4ed8; --model:#6d28d9;
    }
    body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans","PingFang SC","Noto Sans SC",system-ui,sans-serif;font-size:14px;line-height:1.5}
    main{max-width:1100px;margin:0 auto;padding:20px 22px 80px}
    .mono{font-family:"IBM Plex Mono",ui-monospace,monospace}

    /* scope header */
    .scope{background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:14px 16px 0;margin-bottom:14px;overflow:hidden}
    .scope-top{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap}
    h1{margin:0;font-family:"IBM Plex Mono",monospace;font-size:22px;font-weight:600;letter-spacing:2px;color:var(--ink)}
    h1 .sub{font-family:"IBM Plex Sans",sans-serif;font-weight:500;font-size:13px;color:var(--muted);letter-spacing:0;margin-left:8px}
    .scope-stats{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--muted)}
    .scope-stats b{color:var(--ink);font-weight:600}
    .nav-link{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--amber);border:1px solid var(--amber);border-radius:3px;padding:3px 9px;text-decoration:none;white-space:nowrap}
    .nav-link:hover{background:var(--amber);color:#fff}
    .week-switch{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--amber);border:1px solid var(--amber);border-radius:3px;padding:3px 6px;background:#fbfcfd;cursor:pointer}
    .week-switch:hover{border-color:var(--ink)}
    .sweep{height:2px;margin:12px -16px 0;background:linear-gradient(90deg,transparent 0%,var(--hair) 20%,var(--hair) 80%,transparent 100%);position:relative;overflow:hidden}
    .sweep::after{content:"";position:absolute;inset:0;width:30%;background:linear-gradient(90deg,transparent,var(--amber),transparent);animation:sweep 3.2s linear infinite}
    @keyframes sweep{0%{transform:translateX(-100%)}100%{transform:translateX(400%)}}
    @media(prefers-reduced-motion:reduce){.sweep::after{animation:none;opacity:.5}}
    .controls{display:flex;gap:10px;align-items:center;padding:10px 0 12px;flex-wrap:wrap}
    .search{flex:1;min-width:180px;padding:6px 10px;border:1px solid var(--rule);border-radius:4px;background:#fbfcfd;font-family:"IBM Plex Sans",sans-serif;font-size:13px;color:var(--ink)}
    .search:focus{outline:none;border-color:var(--ink)}
    .sort{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--faint);display:flex;gap:4px;align-items:center}
    .sort button{border:1px solid var(--rule);background:#fbfcfd;color:var(--muted);font-family:inherit;font-size:11px;padding:3px 8px;border-radius:3px;cursor:pointer}
    .sort button.on{background:var(--ink);color:#fff;border-color:var(--ink)}

    /* agent-ranked recommendations — the primary desktop reading path */
    .recommendations{position:relative;overflow:hidden;background:var(--ink);color:#f4f0e8;border:1px solid #203642;border-radius:7px;padding:17px 19px 15px;margin-bottom:16px}
    .recommendations::after{content:"";position:absolute;right:-90px;top:-110px;width:280px;height:280px;border:1px solid rgba(194,65,12,.35);border-radius:50%;box-shadow:0 0 0 34px rgba(194,65,12,.08),0 0 0 68px rgba(194,65,12,.04);pointer-events:none}
    .rec-head{position:relative;z-index:1;display:flex;align-items:flex-end;justify-content:space-between;gap:20px;padding-bottom:12px;border-bottom:1px solid rgba(255,255,255,.14)}
    .rec-kicker{font-family:"IBM Plex Mono",monospace;font-size:10px;line-height:1.2;color:#f2a16f;letter-spacing:1.2px;text-transform:uppercase;margin-bottom:4px}
    .rec-head h2{margin:0;font-size:20px;line-height:1.2;font-weight:700;letter-spacing:.2px;color:#fffaf2}
    .rec-count{font-family:"IBM Plex Mono",monospace;color:#ffb27d;font-weight:600;margin-left:5px}
    .rec-note{max-width:430px;margin:0;color:#d5dfe4;font-size:13px;line-height:1.5;text-align:right}
    .rec-grid{position:relative;z-index:1;display:grid;grid-template-columns:1fr 1fr;column-gap:24px}
    .rec-item{display:grid;grid-template-columns:34px 1fr;gap:10px;padding:12px 0 11px;border-bottom:1px solid rgba(255,255,255,.12);color:inherit;text-decoration:none;min-width:0}
    .rec-item:nth-last-child(-n+2){border-bottom:0}
    .rec-item:hover .rec-title{color:#ffb27d}
    .rec-rank{font-family:"IBM Plex Mono",monospace;font-size:18px;line-height:1;color:#f0783c;padding-top:2px}
    .rec-body{min-width:0}
    .rec-meta{display:flex;align-items:center;gap:7px;flex-wrap:wrap;font-family:"IBM Plex Mono",monospace;font-size:11px;color:#b8c7cf;margin-bottom:4px}
    .rec-tier{color:#f6c5a8}
    .rec-score{color:#fffaf2;font-weight:600}
    .rec-title{display:block;color:#fffaf2;font-weight:700;font-size:16px;line-height:1.35;letter-spacing:.1px;transition:color .12s}
    .rec-summary{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;color:#dbe3e7;font-weight:400;font-size:12.75px;line-height:1.5;margin-top:4px}
    .rec-tags{display:flex;align-items:center;flex-wrap:wrap;gap:4px;margin-top:7px}
    .rec-tags b{font-family:"IBM Plex Mono",monospace;color:#91a3ad;font-size:10px;font-weight:500;margin-right:2px}
    .rec-tag{font-family:"IBM Plex Mono",monospace;color:#c9d5db;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.1);border-radius:3px;padding:1px 6px;font-size:10px;line-height:1.45}
    .rec-why{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;color:#d2dce1;font-size:12.5px;line-height:1.5;margin-top:7px}
    .rec-why b{color:#f6c5a8;font-weight:500}
    .rec-original{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;color:#91a3ad;font-size:10.5px;line-height:1.4;margin-top:5px}
    .rec-empty{position:relative;z-index:1;color:#cbd5da;font-size:13px;padding:15px 0 2px}
    .rec-more{position:relative;z-index:1;display:block;margin:11px auto 0;border:1px solid rgba(255,178,125,.72);border-radius:3px;background:transparent;color:#ffd0b0;font-family:"IBM Plex Mono",monospace;font-size:11px;padding:7px 14px;cursor:pointer}
    .rec-more:hover{background:#c2410c;color:#fff;border-color:#c2410c}

    /* weekly highlights */
    .weekly{background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:12px 15px;margin-bottom:18px}
    .weekly-title{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--amber);text-transform:uppercase;letter-spacing:.7px;margin-bottom:5px;font-weight:600}
    .weekly-ov{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;font-size:12.5px;color:var(--ink);line-height:1.55;margin-bottom:6px;max-width:1000px}
    .weekly-hl{display:grid;grid-template-columns:18px minmax(180px,auto) 1fr;gap:7px;align-items:baseline;padding:5px 0;border-top:1px solid var(--hair)}
    .weekly-hl:first-of-type{border-top:none}
    .weekly-num{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--amber);font-weight:600;min-width:16px}
    .weekly-topic{font-weight:600;font-size:13px;color:var(--ink);text-decoration:none}
    .weekly-topic:hover{color:var(--amber)}
    .weekly-why{color:var(--muted);font-size:12px;line-height:1.45;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .weekly-more{border-top:1px solid var(--hair);margin-top:2px;padding-top:2px}
    .weekly-more summary{list-style:none;cursor:pointer;font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--amber);padding:5px 0 1px}
    .weekly-more summary::-webkit-details-marker{display:none}
    .weekly-more[open] summary{margin-bottom:2px}

    /* complete weekly scan */
    .all-research{margin-top:2px}
    .all-head{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;padding:2px 1px 9px;border-bottom:1px solid var(--rule)}
    .all-kicker{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--faint);letter-spacing:.8px;text-transform:uppercase}
    .all-head h2{margin:2px 0 0;font-size:18px;line-height:1.25}
    .all-summary{font-size:12px;color:var(--muted);margin:0;text-align:right}
    /* filter */
    .filter{background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:10px 12px;margin-bottom:16px}
    .dim-group{display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin-bottom:5px}
    .dim-group:last-child{margin-bottom:0}
    .dim-label{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--faint);min-width:34px;text-transform:uppercase;letter-spacing:.5px}
    .ftag{padding:2px 8px;border:1px solid var(--rule);background:#fbfcfd;color:var(--muted);font-family:"IBM Plex Mono",monospace;font-size:11px;border-radius:3px;cursor:pointer;line-height:1.5}
    .ftag:hover{border-color:var(--ink);color:var(--ink)}
    .ftag.active[data-dim=方向]{background:var(--fx);color:#fff;border-color:var(--fx)}
    .ftag.active[data-dim=应用]{background:var(--app);color:#fff;border-color:var(--app)}
    .ftag.active[data-dim=硬件]{background:var(--hw);color:#fff;border-color:var(--hw)}
    .ftag.active[data-dim=模型]{background:var(--model);color:#fff;border-color:var(--model)}

    /* tier bands */
    section.band{margin-bottom:20px;scroll-margin-top:54px}
    /* sticky section tabs */
    .tabs{position:sticky;top:0;z-index:30;background:var(--bg);display:flex;gap:6px;flex-wrap:wrap;padding:8px 0 8px;margin-bottom:14px;border-bottom:1px solid var(--rule)}
    .tab{font-family:"IBM Plex Mono",monospace;font-size:11px;padding:4px 11px;border:1px solid var(--rule);border-radius:14px;background:var(--panel);color:var(--muted);cursor:pointer;line-height:1.5}
    .tab b{color:var(--ink);font-weight:600;margin-left:5px}
    .tab:hover{border-color:var(--ink);color:var(--ink)}
    .tab.active{background:var(--ink);color:#fff;border-color:var(--ink)}
    .tab.active b{color:#fff}
    .band-head{display:flex;align-items:center;gap:8px;margin:0 0 6px;padding:0 0 4px;border-bottom:1px solid var(--rule);cursor:pointer;user-select:none}
    .band-head:hover .band-title{color:var(--amber)}
    .fold{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--faint);transition:transform .15s;display:inline-block;width:10px}
    .band.collapsed .fold{transform:rotate(-90deg)}
    .band.collapsed .band-body{display:none}
    .band-body{}
    .band-bar{width:3px;height:14px;border-radius:1px}
    .band-title{font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:600;letter-spacing:.5px;text-transform:uppercase}
    .band-count{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--faint)}
    .band-meta{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--faint);margin-left:auto}

    /* signal row */
    .row{display:flex;align-items:baseline;gap:10px;padding:9px 12px;background:var(--panel);border:1px solid var(--hair);border-radius:5px;margin-bottom:6px;text-decoration:none;color:var(--ink);transition:border-color .12s,transform .06s}
    .row:hover{border-color:var(--rule);transform:translateX(2px)}
    .row.hi{border-left:3px solid var(--amber);padding-left:10px}
    .sig{display:flex;flex-direction:column;align-items:center;gap:3px;min-width:34px;flex-shrink:0}
    .sig-n{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;color:var(--ink)}
    .sig-n.hi{color:var(--amber)}
    .sig-bars{display:flex;gap:1.5px;align-items:flex-end;height:9px}
    .sig-bars i{width:3px;height:9px;background:var(--hair);border-radius:1px}
    .sig-bars i.on{background:var(--ink)}
    .sig-bars i.on.hi{background:var(--amber)}
    .tier{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--faint);flex-shrink:0}
    .date{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--faint);flex-shrink:0}
    .open{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--green);font-weight:600;flex-shrink:0}
    .rec-badge{font-family:"IBM Plex Mono",monospace;font-size:10px;color:#fff;background:var(--amber);font-weight:600;flex-shrink:0;padding:1px 6px;border-radius:3px}
    .row.rec{border-left:3px solid var(--amber);padding-left:10px}
    .ttl{font-weight:600;font-size:13.5px;flex:1;min-width:160px}
    .row:hover .ttl{color:var(--amber)}
    .tags{display:flex;flex-wrap:wrap;gap:3px;margin-top:4px}
    .tag{font-family:"IBM Plex Mono",monospace;font-size:10px;padding:1px 6px;border-radius:2px;line-height:1.5}
    .tag[data-dim=方向]{color:var(--fx);background:#fbeae3}
    .tag[data-dim=应用]{color:var(--app);background:#e3f0e8}
    .tag[data-dim=硬件]{color:var(--hw);background:#e3ecf8}
    .tag[data-dim=模型]{color:var(--model);background:#eee6f7}
    .abs{color:var(--muted);font-size:12px;line-height:1.5;margin-top:4px}
    .empty{color:var(--faint);font-family:"IBM Plex Mono",monospace;font-size:13px;padding:30px;text-align:center}

    /* detail overlay (rendered from inlined data — no server fetch, so a stale
       cached index never 404s when clicking a paper) */
    .overlay{position:fixed;inset:0;background:rgba(11,26,36,.45);backdrop-filter:blur(2px);z-index:50;display:flex;align-items:flex-start;justify-content:center;padding:40px 16px;overflow:auto}
    .overlay.hidden{display:none}
    .card{background:var(--panel);border:1px solid var(--rule);border-radius:8px;max-width:720px;width:100%;padding:20px 22px;box-shadow:0 8px 30px rgba(11,26,36,.18)}
    .card-close{float:right;cursor:pointer;font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--faint);border:1px solid var(--rule);border-radius:4px;padding:2px 9px;background:#fbfcfd}
    .card-close:hover{color:var(--ink);border-color:var(--ink)}
    .card-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--faint);margin:4px 0 10px}
    .card h2{margin:0 0 8px;font-size:17px;font-weight:700;line-height:1.35}
    .card .abs{margin:10px 0;color:var(--ink);font-size:13px}
    .card .field{margin:8px 0;font-size:12.5px;line-height:1.55}
    .card .field b{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--faint);font-weight:600;text-transform:uppercase;letter-spacing:.4px;margin-right:6px}
    .card .src{display:inline-block;margin-top:10px;font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--amber);text-decoration:none;border:1px solid var(--amber);border-radius:4px;padding:5px 10px}
    .card .src:hover{background:var(--amber);color:#fff}
    @media(max-width:640px){.row{flex-wrap:wrap}.ttl{min-width:100%}}
  </style>
</head>
<body>
  <main>
    <header class="scope">
      <div class="scope-top">
        <h1>RADAR<span class="sub">端侧 AI Agent 信号周报</span></h1>
        <div class="scope-stats" id="summary">scanning…</div>
        <a class="nav-link" href="notes.html">调研笔记 ↗</a>
        <a class="nav-link" href="snn.html">SNN 洞察 ↗</a>
        <a class="nav-link" href="waic.html">WAIC ↗</a>
        <select class="week-switch" id="week-switch" title="切换周"></select>
      </div>
      <div class="sweep"></div>
      <div class="controls">
        <input class="search" id="search" placeholder="搜索标题 / 关键词…" autocomplete="off">
        <div class="sort">sort
          <button id="sort-score" class="on">score</button>
          <button id="sort-date">date</button>
        </div>
      </div>
    </header>
    <section class="recommendations" id="recommendations" aria-live="polite"></section>
    <section class="weekly" id="weekly"></section>
    <section class="all-research" id="all-research">
      <header class="all-head">
        <div><div class="all-kicker">complete weekly scan</div><h2>完整调研</h2></div>
        <p class="all-summary" id="all-summary"></p>
      </header>
      <div class="tabs" id="tabs"></div>
      <div class="filter" id="filter"></div>
      <div id="papers"></div>
      <div id="trending"></div>
    </section>
    <div id="overlay" class="overlay hidden" onclick="if(event.target===this)closeDetail()"></div>
  </main>
  <script>
    let ALL=[], ACTIVE=new Set(), Q="", SORT="score", SHOW_ALL_RECOMMENDED=false;
    const REC_PREVIEW=6;
    const WEEKLY_PREVIEW=3;
    const TIER=[["官方动态","--amber"],["开源大项目","--green"],["公司项目","--blue"],["学校顶会","--purple"],["学校预印本","--slate"]];
    const isRecommended=p=>p.recommendation==='推荐';
    const hasContent=v=>v&&v!=='未报告';

    async function loadPapers(){
      const res = await fetch("/api/papers");
      const data = await res.json();
      ALL=data.papers||[];
      renderFilter(); renderRadar();
      attachSpy();
      document.querySelector("#summary").innerHTML=`<b>${ALL.length}</b> signals · 7-day window · <b>${range()}</b>`;
    }
    async function loadWeekly(){
      const wr = await fetch("/api/weekly");
      const w = await wr.json();
      const el=document.querySelector("#weekly");
      if(!w||!w.highlights||!w.highlights.length){el.innerHTML="";return;}
      const rows=(items,start)=>items.map((h,i)=>{
        const a=h.url
          ?`<a class="weekly-topic" href="${escapeAttr(h.url)}" target="_blank" rel="noopener">${escapeHtml(h.topic)}</a>`
          :`<a class="weekly-topic" href="/paper/${escapeAttr(h.paper_id)}">${escapeHtml(h.topic)}</a>`;
        return `<div class="weekly-hl"><span class="weekly-num">${start+i+1}</span>${a}<span class="weekly-why">— ${escapeHtml(h.why)}</span></div>`;
      }).join("");
      const first=w.highlights.slice(0,WEEKLY_PREVIEW);
      const rest=w.highlights.slice(WEEKLY_PREVIEW);
      el.innerHTML=`<div class="weekly-title">本周热点 · weekly signals</div>`+
        (w.overview?`<div class="weekly-ov">${escapeHtml(w.overview)}</div>`:"")+
        rows(first,0)+
        (rest.length?`<details class="weekly-more"><summary>展开其余 ${rest.length} 条热点 ↓</summary>${rows(rest,WEEKLY_PREVIEW)}</details>`:"");
    }
    function range(){const d=ALL.map(p=>p.date).sort();return d.length?`${d[0]} → ${d[d.length-1]}`:'';}

    function allTags(){const s=new Set();ALL.forEach(p=>(p.tags||[]).forEach(t=>s.add(t)));return[...s];}
    const dim=t=>t.split(":")[0], val=t=>t.split(":")[1]||t;

    function renderFilter(){
      const bd={};allTags().forEach(t=>{const d=dim(t);(bd[d]=bd[d]||[]).push(t)});
      document.querySelector("#filter").innerHTML=["方向","应用","硬件","模型"].filter(d=>bd[d]).map(d=>
        `<div class="dim-group"><span class="dim-label">${d}</span>`+
        bd[d].map(t=>`<button class="ftag${ACTIVE.has(t)?" active":""}" data-tag="${escapeAttr(t)}" data-dim="${d}">${escapeHtml(val(t))}</button>`).join("")+
        `</div>`).join("");
    }

    function visible(){
      let l=ALL.filter(p=>ACTIVE.size===0||(p.tags||[]).some(t=>ACTIVE.has(t)));
      if(Q){const q=Q.toLowerCase();l=l.filter(p=>((p.title_zh||'')+p.title+p.abstract+(p.tags||[]).join()+p.vendors).toLowerCase().includes(q));}
      l.sort((a,b)=>SORT==="score"?b.score-a.score||b.date.localeCompare(a.date):b.date.localeCompare(a.date));
      return l;
    }
    function sigBars(s){const n=Math.min(5,Math.max(1,Math.ceil(s/4)));const hi=s>=14;let r="";for(let i=0;i<5;i++)r+=`<i class="${i<n?'on':''} ${hi?'hi':''}"></i>`;return r;}

    function renderRecommendations(){
      const el=document.querySelector("#recommendations");
      if(!ALL.length){el.hidden=true;return;}
      el.hidden=false;
      const total=ALL.filter(isRecommended).length;
      const recommended=visible().filter(isRecommended).sort((a,b)=>{
        const tierDiff=TIER.findIndex(([t])=>t===a.source_tier)-TIER.findIndex(([t])=>t===b.source_tier);
        return tierDiff||b.score-a.score||b.date.localeCompare(a.date);
      });
      const countLabel=recommended.length===total?`${total}`:`${recommended.length}/${total}`;
      const previewLabel=SHOW_ALL_RECOMMENDED?`已展开 ${recommended.length} 条`:`首屏精选 ${Math.min(recommended.length,REC_PREVIEW)} 条`;
      const shown=SHOW_ALL_RECOMMENDED?recommended:recommended.slice(0,REC_PREVIEW);
      const items=shown.map((p,i)=>{
        const titleZh=(p.title_zh||'').trim()||p.title;
        const summary=(p.abstract||'').trim()||'暂无中文摘要';
        const tags=(p.tags||[]).map(t=>`<span class="rec-tag">${escapeHtml(val(t))}</span>`).join('');
        const reason=(p.recommendation_reason||'').trim()||'该条目由 Agent 选为本周优先阅读';
        return `<a class="rec-item" href="/paper/${escapeAttr(p.id)}" onclick="openDetail('${escapeAttr(p.id)}');return false;">
          <span class="rec-rank">${String(i+1).padStart(2,'0')}</span>
          <span class="rec-body"><span class="rec-meta"><span class="rec-tier">${escapeHtml(p.source_tier||'')}</span><span>${escapeHtml(p.date||'')}</span><span class="rec-score">${p.score}/20</span>${p.open_source?'<span class="open">OSS</span>':''}</span><span class="rec-title">${escapeHtml(titleZh)}</span><span class="rec-summary">${escapeHtml(summary)}</span><span class="rec-tags"><b>关键词</b>${tags}</span><span class="rec-why"><b>值得优先看：</b>${escapeHtml(reason)}</span><span class="rec-original">原标题：${escapeHtml(p.title)}</span></span>
        </a>`;
      }).join('');
      el.innerHTML=`<header class="rec-head"><div><div class="rec-kicker">Agent 精选 · 推荐优先</div><h2>Agent 本周推荐 <span class="rec-count">· ${previewLabel} · 共推荐 ${countLabel} 条</span></h2></div><p class="rec-note">完整收录仍保留在下方；这里仅把 Agent 判断更值得优先阅读的内容排到前面。</p></header>`+
        (items?`<div class="rec-grid">${items}</div>`:'<div class="rec-empty">当前搜索或标签筛选下没有 Agent 推荐，完整结果仍在下方。</div>')+
        (recommended.length>REC_PREVIEW?`<button class="rec-more" id="rec-toggle">${SHOW_ALL_RECOMMENDED?'收起推荐':'查看其余 '+(recommended.length-REC_PREVIEW)+' 条'}</button>`:'');
    }

    function renderRadar(){
      renderRecommendations();
      renderPapers();
      const matching=visible();
      const recCount=matching.filter(isRecommended).length;
      document.querySelector("#all-summary").textContent=`当前 ${matching.length} 条 · ${recCount} 条推荐已在上方展示 · 下方 ${matching.length-recCount} 条不重复`;
    }

    function renderRow(p){
      const hi=p.score>=14;
      const rec=p.recommendation==='推荐';
      const tags=(p.tags||[]).map(t=>`<span class="tag" data-dim="${dim(t)}">${escapeHtml(val(t))}</span>`).join("");
      return`<a class="row${hi?' hi':''}${rec?' rec':''}" href="/paper/${escapeAttr(p.id)}" onclick="openDetail('${escapeAttr(p.id)}');return false;">
        <span class="sig"><span class="sig-n${hi?' hi':''}">${p.score}</span><span class="sig-bars">${sigBars(p.score)}</span></span>
        <span class="tier">${escapeHtml(p.source_tier||'')}</span>
        ${rec?'<span class="rec-badge">推荐</span>':''}
        ${p.open_source?'<span class="open">OSS</span>':''}
        <span class="date">${p.date}</span>
        <span class="ttl">${escapeHtml(p.title)}</span>
        ${tags?`<span class="tags">${tags}</span>`:''}
        <span class="abs">${escapeHtml(p.abstract||'')}</span>
      </a>`;
    }

    function openDetail(id){
      const p=ALL.find(x=>x.id===id);
      const ov=document.querySelector("#overlay");
      if(!p){ov.classList.add("hidden");return;}
      const tags=(p.tags||[]).map(t=>`<span class="tag" data-dim="${dim(t)}">${escapeHtml(val(t))}</span>`).join("");
      const hi=p.score>=14;
      ov.innerHTML=`<div class="card">
        <span class="card-close" onclick="closeDetail()">esc ✕</span>
        <div class="card-meta"><span class="band-bar" style="display:inline-block;width:3px;height:12px;background:var(--ink)"></span><span class="tier">${escapeHtml(p.source_tier||'')}</span>${p.open_source?'<span class="open">OSS</span>':''}<span class="date">${p.date}</span><span>score ${p.score}</span><span>(${p.score_relevance||0}+${p.score_contribution||0})</span></div>
        <h2>${escapeHtml(p.title)}</h2>
        ${tags?`<div class="tags">${tags}</div>`:''}
        <div class="abs">${escapeHtml(p.abstract||'')}</div>
        ${hasContent(p.effects)?`<div class="field"><b>effects</b>${escapeHtml(p.effects)}</div>`:''}
        ${hasContent(p.mechanism)?`<div class="field"><b>mechanism</b>${escapeHtml(p.mechanism)}</div>`:''}
        ${p.score_reason?`<div class="field"><b>评分依据</b>${escapeHtml(p.score_reason)}</div>`:''}
        ${p.authors?`<div class="field"><b>authors</b>${escapeHtml(p.authors)}</div>`:''}
        ${p.vendors?`<div class="field"><b>vendors</b>${escapeHtml(p.vendors)}</div>`:''}
        ${p.venue?`<div class="field"><b>venue</b>${escapeHtml(p.venue)}</div>`:''}
        ${p.paper_url?`<a class="src" href="${escapeAttr(p.paper_url)}" target="_blank" rel="noopener">原文 ↗ ${escapeHtml(p.paper_url.replace(/^https?:\/\//,'').split('/')[0])}</a>`:''}
      </div>`;
      ov.classList.remove("hidden");
      document.body.style.overflow="hidden";
    }
    function closeDetail(){const ov=document.querySelector("#overlay");ov.classList.add("hidden");ov.innerHTML="";document.body.style.overflow="";}
    document.addEventListener("keydown",e=>{if(e.key==="Escape")closeDetail();});

    function renderPapers(){
      const l=visible().filter(p=>!isRecommended(p)),el=document.querySelector("#papers");
      if(!l.length){el.innerHTML=`<div class="empty">${visible().length?'当前结果均已在 Agent 推荐中展示':'no signal — 调整筛选或搜索'}</div>`;renderTabs({});return;}
      const g={};l.forEach(p=>{(g[p.source_tier]=g[p.source_tier]||[]).push(p)});
      const COLLAPSE=25;  // sections with more rows than this start collapsed
      el.innerHTML=TIER.filter(([t])=>g[t]).map(([t,c])=>{
        const cl=g[t].length>COLLAPSE?' collapsed':'';
        return `<section class="band${cl}" id="band-${escapeAttr(t)}"><div class="band-head" onclick="this.parentElement.classList.toggle('collapsed')"><span class="fold">▾</span><span class="band-bar" style="background:${c}"></span><span class="band-title">${t}</span><span class="band-count">${g[t].length}</span>${g[t].length>COLLAPSE?'<span class="band-meta">点击展开</span>':''}</div>`+
        `<div class="band-body">`+g[t].map(renderRow).join("")+`</div></section>`;
      }).join("");
      renderTabs(g);
    }

    function renderTabs(g){
      g=g||{};
      const tabs=TIER.filter(([t])=>g[t]).map(([t,c])=>`<button class="tab" data-target="band-${escapeAttr(t)}">${t}<b>${g[t].length}</b></button>`);
      const tn=(window.__TRENDING__&&window.__TRENDING__.items)?window.__TRENDING__.items.length:(window.__TRENDING__||[]).length;
      if(tn) tabs.push(`<button class="tab" data-target="band-trending">GitHub 热榜<b>${tn}</b></button>`);
      document.querySelector("#tabs").innerHTML=tabs.join("");
    }

    function renderTrendingRow(r){
      return`<a class="row" href="${escapeAttr(r.url)}" target="_blank" rel="noopener">
        <span class="sig"><span class="sig-n">${r.rank}</span><span class="sig-bars">${sigBars(parseInt((r.week||'0').replace(/,/g,''))/2000)}</span></span>
        <span class="tier">trending</span>
        <span class="date">+${escapeHtml(r.week||'')}/wk</span>
        <span class="ttl">${escapeHtml(r.repo)}</span>
        <span class="abs">${escapeHtml(r.desc||'')}</span>
        <span class="open">${escapeHtml(r.total||'')}★</span>
      </a>`;
    }
    function renderTrending(list){
      const el=document.querySelector("#trending");
      if(!list||!list.length){el.innerHTML="";return;}
      el.innerHTML=`<section class="band" id="band-trending"><div class="band-head" onclick="this.parentElement.classList.toggle('collapsed')"><span class="fold">▾</span><span class="band-bar" style="background:var(--slate)"></span><span class="band-title">GitHub 热榜 · 本周 Top ${list.length}</span><span class="band-count">${list.length}</span><span class="band-meta">未筛选 · github.com/trending</span></div>`+
        `<div class="band-body">`+list.map(renderTrendingRow).join("")+`</div></section>`;
    }
    async function loadTrending(){
      let data = window.__TRENDING__ || null;
      if(!data){try{const r=await fetch("/api/trending");data=await r.json();}catch(e){return;}}
      renderTrending(data.items||data||[]);
      attachSpy();
    }

    document.querySelector("#recommendations").addEventListener("click",e=>{const b=e.target.closest("#rec-toggle");if(!b)return;SHOW_ALL_RECOMMENDED=!SHOW_ALL_RECOMMENDED;renderRecommendations();});
    document.querySelector("#filter").addEventListener("click",e=>{const b=e.target.closest(".ftag");if(!b)return;const t=b.dataset.tag;ACTIVE.has(t)?ACTIVE.delete(t):ACTIVE.add(t);renderFilter();renderRadar();});
    document.querySelector("#search").addEventListener("input",e=>{Q=e.target.value.trim();SHOW_ALL_RECOMMENDED=false;renderRadar();});
    document.querySelector("#sort-score").addEventListener("click",()=>{SORT="score";document.querySelector("#sort-score").classList.add("on");document.querySelector("#sort-date").classList.remove("on");renderRadar();});
    document.querySelector("#sort-date").addEventListener("click",()=>{SORT="date";document.querySelector("#sort-date").classList.add("on");document.querySelector("#sort-score").classList.remove("on");renderRadar();});

    // sticky tab bar: click → expand + scroll to section
    document.querySelector("#tabs").addEventListener("click",e=>{
      const b=e.target.closest(".tab");if(!b)return;
      const tgt=document.getElementById(b.dataset.target);if(!tgt)return;
      tgt.classList.remove("collapsed");
      tgt.scrollIntoView({behavior:"smooth",block:"start"});
    });
    // scroll-spy: highlight the tab of the section currently in view
    const spy=new IntersectionObserver((ents)=>{
      ents.forEach(en=>{if(en.isIntersecting){const id=en.target.id;document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("active",t.dataset.target===id));}});
    },{rootMargin:"-45% 0px -50% 0px"});
    function attachSpy(){document.querySelectorAll("section.band[id]").forEach(s=>spy.observe(s));}

    function escapeHtml(v){return String(v||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
    function escapeAttr(v){return escapeHtml(v).replace(/`/g,"&#96;");}
    function renderWeekSwitch(){
      const ws=window.__WEEKS__||[];
      const sel=document.querySelector('#week-switch');
      if(!ws.length){sel.style.display='none';return;}
      const mine=window.__WEEK_LABEL__||null;
      sel.innerHTML=ws.map(w=>{
        const isMine=(w.current&&mine===null)||(w.label===mine);
        return `<option value="${escapeAttr(w.href)}"${isMine?' selected':''}>${w.current?'本周 · ':''}${escapeHtml(w.title)}</option>`;
      }).join('');
    }
    document.querySelector('#week-switch').addEventListener('change',e=>{if(e.target.value&&e.target.value!==location.pathname)location.href=e.target.value;});
    window.addEventListener("pageshow",renderWeekSwitch);
    renderWeekSwitch();
    loadPapers().catch(e=>{document.querySelector("#summary").textContent=`读取失败：${e}`;});
    loadWeekly().catch(()=>{});
    loadTrending().catch(()=>{});
  </script>
</body>
</html>
"""
