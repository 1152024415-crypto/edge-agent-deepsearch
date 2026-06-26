# Main Agent Workflow

本文件给主 code agent 使用。主 agent 负责调度、校验和发布；调研子 agent 只负责搜索和输出结构化结果。

## 1. 准备上下文

主 agent 必须先读取：

- `AGENTS.md`
- `docs/agent-guide/research-prompt.md`
- `docs/agent-guide/output-contract.md`
- `docs/agent-guide/validation-rules.md`
- `data/index.json`

## 2. 发起调研子 agent

对子 agent 的任务要求：

- 搜索最近一周端侧 AI agent / mobile agent / edge agent / embedded agent 相关论文。
- 目标数量 10 到 20 篇。
- 只收真实论文，不收厂商博客、产品发布、GitHub release。
- 每篇必须给出标题、摘要、效果、工作原理、论文链接、分数。
- 输出必须符合 `docs/agent-guide/output-contract.md`。
- 子 agent 不修改网页、不发布服务器、不写入 `content/papers/`。

## 3. 保存调研结果

主 agent 将子 agent 结果保存为：

```text
research_runs/run-YYYYMMDD-HHMMSS.json
```

## 4. 本地校验

运行：

```powershell
python agent/validate_research_run.py research_runs/run-YYYYMMDD-HHMMSS.json
```

失败处理：

- 时间过期：删除或要求子 agent 补新论文。
- 非论文来源：删除。
- 链接不匹配：删除或重新核验。
- 字段缺失：要求子 agent 补全。

不能为了凑数量强行发布。

## 5. 发布到服务器

服务器启动：

```powershell
python app/server.py --host 127.0.0.1 --port 8000
```

发布：

```powershell
python agent/publish_results.py research_runs/run-YYYYMMDD-HHMMSS.json --server http://127.0.0.1:8000
```

## 6. 验证页面

打开：

```text
http://127.0.0.1:8000/
```

或检查 API：

```text
http://127.0.0.1:8000/api/papers
```

页面应该显示服务器中最新的调研结果。没有本周合格论文时，应显示空状态。
