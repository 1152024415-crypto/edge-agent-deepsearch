# 发布前检查清单（周刷新 → 部署 GitHub Pages）

> 强制「完成前」逐项勾。机械项由 `app/gates/gate_release.py` 拦（FAIL 不许部署）；
> 体验/编辑项靠人执行——assertIn/count 测不出的功能回归全在这里。

## 机械门（gate_release，FAIL 即阻断）

- [ ] `python app/gates/gate_all.py` 通过（含 gate_release）
  - __PAPERS__ 是 `{"papers":[...]}` 字典（非裸数组）；无 `window.__WEEKS__ = [` 运行时注入泄漏
  - 每个内联 paper id 有 `site/paper/<id>.html`；每个历史周有 `site/week/<label>.html`；`site/notes.html` 在
  - weekly_summary highlights 外部 URL（厂商博客/新闻）≥5，非 paper_id 复读
  - 当前周 `官方动态` ≥1；为 0 则有 `data/weeks/<label>-no-vendor.md` 逐厂证据

## 体验项（chrome-devtools 真点，每类链接都要 200）

- [ ] 打开 `site/index.html`（或在线 URL）硬刷新
- [ ] 论文行：点击 → overlay 弹出有内容（或跳详情页 200，非 404）
- [ ] **热点链接**：点前 3 条 → 跳详情页/外部页 200，非 404
- [ ] **周切换器**：切到上周 → 上周页 166 篇渲染、`__WEEK_LABEL__` 正确；切回本周 → 114 篇
- [ ] 返回链接（详情页 `← 返回雷达`）→ 回 index 200
- [ ] 调研笔记 nav → notes.html 200

## 编辑项（跟设计/上周对比）

- [ ] 重读上周 `data/weeks/<上周>.json` 的 weekly.highlights 格式（外部新闻 URL）
- [ ] 本周 highlights 是**编辑性新闻**（厂商动态/行业事件，外部 URL），不是 run top N 论文复读
- [ ] source_tier 分布合理：`官方动态`（厂商博客）非 0；`公司项目`（公司研究论文）≠ 全博客（博客归官方动态档）
- [ ] overview 是本周动态综述，不是论文列表的拼接

## 流程顺序（编辑层 ≠ 采集层）

1. 采厂商动态（18 厂博客 + 模型实验室博客）→ `官方动态` 条目
2. 写 `data/weekly_summary.json`（从厂商新闻 + 判断，≥5 外部 URL）
3. run 论文列表是另一层，不填进 highlights

## 沉淀

- [ ] 本周新错进 `AGENTS.md` 已知教训 + `validation-rules.md`
