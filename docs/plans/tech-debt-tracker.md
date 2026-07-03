# Tech Debt Tracker

## Active

- [ ] 给 `app/server.py` 增加鉴权配置，避免公开写入 `POST /api/research-runs`。
- [ ] 增加真实调研 run fixture，用于端到端展示 10 到 20 篇论文。
- [ ] 给 `GET /api/papers` 增加 `window=7d` 参数。

## Completed

- [x] 清理旧非论文样例和 2025 旧样例。
- [x] 把最终流程改成主 agent 调研发布到服务器。
- [x] 增加 `validate_research_run.py` 和 `publish_results.py`。
- [x] 增加服务器 `POST /api/research-runs` / `GET /api/papers` / `POST /api/insights`。
- [x] 增加死链检查脚本（已实现于 `agent/research_run.py::is_link_alive`）。
