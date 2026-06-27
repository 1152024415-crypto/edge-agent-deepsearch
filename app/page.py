"""Server-rendered shell for the paper radar page."""

INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>端侧 AI Agent 论文雷达</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font-family: -apple-system, "Segoe UI", "Microsoft YaHei", Arial, sans-serif; background: #f7f3ea; color: #202621; }
    main { max-width: 1100px; margin: 0 auto; padding: 20px; }
    h1 { margin: 0 0 4px; font-size: 26px; color: #202621; }
    .muted { color: #627066; margin: 0 0 16px; font-size: 14px; }
    .tabs { display: flex; flex-wrap: wrap; gap: 4px; border-bottom: 2px solid #cfc6b4; margin-bottom: 16px; }
    .tab { padding: 8px 18px; border: none; background: transparent; color: #627066; font-size: 15px; font-weight: 600; cursor: pointer; border-bottom: 3px solid transparent; margin-bottom: -2px; display: inline-flex; align-items: center; gap: 6px; }
    .tab:hover { color: #8d3d30; }
    .tab.active { color: #8d3d30; border-bottom-color: #8d3d30; }
    .tab .count { display: inline-block; min-width: 18px; padding: 0 6px; background: #eee7da; color: #596258; border-radius: 9px; font-size: 11px; font-weight: 700; line-height: 16px; text-align: center; }
    .tab.active .count { background: #8d3d30; color: #fffaf0; }
    .cat-panel { display: none; }
    .cat-panel.active { display: block; }
    .card { background: #fffdf7; border: 1px solid #cfc6b4; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px; }
    .card-head { display: flex; align-items: baseline; flex-wrap: wrap; gap: 8px; }
    .score { font-weight: 700; color: #8d3d30; font-size: 20px; min-width: 30px; }
    .vendor-badge { display: inline-block; padding: 2px 7px; border: 1px solid #8d3d30; color: #8d3d30; font-size: 11px; font-weight: 700; border-radius: 3px; }
    .open-badge { display: inline-block; padding: 2px 7px; border: 1px solid #2e7d32; color: #2e7d32; font-size: 11px; font-weight: 700; border-radius: 3px; }
    .vendor-tag { display: inline-block; padding: 3px 10px 3px 8px; background: #fffdf7; border-left: 3px solid #8d3d30; border-radius: 0 4px 4px 0; font-size: 12px; font-weight: 600; color: #8d3d30; }
    .date { color: #627066; font-size: 13px; }
    .title { font-weight: 700; font-size: 15px; color: #202621; text-decoration: none; }
    .title:hover { color: #8d3d30; }
    .keywords { display: flex; flex-wrap: wrap; gap: 5px; margin: 8px 0 4px; }
    .kw { display: inline-block; padding: 2px 9px; background: #eee7da; border-radius: 11px; font-size: 12px; color: #596258; line-height: 1.6; }
    .field { display: flex; margin-top: 8px; gap: 10px; }
    .label { flex-shrink: 0; width: 84px; color: #627066; font-size: 13px; font-weight: 600; }
    .text { color: #3f463f; font-size: 14px; line-height: 1.55; }
    .score-reason { margin-top: 8px; color: #4c554e; font-size: 12px; line-height: 1.4; }
    .score-dims { margin-top: 3px; color: #7a837a; font-size: 11px; }
    .card-foot { display: flex; gap: 8px; margin-top: 12px; align-items: center; flex-wrap: wrap; }
    input { padding: 5px 8px; border: 1px solid #cfc6b4; background: #fffaf0; border-radius: 4px; font-size: 13px; color: #202621; }
    input[name="insight_person"] { width: 130px; }
    input[name="wiki_url"] { width: 200px; }
    button { padding: 5px 14px; border: 1px solid #8d3d30; color: #8d3d30; background: #fffaf0; cursor: pointer; border-radius: 4px; font-size: 13px; }
    button:hover { background: #8d3d30; color: #fffaf0; }
    .empty { color: #627066; font-style: italic; padding: 20px; text-align: center; }
    @media (max-width: 640px) {
      .field { flex-direction: column; gap: 2px; }
      .label { width: auto; }
      input[name="insight_person"], input[name="wiki_url"] { width: 100%; }
    }
  </style>
</head>
<body>
  <main>
    <h1>端侧 AI Agent 论文雷达</h1>
    <p class="muted" id="summary">正在读取服务器最新调研结果...</p>
    <div class="tabs" id="tabs" role="tablist">
      <button class="tab" data-tab="academic" role="tab">学术论文<span class="count" id="count-academic">0</span></button>
      <button class="tab" data-tab="official" role="tab">官方动态<span class="count" id="count-official">0</span></button>
    </div>
    <div id="papers"></div>
  </main>
  <script>
    async function loadPapers() {
      const res = await fetch("/api/papers");
      const data = await res.json();
      const all = data.papers || [];
      // 按 source_type 分两组；tab 内保持 API 返回顺序（storage 已按 is_major_vendor_official DESC, score DESC 排）
      const academic = all.filter((p) => p.source_type === "学术论文");
      const official = all.filter((p) => p.source_type === "官方技术博客" || p.source_type === "官方产品发布");
      const groups = [
        { id: "academic", papers: academic },
        { id: "official", papers: official }
      ];
      const defaultIdx = groups.findIndex((g) => g.papers.length > 0);
      const activeIdx = defaultIdx === -1 ? 0 : defaultIdx;

      document.querySelector("#count-academic").textContent = String(academic.length);
      document.querySelector("#count-official").textContent = String(official.length);
      document.querySelectorAll(".tab").forEach((t, i) => t.classList.toggle("active", i === activeIdx));

      document.querySelector("#papers").innerHTML = groups.map((g, i) =>
        `<div class="cat-panel${i === activeIdx ? " active" : ""}" data-panel="${g.id}" role="tabpanel">${
          g.papers.map(renderCard).join("") || '<p class="empty">本周无此方向内容</p>'
        }</div>`
      ).join("");

      document.querySelector("#summary").textContent = `${all.length} 条内容 · 官方大厂优先 · 来自服务器最新调研结果`;
    }

    document.querySelector("#tabs").addEventListener("click", (event) => {
      const btn = event.target.closest(".tab");
      if (!btn) return;
      const id = btn.dataset.tab;
      document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === id));
      document.querySelectorAll(".cat-panel").forEach((p) => p.classList.toggle("active", p.dataset.panel === id));
    });

    function renderCard(p) {
      const kws = (p.keywords || []).map((k) => `<span class="kw">${escapeHtml(k)}</span>`).join("");
      const vendorsRaw = (p.vendors || '').trim();
      const official = vendorsRaw ? `<span class="vendor-tag">${escapeHtml(vendorsRaw)}</span>` : (p.is_major_vendor_official ? `<span class="vendor-badge">官方大厂</span>` : '');
      const openBadge = (p.score_open || 0) > 0 ? `<span class="open-badge">开源</span>` : '';
      return `
      <div class="card" data-id="${escapeAttr(p.id)}">
        <div class="card-head">
          <span class="score">${p.score}</span>
          ${official}
          ${openBadge}
          <span class="date">${p.date}</span>
          <a class="title" href="/paper/${escapeAttr(p.id)}">${escapeHtml(p.title)}</a>
        </div>
        <div class="keywords">${kws}</div>
        <div class="field"><span class="label">论文摘要</span><span class="text">${escapeHtml(p.abstract)}</span></div>
        <div class="field"><span class="label">论文效果</span><span class="text">${escapeHtml(p.effects)}</span></div>
        <div class="field"><span class="label">工作原理</span><span class="text">${escapeHtml(p.mechanism)}</span></div>
        <div class="score-reason">评分依据：${escapeHtml(p.score_reason || "")}</div>
        <div class="score-dims">契合${p.score_relevance ?? ''}·厂商${p.score_vendor ?? ''}·贡献${p.score_contribution ?? ''}·质量${p.score_quality ?? ''}·时效${p.score_recency ?? ''}·开源${p.score_open ?? ''}</div>
        <div class="card-foot">
          <input name="insight_person" value="${escapeAttr(p.insight_person || "")}" placeholder="洞察人">
          <input name="wiki_url" value="${escapeAttr(p.wiki_url || "")}" placeholder="wiki 链接">
          <button type="button" data-action="save">保存</button>
        </div>
      </div>`;
    }

    function escapeHtml(value) {
      return String(value || "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
    }
    function escapeAttr(value) {
      return escapeHtml(value).replace(/`/g, "&#96;");
    }

    document.addEventListener("click", async (event) => {
      const button = event.target.closest('[data-action="save"]');
      if (!button) return;
      const card = button.closest(".card");
      await fetch("/api/insights", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          paper_id: card.dataset.id,
          insight_person: card.querySelector('[name="insight_person"]').value,
          wiki_url: card.querySelector('[name="wiki_url"]').value
        })
      });
      button.textContent = "已保存";
    });

    loadPapers().catch((error) => {
      document.querySelector("#summary").textContent = `读取失败：${error}`;
    });
  </script>
</body>
</html>
"""
