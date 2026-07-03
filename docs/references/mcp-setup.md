# MCP 配置说明（项目级）

> 本文件告诉任何进入本仓库的 agent：调研用哪些 MCP、装在哪、怎么激活、每个工具怎么用。
> MCP 配置已沉淀为项目级 `.mcp.json`（仓库根目录），不依赖用户级 opencode 配置。
> **运行态说明**：`.mcp.json` 只是配置态。子 agent 在沙箱环境运行时 MCP 可能不可用，此时走公开 HTTP API 兜底：arXiv `export.arxiv.org/api/query`、HuggingFace `huggingface.co`、GitHub `api.github.com`。逻辑一致，只是传输层不同。

## 概览

调研 agent 搜集阶段用三个 MCP + websearch 互补：

| MCP | 用途 | 是否需 token | 包/命令 |
|---|---|---|---|
| arxiv | 全量结构化搜 arXiv 论文（精准，10× websearch） | 否 | `uvx arxiv-mcp-server` |
| huggingface | HF Daily Papers 社区投票精选热门论文 | 否 | `uvx huggingface-daily-paper-mcp` |
| github | 搜开源仓 trending + release（仅业界大项目） | 是（PAT） | `npx -y @modelcontextprotocol/server-github` |
| websearch | 补充搜大厂官网博客/产品发布（官方域名） | 否 | agent 内置 |

## 前置依赖

- `uv` / `uvx`（跑 arxiv、huggingface MCP）：安装见 https://docs.astral.sh/uv/
- `node` / `npx`（跑 github MCP）：Node.js LTS 自带
- 三个命令本机均已可用（`uv 0.11.21` / `npx` / `node`）

## 激活方式（Claude Code）

`.mcp.json` 是项目级配置，Claude Code 启动时自动读取。首次使用：

1. 重启 Claude Code 会话（或 `/reload-plugins --force`）。
2. 首次调用某 MCP 工具时会弹权限确认，批准即可。
3. 用 `/mcp` 查看已连接的 MCP 及其工具状态。

> opencode 用户级配置（`~/.config/opencode/opencode.json`）里也有同名 arxiv/huggingface MCP，互不影响。本项目以 `.mcp.json` 为准。

## github MCP 的 token

github MCP 走 GitHub API，需要 Personal Access Token（PAT）否则严重限速：

1. 在 https://github.com/settings/tokens 生成 PAT（只需 `public_repo` 读权限即可读公开仓 release）。
2. 设环境变量：`GITHUB_PERSONAL_ACCESS_TOKEN`（Windows: `setx GITHUB_PERSONAL_ACCESS_TOKEN xxx`，重开终端生效）。
3. 不设 token 时 arxiv/huggingface MCP 仍可用，仅 github MCP 会限速/失败。

## 工具使用逻辑（搜集阶段）

### arxiv MCP（`blazickjp/arxiv-mcp-server`）
- `search_papers(query, max_results, sort_by, category, author)`：按关键词搜 arXiv，返回结构化 JSON（标题/作者/摘要/日期/arxiv id）。`sort_by="submittedDate"` 拿最新。
- `download_paper(paper_id)`：下载 PDF 到本地缓存。
- `read_paper(paper_id)`：读论文全文（markdown）。
- 自动限速 3 秒间隔 + 24 小时缓存，符合 arXiv API 规范。
- **date 字段必须取自这里返回的 submittedDate，不许 agent 自填**（防 date 漂移/旧论文充本周）。

### huggingface MCP（`huggingface-daily-paper-mcp`）
- `get_today_papers()` / `get_yesterday_papers()`：当天/昨天社区精选。
- `get_papers_by_date(date=YYYY-MM-DD)`：按日期取精选（过去 7 天每天调一次）。
- 每天约 20 篇社区投票热门，质量比 arXiv 全量高、覆盖窄，和 arXiv 互补。

### github MCP（`@modelcontextprotocol/server-github`）
- 搜开源仓 trending / release：仅收**业界认可大项目**（见 `docs/references/big-projects-whitelist.md`，如 Google ADK / NVIDIA TensorRT Edge Agent / vLLM / SGLang / llama.cpp / ExecuTorch / MLC-LLM 等）。
- 门槛：必须在白名单内 + 最近 7 天有 release/重大 commit + 主题相关。非白名单小仓不收。

### websearch（补充）
- 搜大厂官方博客/产品发布，命中 `vendor-whitelist.md` 官方域名才算。
- 非官方博客/新闻/社媒/二手解读一律排除。

## 排查

- MCP 没连上：`/mcp` 看状态。Windows 上最常见的是 Node 直接 spawn `uvx`/`npx` 不走 shell PATH 解析导致启动失败——`.mcp.json` 已用 `cmd /c uvx` / `cmd /c npx` 包一层规避（可移植，不写死用户路径）。若仍失败，把 `command` 改成绝对路径（如 `C:\\Users\\<you>\\AppData\\Local\\hermes\\bin\\uvx.exe`，args 去掉 `uvx`）。
- arxiv 返回空：换关键词、放宽 `max_results`、检查网络。
- github 限速：补 PAT（`GITHUB_PERSONAL_ACCESS_TOKEN`）。
- github MCP 与 `github` 插件自带的远程 MCP（`api.githubcopilot.com/mcp/`，需 GitHub OAuth）冲突时：本项目用 `.mcp.json` 的本地 PAT 版，忽略插件远程版（或禁用该插件）。
- 首次 `uvx` 会下载包，较慢，之后有缓存。
