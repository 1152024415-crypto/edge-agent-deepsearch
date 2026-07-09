# 周归档 + 切换器 设计

- 日期：2026-07-09
- 状态：待评审
- 关联文件：`agent/build.py`、`app/build.py`、`app/server.py`、`app/page.py`、`data/weekly_summary.json`、`site/index.html`

## 1. 背景与目标

端侧 AI Agent 信号周报站点（`app/page.py` 列表页 + `app/server.py` 运行时 + `app/build.py` 静态化到 `site/` 供 GitHub Pages）每周构建一次。当前 `app/build.py` 每次构建**覆盖 `site/index.html`**，上一周的列表页与「本周热点」随之丢失（paper 详情页因 `site/paper/` 累积归档而不丢）。

目标：

1. 保留所有过往周的页面，无限累积。
2. 用户可在「本周」与任意「历史周」之间切换，切换器在页面顶部。
3. 静态站（GitHub Pages）与本地运行时服务器都支持切换。

非目标：无刷新 SPA 式切换（导航式即可）；不重做 paper 详情页归档（已存在）；不做滚动清理（无限保留）。

## 2. 关键事实（探查结论）

- `data/weekly_summary.json` 在 repo 内**仅被 `app/server.py:200` 读取，无任何 Python 写入**——每周 summary 由用户手工覆盖，周切换是手动时点。
- `app/build.py` 从运行时服务器 fetch `/api/papers`、`/api/weekly`、`/api/trending`，把三者内联成 `window.__PAPERS__/__WEEKLY__/__TRENDING__` 写入 `site/index.html`，并把 `/paper/<id>` 链接重写为相对路径。`site/paper/` 详情页累积不删。
- `research_runs/*.json` 是 run 级（一周可多个 run），通过 `agent/publish_results.py` POST 到 `/api/research-runs`，由 `app/papers.sqlite` 累积存储。论文按时间窗口归属于某周。
- 现有 `site/index.html` 仍冻结着上一周（overview 文本「06-26~07-03」），三套 payload 已内联——可一次性抽取回填。

## 3. 方案：归档快照 + 顶部周选择器（导航式）

把「一周页面」视为一个会被冻结的快照。每次 build 把「服务器当前周」写入按周归档的数据文件；换周时上一周的快照自然成为归档。切换器是顶部下拉，选即导航。

### 3.1 数据模型

- `data/weeks/<label>.json`：一周完整冻结快照。
  ```json
  {
    "label": "2026-06-26",
    "title": "06-26~07-03",
    "range": {"start": "2026-06-26", "end": "2026-07-03"},
    "papers": [ /* /api/papers 的 papers 数组 */ ],
    "weekly": {"overview": "...", "highlights": [...]},
    "trending": {"items": [...]}
  }
  ```
- `data/weeks/manifest.json`：切换器用的索引，最新在前。
  ```json
  [
    {"label": "2026-07-02", "title": "07-02~07-09", "range": {"start":"...","end":"..."}, "current": true},
    {"label": "2026-06-26", "title": "06-26~07-03", "range": {"start":"...","end":"..."}, "current": false}
  ]
  ```
- **label** = 周窗口起始日 `YYYY-MM-DD`。从 `weekly_summary.json` 的 overview 文本解析 `(\d{2})-(\d{2})~(\d{2})-(\d{2})` 取起始日，年份取当前年；解析失败回退到 build 日的 ISO 日期。`title` 沿用 overview 里解析出的 `MM-DD~MM-DD` 原文，`range` 用解析出的起止日（年份补当前年）。
- **边界口径**：以 overview 文本里实际写的 range 为准（如「06-26~07-03」就按这个显示和解析起始日 `2026-06-26`；本周若写「07-02~07-09」则 label=`2026-07-02`）。不强行统一窗口边界。

### 3.2 归档触发（无周变更检测）

每次 `app/build.py` 运行：

1. fetch 服务器当前 `/api/papers`、`/api/weekly`、`/api/trending` → 当前周 payload。
2. 解析当前周 label / title / range。
3. 写 `data/weeks/<当前label>.json`（同 label 幂等覆盖；换周时新建文件）。
4. 刷新 `data/weeks/manifest.json`：glob `data/weeks/*.json`，按 `range.start` 倒序，把 `current=true` 标记给步骤 2 解析出的当前 label，其余 `false`。
5. 渲染 `site/index.html` = 当前周（现有行为不变）。
6. 对 `data/weeks/` 里每个 `label != 当前label` 的归档，渲染 `site/week/<label>.html`（用该归档 payload 内联 + 切换器）。当前周不进 `site/week/`，避免与 index.html 重复。

上一周的快照在上一次 build 时已落盘，换周后它自然成为归档——无需周变更检测、无需从 HTML 反向抽取（首次回填除外）。

### 3.3 一次性回填

首次启用本功能时，现有 `site/index.html` 还冻结着上一周。执行一次回填脚本（并入 `app/build.py` 的 `--backfill` 子命令或独立 `agent/backfill_weeks.py`）：

- 从 `site/index.html` 内联的 `window.__PAPERS__/__WEEKLY__/__TRENDING__` 正则抽取三个 JSON。
- 解析 overview 得 label/title/range。
- 写 `data/weeks/<label>.json` + 更新 manifest。
- 之后正常运行 build 即可维护。

### 3.4 渲染（app/build.py 改造）

- 抽出公共 `render_page(payload, weeks_manifest, week_label_or_none) -> html`：基于 `app/page.py` 的 `INDEX_HTML` 模板，内联 `window.__PAPERS__/__WEEKLY__/__TRENDING__/__WEEKS__/__WEEK_LABEL__`，并把 `fetch("/api/...")` 重写为读全局（沿用现有 `rewrite_index` 技法）。
- `site/index.html`：`render_page(当前payload, manifest, None)`。
- `site/week/<label>.html`：`render_page(归档payload, manifest, label)`，并把 `paper/<id>` 与 `notes.html` 等链接前缀 `../`（因位于 `week/` 子目录）。

### 3.5 运行时路由（app/server.py 改造）

- `/api/weeks` → 返回 `data/weeks/manifest.json`。
- `/week/<label>` → 读 `data/weeks/<label>.json`，用 3.4 的 `render_page` 同款内联渲染（PAPERS/WEEKLY/TRENDING/WEEKS/WEEK_LABEL 全内联），返回冻结页。归档页不 fetch。
- `/`（本周）→ 现有 live fetch 行为不动；仅在返回 HTML 里额外注入 `window.__WEEKS__ = manifest`，供切换器读取。`window.__WEEK_LABEL__` 在 `/` 上为 `null`。
- 不建 `/api/week/<label>`（导航式不需要 JS 取 payload，YAGNI）。

### 3.6 切换器 UI（app/page.py 改造）

- 位置：`scope-top` header，紧挨现有「调研笔记」`nav-link`。
- 形态：`<select id="week-switch">` 下拉，样式套 `.nav-link` chip 调子（等宽、琥珀色边框）。
- 选项：第一项「本周 · <title>」（value 指向当前周入口），其后按 manifest 倒序列历史周。`window.__WEEK_LABEL__` 匹配项标 `selected`；`null` 时选「本周」。
- 导航：`change` 事件里
  - 静态：当前周 → `index.html`（若在 `week/` 子目录则 `../index.html`）；历史周 → `week/<label>.html`（子目录内则 `<label>.html`）。
  - 运行时：当前周 → `/`；历史周 → `/week/<label>`。
  - 路径前缀由页面位置（是否在 `week/` 子目录）决定，渲染时内联一个 `window.__WEEKS_BASE__`（`""` 或 `"../"`）给 JS 拼。
- 移动端：原生 `<select>` 兼容，无需额外适配。

## 4. 数据流

```
weekly_summary.json(手写) ──┐
                            ├─> server /api/* ─> build.py fetch ─> data/weeks/<label>.json(当前)
research_runs/*.json ──┐    │                                       │
                       └─> /api/research-runs ─> sqlite             ├─> manifest.json
                                            │                        │
                                            └─> /api/papers ────────┘
                                              (build.py 把当前周内联进 site/index.html，
                                               把每个历史周内联进 site/week/<label>.html)

runtime:  / ───────────────────> page.py + live fetch(/api/*) + 注入 window.__WEEKS__
          /week/<label> ───────> render_page(归档payload) 冻结页
          /api/weeks ──────────> manifest.json
static:   site/index.html ────> 当前周冻结页（build 时快照）
          site/week/<label>.html > 历史周冻结页
          site/paper/<id>.html ─> 累积归档（已有，复用）
```

## 5. 错误处理

- build.py fetch `/api/weekly` 失败：沿用现有回退 `{"overview":"","highlights":[]}`（build.py:96 已处理）；label 解析失败 → 回退 build 日 ISO 日期，manifest 仍写入。
- `data/weeks/<label>.json` 读取失败（运行时 `/week/<label>`）：返回 404 + 简短提示「该周归档不存在」。
- manifest 为空（首次未回填）：切换器只显示「本周」一项，不报错。
- 归档 payload 缺 trending：`window.__TRENDING__` 回退 `{"items":[]}`。

## 6. 测试

- `agent/build_notes.py` 风格的轻量自检脚本（或 build.py `--check`）：
  1. 回填后 `data/weeks/2026-06-26.json` 存在，papers 数量与 `site/index.html` 内联数一致。
  2. 跑一次 build（mock 服务器或本地 server）后，`manifest.json` 含当前周且 `current=true`；`site/week/<历史label>.html` 生成；`index.html` 为当前周。
  3. 切换器：`site/week/<历史label>.html` 里 `window.__WEEK_LABEL__` 等于该 label；`index.html` 里为 `null`。
  4. 相对路径：`site/week/*.html` 里 `paper/<id>` 链接带 `../` 前缀；`index.html` 里不带。
- 人工：本地起 server，访问 `/` 与 `/week/2026-06-26`，切换器在两页之间跳转正常；GitHub Pages 上 `site/` 同样可切。

## 7. 改动清单

| 文件 | 改动 |
|---|---|
| `app/build.py` | 抽 `render_page`；每次 build 写当前周 `data/weeks/<label>.json` + manifest + 渲染历史周 `site/week/<label>.html`；加 `--backfill` 从现有 `site/index.html` 回填 |
| `app/server.py` | 加 `/api/weeks`、`/week/<label>` 路由；`/` 返回注入 `window.__WEEKS__` |
| `app/page.py` | header 加 `<select id="week-switch">` + 切换 JS（读 `__WEEKS__`/`__WEEK_LABEL__`/`__WEEKS_BASE__`，change 即导航） |
| `data/weeks/` | 新目录；`<label>.json` × N + `manifest.json` |

## 8. 风险与取舍

- **overview 文本解析脆弱**：overview 格式若改动会解析失败。回退到 build 日日期可保不崩，但 label 会不准。后续可给 `weekly_summary.json` 加结构化 `week` 字段硬化，本期不做。
- **静态站相对路径**：`week/` 子目录与根目录的链接前缀差异靠 `__WEEKS_BASE__` 与 `paper/` 链接重写处理，需仔细测。
- **归档页冻结**：历史周不再 live，paper 列表与热点固定在 build 时快照——这是预期行为（历史不应变）。
- **无限累积体积**：每周一个 json + html，量级很小，暂不清理；若未来成问题再加滚动清理。
