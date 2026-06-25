# DESIGN.md — edge_agent 技术设计

> 配套 `SPEC.md`（做什么）与 `ARCHITECTURE.md`（职责边界）。本文件定"agent 如何使用本仓完成一次周报搜集与展示"。
> 骨架版，随实现演进；spec 变更先改 SPEC / README，再改本文件。

## 1. Agent 搜集工作流
每周由 Codex / Hermes 等 agent 手动或定期唤起执行。仓库不内置固定爬虫 / 信息源适配器，agent 使用自身搜索、浏览、阅读工具完成检索。

1. 读 `README.md` 获取本次搜集提示词、检索式、纳入排除标准、评分体系
2. 算 cutoff：读 `data/.last_run`；若为 `never`，首次用 `now - 7d`
3. 加载已收录集：`data/index.json`
4. 检索四类信息源：学术论文 / 厂商博客 / GitHub releases / 产品大会发布
5. 候选条目去重：URL / arXiv id / slug / title 对照 `index.json`
6. 阅读原文并抽取事实；实际效果必须来自原文，摘不到写"未报告"
7. 按 SPEC 第六节评分，由执行 agent 裁量纳入 / 纳入待复审 / 排除
8. 纳入条目写 `content/posts/<slug>.md`
9. 更新 `data/index.json`，保持 id/slug 与 post 文件一致
10. 跑 `python scripts/gate_all.py`；失败则修 post/index 后重跑
11. gate 过后写 `data/.last_run` = now（ISO）
12. 本地 build `site/`，再按需要 push 到 GitHub Pages 展示

## 2. 状态管理
- `data/index.json`：去重索引，`{entries:[{id, slug, title, source_type, date, url, score, vendors, branches, recommendation}], last_updated}`
- `data/.last_run`：ISO 时间戳或 `never`，作为下一次 agent 搜集的滚动窗口起点
- `data/vendors.yaml`：机器可读大厂白名单，供 vendor gate 与评分参考
- 三者由 git 跟踪，可恢复可审计；不要把已收录列表只留在 agent 对话或工具记忆里

## 3. 内容模型（frontmatter）
`content/posts/<slug>.md` 每条带 frontmatter，关键字段：
`id / slug / title / authors / affiliations / source_type / date / url / branches / vendors / score / score_relevance / score_vendor / score_contribution / score_quality / score_recency / recommendation / review_hint`

字段规范以 `scripts/frontmatter.schema.json` 为机械化准绳。README 第八节是 agent 产出分析格式，frontmatter 是展示与 gate 使用的结构化映射。

## 4. 机械化强制
- frontmatter schema 校验：缺字段、类型不对、score 越界直接失败
- score 维度校验：五个维度之和必须等于 `score`
- 去重一致性：`index.json` entries 与 `content/posts/*.md` 双向一一对应
- 时间窗口：post 日期必须落在 `.last_run` 推导出的过去一周窗口内，且不能是未来日期
- vendor 白名单：frontmatter `vendors` 只能使用 `data/vendors.yaml` 中的标准 name
- build 前必须跑 `python scripts/gate_all.py`，不过 gate 不允许更新 `.last_run` 或 push 展示结果

## 5. 展示构建
- 当前 `scripts/build.py` 是极简 SSG：读取 `content/posts/*.md`，生成 `site/index.html`
- `site/` 是 build 产物，用于 GitHub Pages 展示，不是内容源头
- 后续如换 Hugo / Astro / MkDocs，`content/posts/*.md` 和 `data/index.json` 的数据边界不变，只替换 build 实现

## 6. 熵管理（待补，跑通后）
- 定期扫重复条目、死链、frontmatter 漂移
- 检查 index 与 posts 是否长期一致
- 检查 vendor 白名单是否漏判新厂商 / 机构
- 将 agent 运行中的错误沉淀到 `AGENTS.md` 已知教训

## 7. 待定
- 网站选型：继续极简 SSG，还是改 Hugo / Astro / MkDocs
- agent 周更触发方式：手动运行、提醒自动化，还是外部调度唤起
- 是否增加 agent 搜集前/后 checklist，降低漏跑 gate 或漏更新 `.last_run` 的概率
