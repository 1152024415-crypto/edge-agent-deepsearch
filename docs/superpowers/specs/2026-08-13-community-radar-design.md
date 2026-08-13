# 社区雷达设计

## 目标

在不降低正式周报可信度的前提下，引入 X、Reddit、Hacker News、厂商/开源社区论坛等早期信号。社区内容只负责“发现”，不能直接成为正式论文、官方动态或 Agent 推荐。

## 信息架构

桌面首页顺序固定为：本周推荐 → 本周判断 → 完整资料库 → 社区雷达 → GitHub 待核验线索。

“社区雷达”和 GitHub Trending 同属发现层，但分开显示：社区雷达关注讨论、实测、发布预告和开发者反馈；GitHub Trending 关注新仓库。两者都不能混入正式收录数量。

## 数据契约

新增独立编辑产物 `data/community_radar.json`：

```json
{
  "window": {"start": "2026-08-07", "end": "2026-08-13"},
  "coverage": [
    {"source": "X", "status": "limited", "note": "仅使用公开索引结果，不登录抓取"}
  ],
  "items": [
    {
      "id": "stable-id",
      "source": "X",
      "author": "账号或社区名",
      "url": "https://x.com/...",
      "published_at": "2026-08-12T10:00:00Z",
      "title_zh": "中文标题",
      "summary_zh": "两句以内中文总结。",
      "why_it_matters": "为什么端侧 AI 读者值得注意。",
      "device_scope": "手机",
      "topic": "Agent",
      "verification": "仅线索",
      "evidence_url": ""
    }
  ]
}
```

允许来源：`X`、`Reddit`、`Hacker News`、`厂商论坛`、`开发者论坛`。`device_scope` 只用 `手机`、`PC`、`其他端侧`、`通用技术`；`verification` 只用 `仅线索`、`已回链原始材料`、`已进入正式周报`。每条必须有原帖直达 URL、可核验时间、中文标题/总结/价值判断。登录墙或无法确认日期的内容不收。

## 搜集方法

- X：只用公开网页搜索索引发现原帖，能打开原帖或可靠获取原帖元信息才展示；不要求用户登录，不使用不安全账号环境。
- Hacker News：公开 Algolia/API 或帖子直达页。
- Reddit：公开帖子页、RSS/JSON 可访问时采集；访问受限则在 coverage 标注，不伪装完整。
- 厂商/开发者论坛：优先 Discourse JSON/RSS 和主题直达页，如 NVIDIA Developer Forums、PyTorch Forums、Hugging Face Discussions。

每周按手机 Agent → PC Agent → 端侧模型/Infra → 其他设备排序，热度只作同级辅助。社区线索如找到官方发布、论文或合格大项目 release，应在下一步核验后进入正式周报；页面保留状态和 evidence URL，避免重复判断。

## 页面

社区雷达默认显示 8 条，支持来源和设备快速筛选，并可展开全部。每条采用单行编辑结构：来源/时间/设备/核验状态 → 中文标题 → 中文总结 → 值得注意的原因 → 作者和原帖链接。空数据时显示“本周没有完成核验的社区线索”及 coverage，而不是隐藏板块。

## 归档、接口与失败处理

- `GET /api/community` 读取当前 `data/community_radar.json`，缺失或格式错误时返回空 items 和覆盖说明。
- 静态构建内联 `window.__COMMUNITY__`，动态页面优先读内联数据、不存在时请求 API。
- `data/weeks/<label>.json` 一并冻结 community，历史周不读取当前社区数据。
- 发布门禁检查字段、七日窗口、URL、中文可读性、来源/状态枚举、板块顺序和静态内联契约；X 覆盖为 limited 可以发布，但必须有说明。

## 非目标

- 不把互动量当成可信度或推荐分。
- 不自动把社区帖子升级为正式收录。
- 不要求 X 登录、付费 API 或用户账号。
- 不构建通用社交媒体爬虫；每周由 Agent 使用公开入口采集并编辑 JSON。
