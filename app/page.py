"""Server-rendered shell for the desktop weekly edge-AI research radar."""

INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RADAR · 端侧 AI Agent 周报</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *{box-sizing:border-box}
    :root{
      --canvas:#e9e6de;--paper:#f8f6f0;--panel:#fffdf8;--ink:#202622;--muted:#657069;
      --faint:#8b938e;--rule:#cfcfc7;--hair:#e2e0d8;--rust:#aa4827;--rust-soft:#f3dfd5;
      --moss:#416a50;--moss-soft:#e3ede5;--blue:#365f7c;--blue-soft:#e2eaf0;
      --violet:#655879;--violet-soft:#ebe6ef;--slate:#707873;--slate-soft:#eaedea;
      --amber:#aa4827;--green:#416a50;--purple:#655879;
      --fx:#a84324;--app:#356548;--hw:#315d79;--model:#675376;
    }
    html{scroll-behavior:smooth}
    body{margin:0;background:var(--canvas);color:var(--ink);font-family:"IBM Plex Sans","PingFang SC","Noto Sans SC",sans-serif;font-size:14px;line-height:1.55}
    button,input,select{font:inherit}
    button,a,select,input{outline-offset:3px}
    button:focus-visible,a:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid var(--rust)}
    main{max-width:1240px;margin:0 auto;padding:28px 28px 96px}
    .mono{font-family:"IBM Plex Mono",ui-monospace,monospace}
    .sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
    .eyebrow{margin:0 0 4px;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;font-weight:600;letter-spacing:1.15px;text-transform:uppercase;color:var(--rust)}
    .section-head{display:flex;align-items:flex-end;justify-content:space-between;gap:28px;padding-bottom:13px;border-bottom:1px solid var(--rule)}
    .section-head h2{margin:0;font-size:clamp(22px,2.2vw,31px);line-height:1.12;letter-spacing:-.02em}
    .section-note{max-width:520px;margin:0;color:var(--muted);font-size:13px;line-height:1.55;text-align:right}

    /* masthead */
    .masthead{background:var(--paper);border:1px solid var(--rule);border-top:4px solid var(--ink);padding:20px 22px 16px;margin-bottom:18px}
    .masthead-main{display:grid;grid-template-columns:minmax(300px,1fr) auto;gap:30px;align-items:end}
    .brand{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
    h1{margin:0;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:29px;line-height:1;font-weight:600;letter-spacing:4px}
    .brand-copy{font-size:15px;font-weight:600;color:var(--muted)}
    .brand-deck{margin:9px 0 0;max-width:620px;color:var(--muted);font-size:12.5px}
    .scope-stats{display:grid;grid-template-columns:repeat(4,minmax(82px,auto));gap:18px;align-items:end;text-align:right}
    .scope-stats span{display:block;min-width:0}
    .scope-stats b{display:block;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:18px;line-height:1.1;color:var(--ink)}
    .scope-stats small{display:block;margin-top:4px;color:var(--faint);font-size:10px;white-space:nowrap}
    .masthead-foot{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-top:17px;padding-top:13px;border-top:1px solid var(--hair)}
    .nav{display:flex;gap:8px;flex-wrap:wrap}
    .nav-link{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10.5px;color:var(--ink);border-bottom:1px solid var(--rule);padding:3px 0;text-decoration:none}
    .nav-link:hover{color:var(--rust);border-color:var(--rust)}
    .week-switch{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;color:var(--ink);border:1px solid var(--rule);background:var(--panel);padding:6px 10px;cursor:pointer}

    /* editorial recommendation roster */
    .recommendations{background:var(--paper);border:1px solid var(--rule);border-top:4px solid var(--rust);padding:20px 22px 12px;margin-bottom:18px}
    .rec-head{display:flex;align-items:flex-end;justify-content:space-between;gap:28px;padding-bottom:15px;border-bottom:1px solid var(--rule)}
    .rec-head h2{margin:0;font-size:clamp(23px,2.5vw,33px);line-height:1.08}
    .rec-count{font-family:"IBM Plex Mono",ui-monospace,monospace;color:var(--rust);font-size:12px;font-weight:500;letter-spacing:0}
    .rec-note{max-width:520px;margin:0;color:var(--muted);font-size:13px;line-height:1.55;text-align:right}
    .rec-list{position:relative}
    .rec-item{display:grid;grid-template-columns:72px minmax(0,1fr) minmax(260px,360px);gap:22px;padding:18px 4px;border-bottom:1px solid var(--hair);color:inherit;text-decoration:none;content-visibility:auto;contain-intrinsic-size:142px}
    .rec-item:last-child{border-bottom:0}
    .rec-item:hover{background:color-mix(in srgb,var(--rust-soft) 34%,transparent)}
    .rec-rank{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:26px;line-height:1;color:var(--rust);letter-spacing:-1px}
    .rec-rank::after{content:"";display:block;width:28px;height:2px;margin-top:10px;background:var(--rust)}
    .rec-main,.rec-editorial{min-width:0}
    .rec-meta{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-bottom:7px;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10.5px;color:var(--faint)}
    .rec-edge-scope{color:var(--ink);background:var(--rust-soft);border:1px solid color-mix(in srgb,var(--rust) 38%,var(--rule));padding:2px 7px;font-weight:600}
    .rec-tier{color:var(--rust);font-weight:500}
    .rec-score{color:var(--ink);font-weight:600}
    .rec-title{display:block;color:var(--ink);font-weight:700;font-size:clamp(17px,1.65vw,21px);line-height:1.3;letter-spacing:-.01em}
    .rec-summary{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;color:var(--muted);font-size:13.5px;line-height:1.6;margin-top:6px}
    .rec-tags{display:flex;align-items:center;flex-wrap:wrap;gap:5px;margin-top:10px}
    .rec-tags b{font-family:"IBM Plex Mono",ui-monospace,monospace;color:var(--faint);font-size:9.5px;font-weight:500;margin-right:3px}
    .rec-tag{font-family:"IBM Plex Mono",ui-monospace,monospace;color:var(--muted);background:var(--panel);border:1px solid var(--hair);padding:2px 6px;font-size:9.5px;line-height:1.45}
    .rec-editorial{border-left:2px solid var(--rust-soft);padding-left:18px;align-self:stretch}
    .rec-why{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden;color:var(--ink);font-size:12.5px;line-height:1.6;margin:0}
    .rec-why b{display:block;margin-bottom:3px;font-family:"IBM Plex Mono",ui-monospace,monospace;color:var(--rust);font-size:9.5px;letter-spacing:.65px}
    .rec-original{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;color:var(--faint);font-size:10.5px;line-height:1.45;margin-top:10px}
    .rec-empty{color:var(--muted);font-size:13px;padding:22px 0 10px}
    .rec-more,.trending-more{display:block;margin:12px auto 2px;border:1px solid var(--rust);background:transparent;color:var(--rust);font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10.5px;padding:7px 15px;cursor:pointer}
    .rec-more:hover,.trending-more:hover{background:var(--rust);color:var(--paper)}

    /* weekly editorial layer */
    .weekly{background:var(--panel);border:1px solid var(--rule);padding:20px 22px;margin-bottom:26px}
    .weekly-grid{display:grid;grid-template-columns:minmax(0,1.12fr) minmax(360px,.88fr);gap:34px;padding-top:17px}
    .weekly-overview{padding-right:28px;border-right:1px solid var(--hair)}
    .weekly-label{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;color:var(--rust);letter-spacing:.8px;margin-bottom:8px}
    .weekly-ov{margin:0;font-size:14px;color:var(--ink);line-height:1.8}
    .weekly-stories h3{margin:0 0 4px;font-size:13px}
    .weekly-hl{display:grid;grid-template-columns:24px minmax(150px,.75fr) minmax(0,1fr);gap:8px;align-items:baseline;padding:8px 0;border-top:1px solid var(--hair)}
    .weekly-num{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;color:var(--rust);font-weight:600}
    .weekly-topic{font-weight:600;font-size:12.5px;color:var(--ink);text-decoration:none}
    .weekly-topic:hover{color:var(--rust)}
    .weekly-why{color:var(--muted);font-size:11.5px;line-height:1.5}
    .weekly-more{border-top:1px solid var(--hair);margin-top:2px}
    .weekly-more summary{list-style:none;cursor:pointer;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;color:var(--rust);padding:8px 0 0}
    .weekly-more summary::-webkit-details-marker{display:none}

    /* complete library */
    .all-research{scroll-margin-top:12px}
    .all-head{padding:0 1px 12px}
    .all-summary{font-size:12px;color:var(--muted);margin:0;text-align:right}
    .source-map{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));border:1px solid var(--rule);background:var(--panel);margin:15px 0 12px}
    .source-card{display:grid;grid-template-rows:auto auto 1fr;gap:3px;min-height:96px;padding:13px 14px;border:0;border-right:1px solid var(--hair);background:transparent;color:var(--ink);text-align:left;cursor:pointer}
    .source-card:last-child{border-right:0}
    .source-card:hover,.source-card.active{background:var(--slate-soft)}
    .source-card.active{box-shadow:inset 0 -3px 0 var(--rust)}
    .source-card b{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:20px;line-height:1}
    .source-card span{font-size:12px;font-weight:600}
    .source-card small{font-size:10.5px;line-height:1.4;color:var(--muted)}
    .library-tools{display:grid;grid-template-columns:minmax(280px,1fr) auto;gap:12px;padding:12px 14px;background:var(--panel);border:1px solid var(--rule);margin-bottom:10px}
    .search{width:100%;padding:8px 10px;border:1px solid var(--rule);background:var(--paper);font-size:13px;color:var(--ink)}
    .search:focus{border-color:var(--rust)}
    .sort{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;color:var(--faint);display:flex;gap:5px;align-items:center}
    .sort button{border:1px solid var(--rule);background:var(--paper);color:var(--muted);font-family:inherit;font-size:10.5px;padding:5px 9px;cursor:pointer}
    .sort button.on{background:var(--ink);color:var(--paper);border-color:var(--ink)}
    .filter-shell{background:var(--panel);border:1px solid var(--rule);padding:11px 13px}
    .filter-shell.advanced{border-top:0;background:color-mix(in srgb,var(--panel) 70%,var(--slate-soft))}
    .dim-group{display:flex;flex-wrap:wrap;gap:5px;align-items:center;margin-bottom:7px}
    .dim-group:last-child{margin-bottom:0}
    .dim-label{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:9.5px;color:var(--faint);min-width:42px;letter-spacing:.45px}
    .ftag{padding:3px 8px;border:1px solid var(--hair);background:var(--paper);color:var(--muted);font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;cursor:pointer;line-height:1.5}
    .ftag:hover{border-color:var(--ink);color:var(--ink)}
    .ftag.active{background:var(--ink);color:var(--paper);border-color:var(--ink)}
    .ftag.active[data-dim=方向]{background:var(--fx);border-color:var(--fx)}
    .ftag.active[data-dim=应用]{background:var(--app);border-color:var(--app)}
    .ftag.active[data-dim=硬件]{background:var(--hw);border-color:var(--hw)}
    .ftag.active[data-dim=模型]{background:var(--model);border-color:var(--model)}
    .filter-actions{display:flex;justify-content:space-between;align-items:center;padding:7px 1px 4px}
    .filter-action{border:0;background:transparent;color:var(--rust);font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;padding:4px 1px;cursor:pointer}
    .filter-action:disabled{color:var(--faint);cursor:default}
    .tabs{position:sticky;top:0;z-index:30;background:color-mix(in srgb,var(--canvas) 94%,transparent);display:flex;gap:6px;flex-wrap:wrap;padding:9px 0;margin:8px 0 11px;border-bottom:1px solid var(--rule)}
    .tab{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10.5px;padding:4px 10px;border:1px solid var(--rule);border-radius:14px;background:var(--panel);color:var(--muted);cursor:pointer;line-height:1.5}
    .tab b{color:var(--ink);font-weight:600;margin-left:5px}
    .tab.active{background:var(--ink);color:var(--paper);border-color:var(--ink)}
    .tab.active b{color:var(--paper)}
    section.band{margin-bottom:18px;scroll-margin-top:58px;content-visibility:auto;contain-intrinsic-size:500px}
    .band-head{display:flex;width:100%;align-items:center;gap:8px;margin:0 0 7px;padding:5px 1px;border:0;border-bottom:1px solid var(--rule);background:transparent;color:var(--ink);cursor:pointer;text-align:left}
    .band-head:hover .band-title{color:var(--rust)}
    .fold{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;color:var(--faint);transition:transform .15s;display:inline-block;width:10px}
    .band.collapsed .fold{transform:rotate(-90deg)}
    .band.collapsed .band-body{display:none}
    .band-bar{width:3px;height:14px}
    .band-title{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11.5px;font-weight:600;letter-spacing:.45px}
    .band-count{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10.5px;color:var(--faint)}
    .band-meta{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:9.5px;color:var(--faint);margin-left:auto}
    .signal-row{display:grid;grid-template-columns:48px minmax(0,1fr);gap:12px;padding:11px 13px;background:var(--panel);border:1px solid var(--hair);margin-bottom:6px;text-decoration:none;color:var(--ink);transition:border-color .12s,transform .08s;content-visibility:auto;contain-intrinsic-size:106px}
    .signal-row:hover{border-color:var(--rule);transform:translateX(2px)}
    .signal-row.rec{border-left:3px solid var(--rust);padding-left:11px}
    .sig{display:flex;flex-direction:column;align-items:center;gap:4px;padding-top:2px}
    .sig-n{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:14px;font-weight:600;color:var(--ink)}
    .sig-n.hi{color:var(--rust)}
    .sig-bars{display:flex;gap:1.5px;align-items:flex-end;height:9px}
    .sig-bars i{width:3px;height:9px;background:var(--hair)}
    .sig-bars i.on{background:var(--ink)}
    .sig-bars i.on.hi{background:var(--rust)}
    .row-body{min-width:0}
    .row-meta{display:flex;align-items:center;gap:7px;flex-wrap:wrap;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:9.5px;color:var(--faint)}
    .tier{color:var(--faint)}
    .date{color:var(--faint)}
    .open{color:var(--moss);font-weight:600}
    .rec-badge{color:var(--paper);background:var(--rust);font-weight:600;padding:1px 6px}
    .ttl{display:block;margin-top:3px;font-weight:600;font-size:13.5px;line-height:1.42}
    .signal-row:hover .ttl{color:var(--rust)}
    .abs{color:var(--muted);font-size:12px;line-height:1.55;margin-top:4px}
    .tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
    .tag{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:9.5px;padding:1px 6px;line-height:1.5}
    .tag[data-dim=方向]{color:var(--fx);background:#f5e4dc}
    .tag[data-dim=应用]{color:var(--app);background:#e4eee7}
    .tag[data-dim=硬件]{color:var(--hw);background:#e3ebf0}
    .tag[data-dim=模型]{color:var(--model);background:#ece6f0}
    .empty{color:var(--muted);font-size:13px;padding:34px 18px;text-align:center;border:1px dashed var(--rule);background:var(--panel)}
    .empty button{display:block;margin:10px auto 0;border:1px solid var(--rust);background:transparent;color:var(--rust);padding:5px 10px;cursor:pointer}

    /* unverified discovery stream */
    .discovery{margin-top:35px;padding-top:20px;border-top:4px double var(--rule)}
    .discovery-note{display:inline-block;margin:12px 0 10px;padding:5px 8px;background:var(--slate-soft);color:var(--muted);font-size:11px}
    .trending-row{display:grid;grid-template-columns:48px minmax(190px,.65fr) minmax(0,1fr) auto;gap:12px;align-items:center;padding:10px 12px;border-bottom:1px solid var(--hair);color:var(--ink);text-decoration:none;background:var(--panel)}
    .trending-row:hover{background:var(--slate-soft)}
    .trending-rank{font-family:"IBM Plex Mono",ui-monospace,monospace;color:var(--rust);font-size:13px}
    .trending-repo{font-weight:600;font-size:12.5px}
    .trending-desc{color:var(--muted);font-size:11.5px}
    .trending-meta{font-family:"IBM Plex Mono",ui-monospace,monospace;color:var(--moss);font-size:9.5px;white-space:nowrap}

    /* detail dialog */
    .overlay{position:fixed;inset:0;background:rgba(32,38,34,.48);z-index:50;display:flex;align-items:flex-start;justify-content:center;padding:42px 18px;overflow:auto}
    .overlay.hidden{display:none}
    .card{background:var(--panel);border:1px solid var(--rule);border-top:4px solid var(--rust);max-width:760px;width:100%;padding:22px 24px;box-shadow:0 18px 44px rgba(32,38,34,.2)}
    .card-close{float:right;cursor:pointer;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;color:var(--muted);border:1px solid var(--rule);padding:4px 9px;background:var(--paper)}
    .card-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;color:var(--faint);margin:3px 60px 11px 0}
    .card h2{margin:0 0 9px;font-size:20px;line-height:1.35}
    .card .abs{margin:11px 0;color:var(--ink);font-size:13.5px}
    .card .field{margin:9px 0;font-size:12.5px;line-height:1.6}
    .card .field b{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;color:var(--faint);font-weight:600;letter-spacing:.4px;margin-right:7px}
    .card .src{display:inline-block;margin-top:12px;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;color:var(--rust);text-decoration:none;border:1px solid var(--rust);padding:6px 10px}
    .card .src:hover{background:var(--rust);color:var(--paper)}

    @media(max-width:980px){
      .masthead-main{grid-template-columns:1fr}.scope-stats{text-align:left}
      .rec-item{grid-template-columns:58px minmax(0,1fr)}.rec-editorial{grid-column:2;border-left:0;border-top:2px solid var(--rust-soft);padding:10px 0 0}
      .weekly-grid{grid-template-columns:1fr}.weekly-overview{padding-right:0;border-right:0;border-bottom:1px solid var(--hair);padding-bottom:16px}
      .source-map{grid-template-columns:repeat(3,minmax(0,1fr))}.source-card:nth-child(3){border-right:0}.source-card:nth-child(-n+3){border-bottom:1px solid var(--hair)}
    }
    @media(max-width:680px){
      main{padding:14px 12px 70px}.scope-stats{grid-template-columns:repeat(2,1fr)}.masthead-foot{align-items:flex-start;flex-direction:column}
      .section-head,.rec-head{align-items:flex-start;flex-direction:column}.section-note,.rec-note,.all-summary{text-align:left}
      .rec-item{grid-template-columns:42px minmax(0,1fr);gap:12px}.rec-editorial{grid-column:1/-1}
      .weekly-hl{grid-template-columns:20px 1fr}.weekly-why{grid-column:2}
      .source-map{grid-template-columns:1fr 1fr}.source-card{border-bottom:1px solid var(--hair)}.source-card:nth-child(odd){border-right:1px solid var(--hair)}.source-card:nth-child(even){border-right:0}
      .library-tools{grid-template-columns:1fr}.trending-row{grid-template-columns:34px 1fr}.trending-desc,.trending-meta{grid-column:2}
    }
    @media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
  </style>
</head>
<body>
  <main>
    <header class="masthead">
      <div class="masthead-main">
        <div>
          <div class="brand"><h1>RADAR</h1><span class="brand-copy">端侧 AI Agent 每周研究</span></div>
          <p class="brand-deck">过去 7 天完整收录，Agent 负责把更值得优先阅读的内容排在前面。</p>
        </div>
        <div class="scope-stats" id="summary" aria-live="polite"><span><b>—</b><small>正在读取</small></span></div>
      </div>
      <div class="masthead-foot">
        <nav class="nav" aria-label="辅助内容">
          <a class="nav-link" href="notes.html">调研笔记 ↗</a>
          <a class="nav-link" href="snn.html">SNN 洞察 ↗</a>
          <a class="nav-link" href="waic.html">WAIC ↗</a>
        </nav>
        <label><span class="sr-only">切换周</span><select class="week-switch" id="week-switch" title="切换周"></select></label>
      </div>
    </header>

    <section class="recommendations" id="recommendations" aria-live="polite"></section>
    <section class="weekly" id="weekly"></section>

    <section class="all-research" id="all-research">
      <header class="section-head all-head">
        <div><p class="eyebrow">本周完整收录</p><h2>完整资料库</h2></div>
        <p class="all-summary" id="all-summary">正在读取本周收录…</p>
      </header>
      <div class="source-map" id="source-map" aria-label="本周收录构成"></div>
      <div class="library-tools">
        <label><span class="sr-only">搜索完整资料库</span><input class="search" id="search" placeholder="搜索中文介绍、原标题、机构或关键词…" autocomplete="off"></label>
        <div class="sort" aria-label="排序">排序
          <button type="button" id="sort-score" class="on" aria-pressed="true">价值分</button>
          <button type="button" id="sort-date" aria-pressed="false">时间</button>
        </div>
      </div>
      <div class="filter-shell" id="primary-filter" aria-label="常用筛选"></div>
      <div class="filter-actions">
        <button class="filter-action" type="button" id="advanced-toggle" aria-expanded="false" aria-controls="advanced-filter">更多筛选 ↓</button>
        <button class="filter-action" type="button" id="clear-filters" disabled>清除筛选</button>
      </div>
      <div class="filter-shell advanced" id="advanced-filter" hidden aria-label="更多筛选"></div>
      <div class="tabs" id="tabs" aria-label="来源分段导航"></div>
      <div id="papers" aria-live="polite"><div class="empty">正在读取本周数据…</div></div>
    </section>

    <section class="discovery" id="discovery">
      <header class="section-head">
        <div><p class="eyebrow">发现线索 · 尚未核验</p><h2>GitHub 待核验线索</h2></div>
        <p class="section-note">这里是本周发现入口，不等同于正式收录或推荐；进入资料库前仍需核对影响力、代码真实性和设备端闭环。</p>
      </header>
      <div class="discovery-note">未进入正式收录 · 需要进一步核验</div>
      <div id="discovery-list"></div>
    </section>

    <div id="overlay" class="overlay hidden" onclick="if(event.target===this)closeDetail()"></div>
  </main>

  <script>
    let ALL=[], TRENDING_CACHE=[], ACTIVE=new Set(), Q="", SORT="score", ACTIVE_SOURCE="", ACTIVE_SCOPE="", SHOW_ALL_RECOMMENDED=false, SHOW_ALL_TRENDING=false, ADVANCED_OPEN=false, LAST_FOCUS=null;
    const REC_PREVIEW=6;
    const WEEKLY_PREVIEW=3;
    const TRENDING_PREVIEW=8;
    const TIER=[
      ["官方动态","--amber","厂商与模型实验室的一手发布"],
      ["开源大项目","--green","通过白名单审计的重要项目更新"],
      ["公司项目","--blue","有机构一手证据的公司研究"],
      ["学校顶会","--purple","高校正式顶会与顶刊工作"],
      ["学校预印本","--slate","本周最新高校预印本"]
    ];
    const EDGE_AGENT_PRIORITY={"手机":0,"PC":1,"其他端侧":2,"非端侧Agent":3};
    const EDGE_AGENT_LABELS={"手机":"手机端 Agent","PC":"PC 端 Agent","其他端侧":"其他端侧 Agent"};
    const SCOPE_FILTERS=[["","全部设备"],["手机","手机端 Agent"],["PC","PC 端 Agent"],["其他端侧","其他端侧 Agent"],["非端侧Agent","其他技术"]];
    const PRIMARY_DIRECTIONS=["方向:端侧agent","方向:高效推理","方向:编译部署","方向:量化","方向:多模态","方向:推理框架","方向:安全隐私","方向:云端serving"];
    const edgeAgentPriority=p=>EDGE_AGENT_PRIORITY[p.edge_agent_scope]??3;
    const isRecommended=p=>p.recommendation==='推荐';
    const hasContent=v=>v&&v!=='未报告';
    const dim=t=>t.split(":")[0], val=t=>t.split(":")[1]||t;

    async function loadPapers(){
      let data=window.__PAPERS__||null;
      if(!data){
        const res=await fetch("/api/papers");
        if(!res.ok)throw new Error("HTTP "+res.status);
        data=await res.json();
      }
      ALL=data.papers||[];
      renderRadar();
      renderHeaderStats();
      attachSpy();
    }
    async function loadWeekly(){
      let w=window.__WEEKLY__||null;
      if(!w){
        const wr=await fetch("/api/weekly");
        if(!wr.ok)throw new Error("HTTP "+wr.status);
        w=await wr.json();
      }
      const el=document.querySelector("#weekly");
      if(!w||!w.highlights||!w.highlights.length){el.hidden=true;return;}
      el.hidden=false;
      const rows=(items,start)=>items.map((h,i)=>{
        const a=h.url
          ?`<a class="weekly-topic" href="${escapeAttr(h.url)}" target="_blank" rel="noopener">${escapeHtml(h.topic)}</a>`
          :`<a class="weekly-topic" href="/paper/${escapeAttr(h.paper_id)}">${escapeHtml(h.topic)}</a>`;
        return `<div class="weekly-hl"><span class="weekly-num">${String(start+i+1).padStart(2,'0')}</span>${a}<span class="weekly-why">${escapeHtml(h.why)}</span></div>`;
      }).join("");
      const first=w.highlights.slice(0,WEEKLY_PREVIEW);
      const rest=w.highlights.slice(WEEKLY_PREVIEW);
      el.innerHTML=`<header class="section-head"><div><p class="eyebrow">本周编辑判断</p><h2>本周判断</h2></div><p class="section-note">编辑综述负责说明变化，外部动态负责提供可核验入口；两者都不替代下方完整资料库。</p></header>`+
        `<div class="weekly-grid"><article class="weekly-overview"><div class="weekly-label">本周一句话与判断</div><p class="weekly-ov">${escapeHtml(w.overview||'')}</p></article><div class="weekly-stories"><h3>外部动态</h3>`+
        rows(first,0)+(rest.length?`<details class="weekly-more"><summary>展开其余 ${rest.length} 条热点 ↓</summary>${rows(rest,WEEKLY_PREVIEW)}</details>`:"")+
        `</div></div>`;
    }
    function range(){
      const ws=window.__WEEKS__||[],mine=window.__WEEK_LABEL__||null;
      const weekMeta=mine?ws.find(w=>w.label===mine):ws.find(w=>w.current);
      if(weekMeta&&weekMeta.range&&weekMeta.range.start&&weekMeta.range.end){
        return `${weekMeta.range.start.slice(5)} → ${weekMeta.range.end.slice(5)}`;
      }
      const d=ALL.map(p=>p.date).filter(Boolean).sort();
      return d.length?`${d[0].slice(5)} → ${d[d.length-1].slice(5)}`:'';
    }
    function renderHeaderStats(){
      const rec=ALL.filter(isRecommended).length;
      const direct=ALL.filter(p=>edgeAgentPriority(p)<3).length;
      const sources=new Set(ALL.map(p=>p.source_tier).filter(Boolean)).size;
      document.querySelector("#summary").innerHTML=
        `<span><b>${ALL.length}</b><small>本周收录</small></span>`+
        `<span><b>${rec}</b><small>优先推荐</small></span>`+
        `<span><b>${direct}</b><small>真正端侧 Agent</small></span>`+
        `<span><b>${escapeHtml(range())}</b><small>${sources} 类正式来源</small></span>`;
    }

    function allTags(){
      const s=new Set();
      ALL.forEach(p=>(p.tags||[]).forEach(t=>s.add(t)));
      return [...s];
    }
    function tagCounts(){
      const counts={};
      ALL.forEach(p=>(p.tags||[]).forEach(t=>counts[t]=(counts[t]||0)+1));
      return counts;
    }
    function filterButton(label,attrs,active,count){
      return `<button type="button" class="ftag${active?' active':''}" ${attrs} aria-pressed="${active?'true':'false'}">${escapeHtml(label)}${count===undefined?'':` · ${count}`}</button>`;
    }
    function renderSourceMap(){
      const el=document.querySelector("#source-map");
      el.innerHTML=TIER.map(([tier,color,note])=>{
        const count=ALL.filter(p=>p.source_tier===tier).length;
        const active=ACTIVE_SOURCE===tier;
        return `<button type="button" class="source-card${active?' active':''}" data-source="${escapeAttr(tier)}" aria-pressed="${active?'true':'false'}" style="--source-color:var(${color})"><b>${count}</b><span>${escapeHtml(tier)}</span><small>${escapeHtml(note)}</small></button>`;
      }).join("");
    }
    function renderFilter(){
      const counts=tagCounts(),tags=allTags();
      const scopeCounts={};
      ALL.forEach(p=>scopeCounts[p.edge_agent_scope]=(scopeCounts[p.edge_agent_scope]||0)+1);
      const device=SCOPE_FILTERS.map(([scope,label])=>filterButton(
        label,
        `data-scope="${escapeAttr(scope)}" data-dim="设备"`,
        ACTIVE_SCOPE===scope,
        scope?scopeCounts[scope]||0:ALL.length
      )).join("");
      const sources=TIER.map(([tier])=>filterButton(
        tier,
        `data-source="${escapeAttr(tier)}" data-dim="来源"`,
        ACTIVE_SOURCE===tier,
        ALL.filter(p=>p.source_tier===tier).length
      )).join("");
      const primaryDirection=PRIMARY_DIRECTIONS.filter(t=>tags.includes(t)).map(t=>filterButton(
        val(t),
        `data-tag="${escapeAttr(t)}" data-dim="方向"`,
        ACTIVE.has(t),
        counts[t]
      )).join("");
      document.querySelector("#primary-filter").innerHTML=
        `<div class="dim-group"><span class="dim-label">设备</span>${device}</div>`+
        `<div class="dim-group"><span class="dim-label">来源</span>${sources}</div>`+
        (primaryDirection?`<div class="dim-group"><span class="dim-label">方向</span>${primaryDirection}</div>`:"");

      const byDim={};
      tags.filter(t=>!PRIMARY_DIRECTIONS.includes(t)).forEach(t=>{
        const d=dim(t);(byDim[d]=byDim[d]||[]).push(t);
      });
      const advanced=["方向","应用","硬件","模型"].filter(d=>byDim[d]).map(d=>{
        const buttons=byDim[d].sort((a,b)=>(counts[b]||0)-(counts[a]||0)||a.localeCompare(b)).map(t=>filterButton(
          val(t),
          `data-tag="${escapeAttr(t)}" data-dim="${escapeAttr(d)}"`,
          ACTIVE.has(t),
          counts[t]
        )).join("");
        return `<div class="dim-group"><span class="dim-label">${escapeHtml(d)}</span>${buttons}</div>`;
      }).join("");
      const advancedEl=document.querySelector("#advanced-filter");
      advancedEl.innerHTML=advanced;
      advancedEl.hidden=!ADVANCED_OPEN;
      const toggle=document.querySelector("#advanced-toggle");
      toggle.setAttribute("aria-expanded",ADVANCED_OPEN?"true":"false");
      const advancedSelected=[...ACTIVE].filter(t=>!PRIMARY_DIRECTIONS.includes(t)).length;
      toggle.textContent=ADVANCED_OPEN?"收起更多筛选 ↑":`更多筛选${advancedSelected?` · 已选 ${advancedSelected}`:''} ↓`;
      document.querySelector("#clear-filters").disabled=!hasFilters();
    }
    function hasFilters(){return Boolean(ACTIVE.size||ACTIVE_SOURCE||ACTIVE_SCOPE||Q);}

    function visible(){
      let l=ALL.filter(p=>
        (ACTIVE_SOURCE===""||p.source_tier===ACTIVE_SOURCE)&&
        (ACTIVE_SCOPE===""||p.edge_agent_scope===ACTIVE_SCOPE)&&
        (ACTIVE.size===0||(p.tags||[]).some(t=>ACTIVE.has(t)))
      );
      if(Q){
        const q=Q.toLowerCase();
        l=l.filter(p=>((p.title_zh||'')+(p.title||'')+(p.abstract||'')+(p.tags||[]).join()+(p.vendors||'')).toLowerCase().includes(q));
      }
      l.sort((a,b)=>SORT==="score"?(b.score||0)-(a.score||0)||(b.date||'').localeCompare(a.date||''):(b.date||'').localeCompare(a.date||'')||(b.score||0)-(a.score||0));
      return l;
    }
    function sigBars(s){
      const n=Math.min(5,Math.max(1,Math.ceil((s||0)/4))),hi=(s||0)>=14;
      let out="";
      for(let i=0;i<5;i++)out+=`<i class="${i<n?'on':''} ${hi?'hi':''}"></i>`;
      return out;
    }

    function renderRecommendations(){
      const el=document.querySelector("#recommendations");
      if(!ALL.length){el.hidden=true;return;}
      el.hidden=false;
      const recommended=ALL.filter(isRecommended).sort((a,b)=>{
        const edgeDiff=edgeAgentPriority(a)-edgeAgentPriority(b);
        const tierDiff=TIER.findIndex(([t])=>t===a.source_tier)-TIER.findIndex(([t])=>t===b.source_tier);
        return edgeDiff||tierDiff||(b.score||0)-(a.score||0)||(b.date||'').localeCompare(a.date||'');
      });
      const countLabel=`${recommended.length}`;
      const previewLabel=SHOW_ALL_RECOMMENDED?`已展开 ${recommended.length} 条`:`首屏精选 ${Math.min(recommended.length,REC_PREVIEW)} 条`;
      const shown=SHOW_ALL_RECOMMENDED?recommended:recommended.slice(0,REC_PREVIEW);
      const items=shown.map((p,i)=>{
        const titleZh=(p.title_zh||'').trim()||p.title;
        const summary=(p.abstract||'').trim()||'暂无中文摘要';
        const tags=(p.tags||[]).map(t=>`<span class="rec-tag">${escapeHtml(val(t))}</span>`).join('');
        const reason=(p.recommendation_reason||'').trim()||'该条目由 Agent 选为本周优先阅读';
        const edgeScope=EDGE_AGENT_LABELS[p.edge_agent_scope]||'';
        return `<a class="rec-item" href="/paper/${escapeAttr(p.id)}" onclick="openDetail('${escapeAttr(p.id)}',this);return false;">
          <span class="rec-rank">${String(i+1).padStart(2,'0')}</span>
          <span class="rec-main"><span class="rec-meta">${edgeScope?`<span class="rec-edge-scope">${escapeHtml(edgeScope)}</span>`:''}<span class="rec-tier">${escapeHtml(p.source_tier||'')}</span><span>${escapeHtml(p.date||'')}</span><span class="rec-score">${p.score}/20</span>${p.open_source?'<span class="open">OSS</span>':''}</span><span class="rec-title">${escapeHtml(titleZh)}</span><span class="rec-summary">${escapeHtml(summary)}</span><span class="rec-tags"><b>关键词</b>${tags}</span></span>
          <span class="rec-editorial"><span class="rec-why"><b>值得优先看：</b>${escapeHtml(reason)}</span><span class="rec-original">原标题：${escapeHtml(p.title)}</span></span>
        </a>`;
      }).join('');
      el.innerHTML=`<header class="rec-head"><div><p class="eyebrow">Agent 精选 · 推荐优先</p><h2>Agent 本周推荐 <span class="rec-count">· ${previewLabel} · 共推荐 ${countLabel} 条</span></h2></div><p class="rec-note">完整资料库包含全部 ${ALL.length} 条；推荐只是编辑视图，不会把任何已推荐条目从完整收录中移除。</p></header>`+
        (items?`<div class="rec-list">${items}</div>`:'<div class="rec-empty">本周没有已完成策展的推荐，完整资料库仍保留全部合格内容。</div>')+
        (recommended.length>REC_PREVIEW?`<button type="button" class="rec-more" id="rec-toggle">${SHOW_ALL_RECOMMENDED?'收起推荐':'查看其余 '+(recommended.length-REC_PREVIEW)+' 条'}</button>`:'');
    }

    function renderRadar(){
      renderSourceMap();
      renderFilter();
      renderRecommendations();
      renderPapers();
      const matching=visible();
      const recCount=matching.filter(isRecommended).length;
      document.querySelector("#all-summary").textContent=`显示 ${matching.length} / ${ALL.length} 条 · 其中推荐 ${recCount} 条 · 完整资料库包含全部正式收录`;
    }
    function renderRow(p){
      const hi=(p.score||0)>=14,rec=isRecommended(p);
      const tags=(p.tags||[]).map(t=>`<span class="tag" data-dim="${escapeAttr(dim(t))}">${escapeHtml(val(t))}</span>`).join("");
      const displayTitle=(p.title_zh||'').trim()||p.title;
      const original=p.title_zh?`<span class="rec-original">原标题：${escapeHtml(p.title)}</span>`:"";
      return `<a class="signal-row${rec?' rec':''}" href="/paper/${escapeAttr(p.id)}" onclick="openDetail('${escapeAttr(p.id)}',this);return false;">
        <span class="sig"><span class="sig-n${hi?' hi':''}">${p.score}</span><span class="sig-bars">${sigBars(p.score)}</span></span>
        <span class="row-body"><span class="row-meta"><span class="tier">${escapeHtml(p.source_tier||'')}</span>${rec?'<span class="rec-badge">推荐</span>':''}${p.open_source?'<span class="open">OSS</span>':''}<span class="date">${escapeHtml(p.date||'')}</span></span><span class="ttl">${escapeHtml(displayTitle)}</span>${original}<span class="abs">${escapeHtml(p.abstract||'')}</span>${tags?`<span class="tags">${tags}</span>`:''}</span>
      </a>`;
    }
    function renderPapers(){
      const l=visible(),el=document.querySelector("#papers");
      if(!l.length){
        el.innerHTML=`<div class="empty">当前组合筛选没有结果。<button type="button" onclick="clearFilters()">清除筛选</button></div>`;
        renderTabs({});
        return;
      }
      const groups={};
      l.forEach(p=>(groups[p.source_tier]=groups[p.source_tier]||[]).push(p));
      const COLLAPSE=25;
      el.innerHTML=TIER.filter(([tier])=>groups[tier]).map(([tier,color])=>{
        const collapsed=groups[tier].length>COLLAPSE;
        return `<section class="band${collapsed?' collapsed':''}" id="band-${escapeAttr(tier)}"><button type="button" class="band-head" aria-expanded="${collapsed?'false':'true'}" onclick="toggleBand(this)"><span class="fold">▾</span><span class="band-bar" style="background:var(${color})"></span><span class="band-title">${escapeHtml(tier)}</span><span class="band-count">${groups[tier].length}</span>${collapsed?'<span class="band-meta">点击展开</span>':''}</button><div class="band-body">${groups[tier].map(renderRow).join("")}</div></section>`;
      }).join("");
      renderTabs(groups);
      attachSpy();
    }
    function toggleBand(button){
      const band=button.closest(".band");
      band.classList.toggle("collapsed");
      button.setAttribute("aria-expanded",band.classList.contains("collapsed")?"false":"true");
    }
    function renderTabs(groups){
      const tabs=TIER.filter(([tier])=>groups[tier]).map(([tier])=>`<button type="button" class="tab" data-target="band-${escapeAttr(tier)}">${escapeHtml(tier)}<b>${groups[tier].length}</b></button>`);
      document.querySelector("#tabs").innerHTML=tabs.join("");
    }

    function openDetail(id,trigger){
      const p=ALL.find(x=>x.id===id),overlay=document.querySelector("#overlay");
      LAST_FOCUS=trigger||document.activeElement;
      if(!p){overlay.classList.add("hidden");return;}
      const tags=(p.tags||[]).map(t=>`<span class="tag" data-dim="${escapeAttr(dim(t))}">${escapeHtml(val(t))}</span>`).join("");
      const title=(p.title_zh||'').trim()||p.title;
      overlay.innerHTML=`<article class="card" role="dialog" aria-modal="true" aria-labelledby="detail-title"><button type="button" class="card-close" aria-label="关闭详情" onclick="closeDetail()">esc · 关闭</button><div class="card-meta"><span class="tier">${escapeHtml(p.source_tier||'')}</span>${p.open_source?'<span class="open">OSS</span>':''}<span class="date">${escapeHtml(p.date||'')}</span><span>score ${p.score}</span><span>(${p.score_relevance||0}+${p.score_contribution||0})</span></div><h2 id="detail-title">${escapeHtml(title)}</h2>${p.title_zh?`<div class="rec-original">原标题：${escapeHtml(p.title)}</div>`:''}${tags?`<div class="tags">${tags}</div>`:''}<div class="abs">${escapeHtml(p.abstract||'')}</div>${hasContent(p.effects)?`<div class="field"><b>有什么结果</b>${escapeHtml(p.effects)}</div>`:''}${hasContent(p.mechanism)?`<div class="field"><b>怎么做到</b>${escapeHtml(p.mechanism)}</div>`:''}${p.score_reason?`<div class="field"><b>评分依据</b>${escapeHtml(p.score_reason)}</div>`:''}${p.edge_agent_evidence?`<div class="field"><b>设备端闭环</b>${escapeHtml(p.edge_agent_evidence)}</div>`:''}${p.authors?`<div class="field"><b>作者</b>${escapeHtml(p.authors)}</div>`:''}${p.vendors?`<div class="field"><b>机构</b>${escapeHtml(p.vendors)}</div>`:''}${p.venue?`<div class="field"><b>来源</b>${escapeHtml(p.venue)}</div>`:''}${p.paper_url?`<a class="src" href="${escapeAttr(p.paper_url)}" target="_blank" rel="noopener">查看原文 ↗ ${escapeHtml(p.paper_url.replace(/^https?:\/\//,'').split('/')[0])}</a>`:''}</article>`;
      overlay.classList.remove("hidden");
      document.body.style.overflow="hidden";
      overlay.querySelector(".card-close").focus();
    }
    function closeDetail(){
      const overlay=document.querySelector("#overlay");
      overlay.classList.add("hidden");overlay.innerHTML="";document.body.style.overflow="";
      if(LAST_FOCUS&&LAST_FOCUS.focus)LAST_FOCUS.focus();
      LAST_FOCUS=null;
    }
    document.addEventListener("keydown",event=>{if(event.key==="Escape"&&!document.querySelector("#overlay").classList.contains("hidden"))closeDetail();});

    function renderTrendingRow(item){
      return `<a class="trending-row" href="${escapeAttr(item.url)}" target="_blank" rel="noopener"><span class="trending-rank">${String(item.rank||'').padStart(2,'0')}</span><span class="trending-repo">${escapeHtml(item.repo)}</span><span class="trending-desc">${escapeHtml(item.desc||'')}</span><span class="trending-meta">+${escapeHtml(item.week||'0')}/wk · ${escapeHtml(item.total||'')}</span></a>`;
    }
    function renderTrending(list){
      const el=document.querySelector("#discovery-list");
      if(!list||!list.length){el.innerHTML='<div class="empty">本周没有可展示的 GitHub 发现线索。</div>';return;}
      const shown=SHOW_ALL_TRENDING?list:list.slice(0,TRENDING_PREVIEW);
      el.innerHTML=shown.map(renderTrendingRow).join("")+
        (list.length>TRENDING_PREVIEW?`<button type="button" class="trending-more" id="trending-toggle">${SHOW_ALL_TRENDING?'收起线索':'展开全部 '+list.length+' 条线索'}</button>`:"");
    }
    async function loadTrending(){
      let data=window.__TRENDING__||null;
      if(!data){try{const response=await fetch("/api/trending");data=await response.json();}catch(error){document.querySelector("#discovery-list").innerHTML='<div class="empty">GitHub 线索暂时读取失败。</div>';return;}}
      TRENDING_CACHE=data.items||data||[];
      renderTrending(TRENDING_CACHE);
    }

    function handleFilterClick(event){
      const button=event.target.closest(".ftag");
      if(!button)return;
      if(button.dataset.scope!==undefined){ACTIVE_SCOPE=button.dataset.scope===ACTIVE_SCOPE?"":button.dataset.scope;}
      if(button.dataset.source!==undefined){ACTIVE_SOURCE=button.dataset.source===ACTIVE_SOURCE?"":button.dataset.source;}
      if(button.dataset.tag){const tag=button.dataset.tag;ACTIVE.has(tag)?ACTIVE.delete(tag):ACTIVE.add(tag);}
      renderRadar();
    }
    function clearFilters(){
      ACTIVE.clear();ACTIVE_SOURCE="";ACTIVE_SCOPE="";Q="";
      document.querySelector("#search").value="";
      renderRadar();
    }
    function showLoadError(error){
      document.querySelector("#summary").innerHTML='<span><b>—</b><small>读取失败</small></span>';
      document.querySelector("#papers").innerHTML=`<div class="empty">本周资料读取失败：${escapeHtml(error&&error.message||'未知错误')}<button type="button" onclick="loadPapers().catch(showLoadError)">重新读取</button></div>`;
    }
    document.querySelector("#recommendations").addEventListener("click",event=>{
      const button=event.target.closest("#rec-toggle");if(!button)return;
      SHOW_ALL_RECOMMENDED=!SHOW_ALL_RECOMMENDED;renderRecommendations();
    });
    document.querySelector("#discovery-list").addEventListener("click",event=>{
      const button=event.target.closest("#trending-toggle");if(!button)return;
      SHOW_ALL_TRENDING=!SHOW_ALL_TRENDING;renderTrending(TRENDING_CACHE);
    });
    document.querySelector("#primary-filter").addEventListener("click",handleFilterClick);
    document.querySelector("#advanced-filter").addEventListener("click",handleFilterClick);
    document.querySelector("#source-map").addEventListener("click",event=>{
      const button=event.target.closest(".source-card");if(!button)return;
      ACTIVE_SOURCE=button.dataset.source===ACTIVE_SOURCE?"":button.dataset.source;
      renderRadar();
      document.querySelector("#primary-filter").scrollIntoView({behavior:"smooth",block:"start"});
    });
    document.querySelector("#advanced-toggle").addEventListener("click",()=>{
      ADVANCED_OPEN=!ADVANCED_OPEN;renderFilter();
    });
    document.querySelector("#clear-filters").addEventListener("click",clearFilters);
    document.querySelector("#search").addEventListener("input",event=>{Q=event.target.value.trim();renderRadar();});
    document.querySelector("#sort-score").addEventListener("click",()=>{
      SORT="score";document.querySelector("#sort-score").classList.add("on");document.querySelector("#sort-date").classList.remove("on");
      document.querySelector("#sort-score").setAttribute("aria-pressed","true");document.querySelector("#sort-date").setAttribute("aria-pressed","false");renderRadar();
    });
    document.querySelector("#sort-date").addEventListener("click",()=>{
      SORT="date";document.querySelector("#sort-date").classList.add("on");document.querySelector("#sort-score").classList.remove("on");
      document.querySelector("#sort-date").setAttribute("aria-pressed","true");document.querySelector("#sort-score").setAttribute("aria-pressed","false");renderRadar();
    });
    document.querySelector("#tabs").addEventListener("click",event=>{
      const button=event.target.closest(".tab");if(!button)return;
      const target=document.getElementById(button.dataset.target);if(!target)return;
      target.classList.remove("collapsed");
      const head=target.querySelector(".band-head");if(head)head.setAttribute("aria-expanded","true");
      target.scrollIntoView({behavior:"smooth",block:"start"});
    });

    const spy=new IntersectionObserver(entries=>{
      entries.forEach(entry=>{if(entry.isIntersecting){document.querySelectorAll(".tab").forEach(tab=>tab.classList.toggle("active",tab.dataset.target===entry.target.id));}});
    },{rootMargin:"-42% 0px -52% 0px"});
    function attachSpy(){
      spy.disconnect();
      document.querySelectorAll("section.band[id]").forEach(section=>spy.observe(section));
    }
    function escapeHtml(value){return String(value||"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));}
    function escapeAttr(value){return escapeHtml(value).replace(/`/g,"&#96;");}
    function renderWeekSwitch(){
      const weeks=window.__WEEKS__||[],select=document.querySelector("#week-switch");
      if(!weeks.length){select.style.display="none";return;}
      const mine=window.__WEEK_LABEL__||null;
      select.innerHTML=weeks.map(week=>{
        const isMine=(week.current&&mine===null)||(week.label===mine);
        return `<option value="${escapeAttr(week.href)}"${isMine?' selected':''}>${week.current?'本周 · ':''}${escapeHtml(week.title)}</option>`;
      }).join("");
    }
    document.querySelector("#week-switch").addEventListener("change",event=>{if(event.target.value&&event.target.value!==location.pathname)location.href=event.target.value;});
    window.addEventListener("pageshow",renderWeekSwitch);
    renderWeekSwitch();
    loadPapers().catch(showLoadError);
    loadWeekly().catch(()=>{document.querySelector("#weekly").hidden=true;});
    loadTrending().catch(()=>{});
  </script>
</body>
</html>
"""
