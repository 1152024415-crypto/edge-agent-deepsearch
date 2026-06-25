# Tech Debt Tracker

> 记录已知技术债与待补项，随实现演进。完成项移 `docs/exec-plans/completed/`。
> 每次 agent 出错或发现缺漏，在此追加（呼应 AGENTS.md 免疫系统）。

## 待补
- [ ] `scripts/` 机械化强制：frontmatter 校验、过滤检查、去重检查、build
- [ ] 熵管理 agent：过期 / 重复 / 死链 / frontmatter 漂移扫描
- [ ] 网站选型（Hugo / Astro / MkDocs）→ build + `site/` 结构
- [ ] `content/posts/` frontmatter schema 定稿（SPEC 第八节映射）
- [ ] GitHub 展示仓库初始化 + Pages 开启
- [ ] cronjob 周更自动化（先手动跑通）
- [ ] 各信息源检索适配器（arXiv API / 厂商博客订阅 / GitHub releases API / 大会议程）
