# Site API Contract

服务器负责接收主 agent 发布的调研结果，并给展示页提供最新数据。

## GET /api/papers

Returns papers from the latest accepted research run only. Historical runs may stay in SQLite for audit/debugging, but the display page must not mix old runs into the current radar.

返回当前服务器中可展示的论文/官方动态/开源大项目列表。排序先按经核实的`edge_agent_scope`（手机 > PC > 其他端侧 > 非端侧Agent），再按 `source_tier` 优先级（官方动态 > 开源大项目 > 公司项目 > 学校顶会 > 学校预印本）+ `score` 降序。
前端按标签 chip 多选筛选展示（多标签，一个工作可挂多个 tag）；`source_tier` 用 badge 标注。

Query:

- `sort=score`：按分数降序。
- `sort=date`：按日期降序。

Response:

```json
{
  "papers": [
    {
      "id": "fresh-edge-agent-paper",
      "run_id": "run-20260625-120000",
      "title": "Fresh Edge Agent Paper",
      "title_zh": "端侧智能体规划框架",
      "abstract": "这项工作让端侧智能体在手机本地完成规划与执行。",
      "effects": "在真实手机上将推理延迟降低了 23%。",
      "mechanism": "通过压缩本地记忆和规划执行循环减少资源开销。",
      "paper_url": "https://arxiv.org/abs/2606.12345",
      "date": "2026-06-24",
      "score": 14,
      "score_relevance": 9,
      "score_contribution": 5,
      "score_reason": "主题直接命中端侧 agent，报告了明确 benchmark 提升。",
      "source_tier": "学校顶会",
      "open_source": false,
      "tags": ["方向:端侧agent", "方向:记忆", "方向:评测基准"],
      "edge_agent_scope": "手机",
      "edge_agent_evidence": "规划、记忆和工具执行均在手机本地运行。",
      "insight_person": "",
      "wiki_url": "",
      "authors": "",
      "vendors": "",
      "venue": "",
      "recommendation": "推荐",
      "recommendation_reason": "端侧收益明确，并在真实设备上给出了可核验的改善。",
      "updated_at": "2026-06-25T04:00:00+00:00"
    }
  ]
}
```

## GET /api/weekly

返回本周热点综述，数据来自 `data/weekly_summary.json`。

Response:

```json
{
  "overview": "本周端侧 agent 雷达综述一句话。",
  "highlights": [
    {
      "paper_id": "fresh-edge-agent-paper",
      "topic": "端侧 VLM 量化部署",
      "why": "首次在手机 NPU 上跑通 4-bit VLM，延迟 < 100ms。"
    }
  ]
}
```

## GET /api/community

返回独立的 7 日社区雷达。它不属于 research run，也不会混入 `GET /api/papers`。历史周页面使用当周冻结的 `community` 快照。

Response:

```json
{
  "window": {"start": "2026-08-07", "end": "2026-08-13"},
  "coverage": [
    {"source": "X", "status": "limited", "note": "公开索引受限，未找到可直接核验的本周原帖。"}
  ],
  "items": [
    {
      "id": "reddit-local-agent-test",
      "source": "Reddit",
      "author": "r/LocalLLM",
      "url": "https://www.reddit.com/r/LocalLLM/comments/example/",
      "published_at": "2026-08-12T12:00:00Z",
      "title_zh": "本地智能体设备实测",
      "summary_zh": "社区在真实设备上完成了模型和工具调用测试。",
      "why_it_matters": "补充正式基准之外的可用性与部署取舍。",
      "device_scope": "PC",
      "topic": "Agent",
      "verification": "仅线索",
      "evidence_url": ""
    }
  ]
}
```

`coverage` 必须完整覆盖 X / Bluesky / Reddit / Hacker News / Mastodon / GitHub Discussions / Hugging Face / YouTube-Bilibili / 厂商论坛；status 只能是 `found` / `no_match` / `limited` / `unavailable`。`device_scope` 只能是手机 / PC / 其他端侧 / 通用技术；`verification` 只能是仅线索 / 已回链原始材料 / 已进入正式周报。社媒讨论 URL 不得直接作为正式 papers 的 `paper_url`。

## POST /api/research-runs

主 agent 用 `agent/publish_results.py` 调用。服务器会再次校验 payload。

请求必须携带 `Authorization: Bearer <EDGE_PUBLISH_TOKEN>`；服务端未配置令牌时所有写 API 返回 503，令牌缺失或错误返回 401。payload 必须包含完整 `collection_manifest`，其中候选文件条数、文件 SHA-256 和逐记录指纹已由 `agent/attest_candidates.py` 生成；每条 paper 的 `candidate_source` + `candidate_ref` 必须命中对应候选记录。

Request:

```json
{
  "run_id": "run-20260625-120000",
  "generated_at": "2026-06-25T12:00:00+08:00",
  "papers": [
    {
      "id": "fresh-edge-agent-paper",
      "title": "Fresh Edge Agent Paper",
      "title_zh": "端侧智能体规划框架",
      "abstract": "这项工作让端侧智能体在手机本地完成规划与执行。",
      "effects": "在真实手机上将推理延迟降低了 23%。",
      "mechanism": "通过压缩本地记忆和规划执行循环减少资源开销。",
      "paper_url": "https://arxiv.org/abs/2606.12345",
      "date": "2026-06-24",
      "score": 14,
      "score_relevance": 9,
      "score_contribution": 5,
      "score_reason": "主题直接命中端侧 agent，报告了明确 benchmark 提升。",
      "source_tier": "学校顶会",
      "open_source": false,
      "tags": ["方向:端侧agent", "方向:记忆", "方向:评测基准"],
      "edge_agent_scope": "手机",
      "edge_agent_evidence": "规划、记忆和工具执行均在手机本地运行。",
      "insight_person": "",
      "wiki_url": "",
      "recommendation": "推荐",
      "recommendation_reason": "端侧收益明确，并在真实设备上给出了可核验的改善。"
    }
  ]
}
```

Response:

```json
{
  "ok": true,
  "run_id": "run-20260625-120000",
  "accepted": 1
}
```

## POST /api/insights

更新洞察人和 wiki 链接。

Request:

```json
{
  "paper_id": "fresh-edge-agent-paper",
  "insight_person": "Codex",
  "wiki_url": "https://example.com/wiki/fresh-edge-agent-paper"
}
```

Response:

```json
{
  "ok": true,
  "paper_id": "fresh-edge-agent-paper"
}
```
