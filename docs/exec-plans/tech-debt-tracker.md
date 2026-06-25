# Tech Debt Tracker

> 记录已知技术债与待补项，随实现演进。完成项移 `docs/exec-plans/completed/`。
> 每次 agent 出错或发现缺漏，在此追加（呼应 AGENTS.md 免疫系统）。

## 待补
- [ ] `scripts/` 机械化强制补强：过滤规则检查、死链检查、build 输出检查
- [ ] 熵管理 agent：过期 / 重复 / 死链 / frontmatter 漂移扫描
- [ ] 网站选型（Hugo / Astro / MkDocs）→ build + `site/` 结构
- [ ] `content/posts/` frontmatter schema 定稿（SPEC 第八节映射）
- [ ] GitHub 展示仓库初始化 + Pages 开启
- [ ] agent 周更触发方式（手动运行 / 提醒自动化 / 外部调度唤起）
- [ ] agent 运行检查清单（读 README → 搜索 → 写 post/index → gate → build → push）
