# DESIGN.md — edge_agent 技术设计

> 配套 `SPEC.md`（做什么）与 `ARCHITECTURE.md`（架构）。本文件定"怎么实现"。
> 骨架版，随实现演进；spec 变更先改 SPEC 再改本文件。

## 1. 搜集工作流（runtime）
每周触发（cronjob 或手动，先手动跑通再上 cron）：
1. 算 cutoff：`now - 7d`（读 `.last_run` 支持滚动；`never` 则首次用 `now-7d`）
2. 加载已收录集：`data/index.json`
3. 四源并行检索（学术 / 博客 / GitHub / 发布），各源适配检索方式
4. 候选条目去重（URL / arxiv id 匹配 `index.json`）
5. 评分（SPEC 第六节），runtime 裁量纳入
6. 纳入条目写 `content/posts/<slug>.md`
7. 更新 `index.json` + `.last_run`
8. 本地 build → push `site/` 到 GitHub

## 2. 状态管理
- `data/index.json`：去重索引，`{entries:[{id, slug, title, source_type, date, url, score, vendors, branches, recommendation}], last_updated}`
- `data/.last_run`：ISO 时间戳，滚动窗口起点（`never` = 尚未运行）
- 二者 git 跟踪，可恢复可审计

## 3. 内容模型（frontmatter）
`content/posts/<slug>.md` 每条带 frontmatter，关键字段：
`title / authors / org / source_type / date / url / abstract / branches / vendors / mechanism / effects / contribution / score / recommendation / review_hint`
（待 SPEC 第八节输出格式映射成 frontmatter schema 定稿，机械化校验脚本待补）

## 4. 机械化强制（待补，spec / 选型定后）
- frontmatter schema 校验（缺字段 → build 失败）
- 过滤规则检查（日期 / affiliation / 来源链接 → 拒收）
- 去重检查（`index.json` 与 `content/` 一致性）
- LLM auditor 抽查内容符合收录标准
- build 脚本（依赖网站选型）

## 5. 熵管理（待补，跑通后）
- 定期扫过期内容（超一周窗口的标注 / 归档）
- 重复、死链、frontmatter 漂移 → 修整 PR

## 6. 待定
- 网站选型（Hugo / Astro / MkDocs）→ 影响 build + `site/` 结构
- cronjob 周更 vs 手动触发（先手动跑通再上 cron）
