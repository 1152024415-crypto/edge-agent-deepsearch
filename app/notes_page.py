"""Server-rendered shell for the research-notes page (signal-monitor terminal aesthetic).

Renders a manifest of note collections (window.__NOTES__) into a sidebar tree;
clicking a note fetches its markdown (notes/<slug>/<file>.md) and renders it
client-side with marked.js, rewriting relative image paths to notes/<slug>/.
"""

NOTES_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RADAR · 调研笔记</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
  <style>
    *{box-sizing:border-box}
    :root{--bg:#eef1f3;--panel:#ffffff;--ink:#0b1a24;--muted:#5a6b78;--faint:#8a99a6;--rule:#d4dae0;--hair:#e3e8ec;--amber:#c2410c;--green:#15803d}
    body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans","PingFang SC","Noto Sans SC",system-ui,sans-serif;font-size:14.5px;line-height:1.65}
    main{max-width:1180px;margin:0 auto;padding:18px 22px 80px}
    a{color:var(--amber);text-decoration:none}
    a:hover{text-decoration:underline}
    .scope{background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:12px 16px;margin-bottom:14px;display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap}
    h1{margin:0;font-family:"IBM Plex Mono",monospace;font-size:20px;font-weight:600;letter-spacing:1.5px}
    h1 .sub{font-family:"IBM Plex Sans",sans-serif;font-weight:500;font-size:13px;color:var(--muted);letter-spacing:0;margin-left:8px}
    .back{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--faint)}
    .sweep{height:2px;margin:10px -16px -12px;background:linear-gradient(90deg,transparent,var(--hair) 20%,var(--hair) 80%,transparent);position:relative;overflow:hidden}
    .sweep::after{content:"";position:absolute;inset:0;width:30%;background:linear-gradient(90deg,transparent,var(--amber),transparent);animation:sweep 3.2s linear infinite}
    @keyframes sweep{0%{transform:translateX(-100%)}100%{transform:translateX(400%)}}
    @media(prefers-reduced-motion:reduce){.sweep::after{animation:none;opacity:.5}}
    .layout{display:grid;grid-template-columns:248px 1fr 210px;gap:16px;align-items:start;transition:grid-template-columns .2s}
    .layout.collapsed{grid-template-columns:1fr 210px}
    .layout.collapsed .side{display:none}
    .side{background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:12px 10px;position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto;overflow-x:hidden}
    .side-toggle,.copy-md{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--faint);background:none;border:1px solid var(--hair);border-radius:3px;padding:2px 8px;cursor:pointer}
    .side-toggle:hover,.copy-md:hover{color:var(--amber);border-color:var(--amber)}
    .side-title{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--faint);text-transform:uppercase;letter-spacing:.5px;padding:4px 6px 8px;border-bottom:1px solid var(--hair);margin-bottom:6px;display:flex;align-items:center;justify-content:space-between}
    .coll{margin-bottom:10px}
    .coll-name{font-family:"IBM Plex Sans",sans-serif;font-size:12.5px;font-weight:600;color:var(--ink);padding:4px 6px;display:flex;align-items:center;gap:6px}
    .coll-name::before{content:"";width:3px;height:11px;background:var(--amber);border-radius:1px;display:inline-block}
    .coll-desc{font-size:11px;color:var(--faint);padding:0 6px 4px 15px;line-height:1.4}
    .note-link{display:block;padding:4px 8px 4px 15px;font-size:12.5px;color:var(--muted);border-radius:3px;cursor:pointer;line-height:1.4}
    .note-link:hover{background:var(--hair);color:var(--ink)}
    .note-link.active{background:#fbeae3;color:var(--amber);font-weight:600}
    .art{background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:22px 28px;min-height:60vh;min-width:0}
    .art:empty::before{content:"选一篇笔记 →";color:var(--faint);font-family:"IBM Plex Mono",monospace}
    .art h1{font-family:"IBM Plex Sans",sans-serif;font-size:22px;letter-spacing:0;margin:0 0 6px;border-bottom:1px solid var(--rule);padding-bottom:8px;scroll-margin-top:20px}
    .art h2{font-size:17px;margin:26px 0 8px;padding-bottom:4px;border-bottom:1px solid var(--hair);scroll-margin-top:20px}
    .art h3{font-size:14.5px;margin:18px 0 6px;color:var(--ink);scroll-margin-top:20px}
    /* right TOC */
    .toc{background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:12px 10px;position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto}
    .toc-title{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--faint);text-transform:uppercase;letter-spacing:.5px;padding:4px 6px 8px;border-bottom:1px solid var(--hair);margin-bottom:6px}
    .toc a{display:block;padding:3px 8px;font-size:12px;color:var(--muted);border-radius:3px;line-height:1.35;cursor:pointer;text-decoration:none}
    .toc a.h3{padding-left:18px;font-size:11.5px}
    .toc a:hover{background:var(--hair);color:var(--ink)}
    .toc a.active{background:#fbeae3;color:var(--amber);font-weight:600}
    .toc:empty::before{content:"目录";color:var(--faint);font-family:"IBM Plex Mono",monospace;font-size:10px}
    .art p{margin:8px 0}
    .art ul,.art ol{margin:8px 0;padding-left:22px}
    .art li{margin:3px 0}
    .art blockquote{margin:10px 0;padding:6px 14px;border-left:3px solid var(--amber);background:#fdf3ee;color:var(--muted);border-radius:0 4px 4px 0}
    .art blockquote p{margin:4px 0}
    .art code{font-family:"IBM Plex Mono",monospace;font-size:12.5px;background:var(--hair);padding:1px 5px;border-radius:3px}
    .art pre{background:#0b1a24;color:#dbe4ea;padding:12px 14px;border-radius:5px;overflow:auto;margin:10px 0}
    .art pre code{background:none;padding:0;color:inherit;font-size:12.5px}
    .art img{max-width:100%;height:auto;border:1px solid var(--hair);border-radius:4px;margin:8px 0;display:block}
    .art hr{border:none;border-top:1px solid var(--rule);margin:18px 0}
    .art table{border-collapse:collapse;margin:10px 0;width:100%;font-size:13px}
    .art th,.art td{border:1px solid var(--rule);padding:5px 9px;text-align:left}
    .art th{background:var(--hair)}
    .nb-foot{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--faint);padding:6px 6px 0}
    @media(max-width:760px){.layout{grid-template-columns:1fr!important}.side,.toc{position:static;max-height:none;display:none}.side-toggle{display:none}}
  </style>
</head>
<body>
  <main>
    <header class="scope">
      <h1>RADAR<span class="sub">调研笔记 · research notes</span></h1>
      <button class="side-toggle" id="side-toggle" title="收起/展开侧栏">◀ 收起侧栏</button>
      <button class="copy-md" id="copy-md" title="复制当前笔记的原始 markdown 源码">📋 复制原文</button>
      <a class="back" href="index.html">← 返回雷达</a>
      <div class="sweep"></div>
    </header>
    <div class="layout" id="layout">
      <aside class="side" id="side"></aside>
      <article class="art" id="art"></article>
      <aside class="toc" id="toc"></aside>
    </div>
  </main>
  <script>
    const NOTES = window.__NOTES__ || [];
    let CURRENT = null;
    var LAST_RAW = '';

    function renderSide(){
      const el = document.querySelector('#side');
      if(!NOTES.length){el.innerHTML='<div class="side-title">无笔记</div>';return;}
      el.innerHTML = '<div class="side-title">collections</div>' + NOTES.map(c =>
        '<div class="coll">' +
           '<div class="coll-name">' + esc(c.name) + '</div>' +
           (c.desc ? '<div class="coll-desc">' + esc(c.desc) + '</div>' : '') +
           (c.notes||[]).map(n => '<div class="note-link" data-slug="' + esc(c.slug) + '" data-file="' + escAttr(n.file) + '" data-title="' + esc(n.title) + '">' + esc(n.title) + '</div>').join('') +
         '</div>').join('') +
        '<div class="nb-foot">markdown · client-rendered</div>';
      el.addEventListener('click', function(e){
        var b = e.target.closest('.note-link'); if(!b) return;
        location.hash = b.dataset.slug + '/' + b.dataset.file;
      });
    }

    function selectNote(slug, file){
      var link = document.querySelector('.note-link[data-slug="' + slug + '"][data-file="' + file + '"]');
      document.querySelectorAll('.note-link.active').forEach(function(n){n.classList.remove('active');});
      if(link) link.classList.add('active');
      var art = document.querySelector('#art');
      art.innerHTML = '<div style="color:var(--faint);font-family:IBM Plex Mono,monospace">loading…</div>';
      var url = 'notes/' + encodeURIComponent(slug) + '/' + encodeURIComponent(file);
      // HTML notes: load in iframe (self-contained page with own styles/JS)
      if(file.endsWith('.html')){
        LAST_RAW = '';
        art.innerHTML = '<iframe src="' + esc(url) + '" style="width:100%;min-height:80vh;border:none;background:#fff;border-radius:4px;display:block"></iframe>';
        var iframe = art.querySelector('iframe');
        iframe.addEventListener('load', function(){
          try {
            var h = iframe.contentWindow.document.body.scrollHeight;
            if(h > 100) iframe.style.height = (h + 50) + 'px';
          } catch(e){}  // cross-origin — keep min-height
        });
        document.getElementById('toc').innerHTML = '<div class="toc-title">HTML 页面</div>';
        window.scrollTo(0,0);
        CURRENT = {slug:slug, file:file};
        return;
      }
      // MD notes: fetch + marked.js + KaTeX + mermaid + TOC
      fetch(url).then(function(res){
        if(!res.ok){art.innerHTML = '<p>加载失败 (' + res.status + ')：' + esc(url) + '</p>';return null;}
        return res.text();
      }).then(function(md){
        if(md == null) return;
        LAST_RAW = md;  // store raw markdown for copy button
        // Protect $...$$ / $$...$$ from marked's inline parser (it mangles
        // math with _ * | inside, splitting $$ pairs so KaTeX can't match).
        // Replace with plain placeholders, parse, restore, THEN KaTeX render.
        var pm = protectMath(md);
        var html = marked.parse(pm.md);
        html = restoreMath(html, pm.math);
        art.innerHTML = html;
        var imgs = art.querySelectorAll('img');
        for(var i=0;i<imgs.length;i++){
          var s = imgs[i].getAttribute('src');
          if(s && !/^(https?:|\/|data:)/.test(s)) imgs[i].src = 'notes/' + slug + '/' + s.split('/').pop();
        }
        renderMermaid(art);
        renderMath(art);
        renderToc(art);
        window.scrollTo(0,0);
        CURRENT = {slug:slug, file:file};
      }).catch(function(e){art.innerHTML = '<p>加载出错：' + esc(String(e)) + '</p>';});
    }

    // Build right-side TOC from rendered H2/H3; click-to-scroll + current-section highlight.
    function renderToc(art){
      var toc = document.getElementById('toc');
      var heads = art.querySelectorAll('h2, h3');
      if(!heads.length){ toc.innerHTML = ''; return; }
      var html = '<div class="toc-title">目录</div>';
      for(var i=0;i<heads.length;i++){
        var h = heads[i];
        if(!h.id) h.id = 'sec-' + i;
        var cls = h.tagName === 'H3' ? 'h3' : '';
        var txt = h.innerText.replace(/^\d+\.?\s*/, '').slice(0,40);
        html += '<a class="' + cls + '" data-target="' + h.id + '">' + esc(txt) + '</a>';
      }
      toc.innerHTML = html;
      // click → scroll
      toc.querySelectorAll('a').forEach(function(a){
        a.addEventListener('click', function(){
          var t = document.getElementById(a.getAttribute('data-target'));
          if(t) t.scrollIntoView({behavior:'smooth', block:'start'});
        });
      });
      // current-section highlight
      var links = toc.querySelectorAll('a');
      if('IntersectionObserver' in window){
        var obs = new IntersectionObserver(function(entries){
          entries.forEach(function(en){
            if(en.isIntersecting){
              var id = en.target.id;
              links.forEach(function(l){ l.classList.toggle('active', l.getAttribute('data-target')===id); });
            }
          });
        }, {rootMargin:'-20% 0px -70% 0px'});
        heads.forEach(function(h){ obs.observe(h); });
      }
    }

    // Replace $$...$$ (display) and $...$ (inline) with placeholders so
    // marked.parse won't touch the math. Store originals; restore after parse.
    function protectMath(md){
      var math = [];
      // display first (multi-line, non-greedy)
      md = md.replace(/\$\$([\s\S]+?)\$\$/g, function(m){
        var i = math.length; math.push(m); return '\n\nMATHB' + i + '\n\n';
      });
      // inline (no bare $ or newline inside; \\X escapes like \$ count as content
      // so $\$2.70$ matches as one block, not splitting \$ into a false delimiter)
      md = md.replace(/\$((?:\\.|[^\\\$\n])+?)\$/g, function(m){
        var i = math.length; math.push(m); return 'MATHI' + i;
      });
      return {md: md, math: math};
    }
    function restoreMath(html, math){
      // Escape < > & in the restored math so the browser doesn't parse e.g.
      // y_{<t} as an HTML tag (which truncates the formula at y_{). The DOM
      // text node (what KaTeX auto-render reads) is the unescaped math.
      function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
      return html.replace(/MATHB(\d+)/g, function(_, i){ return esc(math[+i]); })
                 .replace(/MATHI(\d+)/g, function(_, i){ return esc(math[+i]); });
    }

    // Render ```mermaid fenced blocks (marked emits <pre><code class="language-mermaid">)
    // as actual diagrams. Convert each to <div class="mermaid"> + run mermaid.
    function renderMermaid(art){
      var blocks = art.querySelectorAll('pre code.language-mermaid');
      if(!blocks.length) return;
      if(!window.mermaid){  // lib not loaded yet — retry shortly
        setTimeout(function(){renderMermaid(art);}, 500);
        return;
      }
      if(!mermaid._init){ mermaid.initialize({startOnLoad:false, securityLevel:'loose'}); mermaid._init = true; }
      var nodes = [];
      blocks.forEach(function(code){
        var pre = code.parentNode;
        var div = document.createElement('div');
        div.className = 'mermaid';
        div.textContent = code.textContent;  // unescaped diagram source (mermaid needs raw >, etc.)
        pre.parentNode.replaceChild(div, pre);
        nodes.push(div);
      });
      try { mermaid.run({nodes: nodes}); } catch(e){
        nodes.forEach(function(d){ d.setAttribute('style','white-space:pre-wrap;font-family:IBM Plex Mono,monospace;font-size:12px;color:var(--muted)'); });
      }
    }

    // Render LaTeX math ($$...$$ display, $...$ inline) via KaTeX auto-render.
    // marked.js emits $ as literal text (it's not math-aware), so auto-render
    // scans the rendered DOM text and converts $...$ / $$...$$ to KaTeX.
    function renderMath(art){
      if(!window.renderMathInElement){  // katex auto-render not loaded yet — retry
        setTimeout(function(){renderMath(art);}, 500);
        return;
      }
      try {
        renderMathInElement(art, {
          delimiters: [
            {left: "$$", right: "$$", display: true},
            {left: "$", right: "$", display: false}
          ],
          throwOnError: false
        });
      } catch(e){}
    }

    function route(){
      var h = location.hash.slice(1);
      if(!h){
        if(NOTES[0] && NOTES[0].notes && NOTES[0].notes[0]) selectNote(NOTES[0].slug, NOTES[0].notes[0].file);
        return;
      }
      var idx = h.indexOf('/');
      if(idx < 0) return;
      // location.hash is URL-encoded by the browser (e.g. Chinese filenames become
      // %E8%BD...). Decode here so selectNote receives the raw name and
      // encodeURIComponent in selectNote encodes exactly once — otherwise the fetch
      // URL is double-encoded (%25E8...) and the note 404s on click.
      try {
        selectNote(decodeURIComponent(h.slice(0, idx)), decodeURIComponent(h.slice(idx + 1)));
      } catch(e) {
        selectNote(h.slice(0, idx), h.slice(idx + 1));  // fall back if not encoded
      }
    }

    function esc(v){v = String(v==null?'':v); return v.replace(/[&<>"']/g, function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
    function escAttr(v){return esc(v).replace(/`/g, '&#96;');}

    // Left sidebar collapse toggle
    (function(){
      var btn = document.getElementById('side-toggle');
      var layout = document.getElementById('layout');
      if(!btn || !layout) return;
      btn.addEventListener('click', function(){
        var c = layout.classList.toggle('collapsed');
        btn.textContent = c ? '▶ 展开侧栏' : '◀ 收起侧栏';
      });
    })();

    // Copy raw markdown source to clipboard
    (function(){
      var btn = document.getElementById('copy-md');
      if(!btn) return;
      btn.addEventListener('click', function(){
        if(!LAST_RAW){ btn.textContent = '⚠ 先选一篇笔记'; setTimeout(function(){btn.textContent='📋 复制原文';},1500); return; }
        navigator.clipboard.writeText(LAST_RAW).then(function(){
          btn.textContent = '✅ 已复制原文';
          setTimeout(function(){ btn.textContent = '📋 复制原文'; }, 2000);
        }).catch(function(){
          // fallback: select + execCommand
          var ta = document.createElement('textarea');
          ta.value = LAST_RAW; document.body.appendChild(ta); ta.select();
          try { document.execCommand('copy'); btn.textContent = '✅ 已复制原文'; setTimeout(function(){btn.textContent='📋 复制原文';},2000); } catch(e){}
          document.body.removeChild(ta);
        });
      });
    })();

    renderSide();
    route();
    window.addEventListener('hashchange', route);
  </script>
</body>
</html>
"""
