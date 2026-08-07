# edge_agent

> 在线展示：https://1152024415-crypto.github.io/edge-agent-deepsearch/

端侧 AI Agent 论文雷达。这个仓库不是传统爬虫项目，也不是只靠 GitHub Pages 展示的 demo；它的最终流程是 **主 code agent 调度调研子 agent，校验调研结果，然后把结果发布到服务器，网页从服务器刷新最新论文列表**。

## 快速开始：跑一次调研并展示

**一键入口**：

```bash
bash agent/run_weekly.sh
```

脚本自动完成所有机械步骤（token/server/sweep/attest/assemble/validate/publish/build/gate/deploy），最后输出本地 + GitHub 两个 URL。需要 agent 智能的步骤（子 agent 调度、翻译、推荐策展）脚本会暂停并打印指令。

如果需要手动操作，下面是完整 10 步（和 `docs/harness.md` 第 3 节主循环、`AGENTS.md` 工作流一致，不许跳步）：

1. **读强入口文档**：`AGENTS.md` → `docs/harness.md` → `.agents/skills/edge-agent-research-pipeline/SKILL.md`。再读 `docs/agent-guide/research-prompt.md`、`output-contract.md`、`validation-rules.md`，以及 `docs/references/mcp-setup.md`、`tag-taxonomy.md`、`big-projects-whitelist.md`。不读就动手，必然漏标准、编断链。

2. **查时间窗口**：读 `data/.last_run` 里的上次调研时间戳。距本次 ≥7 天才跑；不到 7 天就提示"本周已调研"然后停。防重复跑、防拿旧 run 充本周。

3. **发起调研子 agent**：注入 `research-prompt.md` 全文。检索尽量广：明确端侧和端侧技术栈必收，有直接迁移价值的通用推理/serving 也低分保留；只删完全无关、越窗、不可信、链接不匹配和重复项。自动搜集一律标 `纳入`，推荐由主 agent 阅读来源后策展。

4. **覆盖清单 + 候选证明**：四类来源先完成 `research_runs/collection-manifest.json`（动态7日、arXiv分页到窗口外、HF逐日、GitHub release/trending分离、24厂商/模型实验室逐家成功来源证据），再运行 `python agent/attest_candidates.py` 绑定四个候选文件的条数和 SHA-256；缺项、不可达或产物不一致都不能继续。主 agent 再完成评分、中文整理和推荐，保存 run JSON。

5. **校验**：跑 `python agent/validate_research_run.py research_runs/<run_id>.json`。命令先验覆盖清单，再验内容、精确7日窗口、评分、标签、链接、arXiv date 和去重。普通但相关的低贡献内容不因分数低删除；完全无关或来源不合格才丢。

6. **抽检官方/开源条目**：publish 前，fetch 每个 `source_tier=官方动态` 和 `source_tier=开源大项目` 的 URL，对比页面内容 vs 标题摘要。URL 能开 ≠ 内容对题，对不上就丢。

7. **启动服务器**（如未跑）：

   ```powershell
   $env:EDGE_PUBLISH_TOKEN = "<本机随机长令牌>"
   python app/server.py --host 127.0.0.1 --port 8001
   ```

8. **发布**：

   ```powershell
   $env:EDGE_PUBLISH_TOKEN = "<与服务端相同的令牌>"
   python agent/publish_results.py research_runs/<run_id>.json --server http://127.0.0.1:8001
   ```

9. **看效果**：浏览器打开 `http://127.0.0.1:8001/`。按标签 chip 筛选展示，source_tier 优先 + score 排序；点标题进详情页（短摘要 + tags + 原文链接，无「整理中」）。服务器 `GET /api/papers` 只返回最新 run。

10. **收尾**：把 `data/.last_run` 时间戳更新成本次调研时间（ISO 8601，如 `2026-06-26T15:00:00+08:00`）。本周踩到的错误沉淀进 `AGENTS.md` 已知教训 + `docs/agent-guide/validation-rules.md` + `research-prompt.md`，靠 repo 不靠记忆。最后跑 `python tests/test_research_pipeline.py`、`python tests/test_build.py`、`python app/gates/gate_all.py` 确认 harness 健康。

## 最终流程

1. 主 agent 读取 `AGENTS.md` 和 `docs/agent-guide/`。
2. 主 agent 发起一个或多个调研子 agent。
3. 子 agent 按 `docs/agent-guide/research-prompt.md` 搜索、阅读、审查论文。
4. **保存产出**：子 agent 输出结构化候选和 collection manifest，主 agent 完成最终筛选+评分+打标+推荐后存成 run JSON（相关内容尽量全收，不设上限）。
5. 主 agent 运行 validate；覆盖清单不完整时命令直接失败。
6. 校验通过后，主 agent 运行 `python agent/publish_results.py research_runs/<run_id>.json --server <SERVER_URL>`。
7. 服务器接收 `POST /api/research-runs`，写入 SQLite。
8. 展示页调用 `GET /api/papers`，刷新出最新调研结果。

## 目录结构

| 路径 | 用途 |
|---|---|
| `.agents/skills/edge-agent-research-pipeline/SKILL.md` | 项目内 skill，新 codeagent 优先读取 |
| `AGENTS.md` | agent 工作总指引 |
| `docs/README.md` | 文档索引 |
| `docs/agent-guide/research-prompt.md` | 调研子 agent 使用的搜索提示词 |
| `docs/agent-guide/output-contract.md` | 子 agent 输出 JSON 契约 |
| `docs/agent-guide/validation-rules.md` | 论文真实性、时间窗口、链接匹配规则 |
| `docs/agent-guide/main-agent-workflow.md` | 主 agent 调度、校验、发布流程 |
| `docs/references/mcp-setup.md` | MCP 配置和工具用法（arXiv/HF/GitHub） |
| `docs/references/tag-taxonomy.md` | 标签词表人读版（机器版 data/tags.yaml） |
| `docs/references/big-projects-whitelist.md` | 开源大项目白名单 |
| `docs/references/vendor-research-guide.md` | 厂商调研方法（官方 URL/affiliation 搜法） |
| `research_runs/` | 子 agent 每次调研的 JSON 输出 |
| `agent/research_run.py` | research run 校验库 |
| `agent/validate_research_run.py` | 校验子 agent 输出 |
| `agent/publish_results.py` | 发布调研结果到服务器 |
| `app/server.py` | HTTP 路由和服务器入口 |
| `app/storage.py` | SQLite 存储和 paper upsert/query |
| `app/page.py` | 服务器展示页 HTML shell |
| `content/papers/` | 兼容旧静态 build 的本地论文 Markdown，不再作为最终展示来源 |
| `site/` | 静态 build 产物，仅作 fallback |

## 本地运行服务器

```powershell
$env:EDGE_PUBLISH_TOKEN = "<本机随机长令牌>"
python app/server.py --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000/
```

## 发布一次调研结果

调研子 agent 产出：

```text
research_runs/run-20260625-120000.json
```

校验：

```powershell
python agent/validate_research_run.py research_runs/run-20260625-120000.json
```

发布：

```powershell
$env:EDGE_PUBLISH_TOKEN = "<与服务端相同的令牌>"
python agent/publish_results.py research_runs/run-20260625-120000.json --server http://127.0.0.1:8000
```

## 核心约束

- 页面展示真论文 + 大厂官方动态 + 开源大项目更新三类，用 `source_tier` 标注；不许把非官方博客、新闻、社媒、GitHub release、二手解读伪装成官方动态。
- 论文/动态必须是当前日期过去 7 天窗口内的新内容；arXiv 条目 date 必须取自 arXiv 元数据，validate 核对。
- `paper_url` 必须指向论文原文、权威论文页、官方来源页或 github 仓，标题和摘要必须匹配。
- `effects` 必须来自论文原文或官方来源；没有报告就写 `未报告`。
- 服务器只接收和展示结果，不负责搜索论文；搜索由 agent 工具完成。
- 没有本周合格内容时，页面显示空状态，不允许拿旧样例撑场面。

## 验证命令

```powershell
python tests/test_research_pipeline.py
python tests/test_build.py
python app/gates/gate_all.py
```
