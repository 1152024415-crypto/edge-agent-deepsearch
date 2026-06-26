# Site API Contract

服务器负责接收主 agent 发布的调研结果，并给展示页提供最新数据。

## GET /api/papers

Returns papers from the latest accepted research run only. Historical runs may stay in SQLite for audit/debugging, but the display page must not mix old runs into the current radar.

返回当前服务器中可展示的论文/官方动态列表。官方大厂条目固定排序优先；同优先级内默认按分数降序。
前端按 `category` 分成 `应用` / `框架` / `算法` 三个 tab；每条内容的 `keywords` 用小标签展示。

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
      "abstract": "paper abstract",
      "effects": "reported effect",
      "mechanism": "how it works",
      "paper_url": "https://arxiv.org/abs/2606.12345",
      "date": "2026-06-24",
      "score": 92,
      "score_reason": "主题直接命中端侧 agent，报告了明确 benchmark 提升。",
      "source_type": "学术论文",
      "is_major_vendor_official": false,
      "category": "应用",
      "keywords": ["GUI智能体", "端侧部署", "评测基准"],
      "insight_person": "",
      "wiki_url": "",
      "authors": "",
      "vendors": "",
      "venue": "",
      "recommendation": "纳入",
      "updated_at": "2026-06-25T04:00:00+00:00"
    }
  ]
}
```

## POST /api/research-runs

主 agent 用 `agent/publish_results.py` 调用。服务器会再次校验 payload。

Request:

```json
{
  "run_id": "run-20260625-120000",
  "generated_at": "2026-06-25T12:00:00+08:00",
  "papers": [
    {
      "id": "fresh-edge-agent-paper",
      "title": "Fresh Edge Agent Paper",
      "abstract": "paper abstract",
      "effects": "reported effect",
      "mechanism": "how it works",
      "paper_url": "https://arxiv.org/abs/2606.12345",
      "date": "2026-06-24",
      "score": 92,
      "score_reason": "主题直接命中端侧 agent，报告了明确 benchmark 提升。",
      "source_type": "学术论文",
      "is_major_vendor_official": false,
      "category": "应用",
      "keywords": ["GUI智能体", "端侧部署", "评测基准"],
      "insight_person": "",
      "wiki_url": ""
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
