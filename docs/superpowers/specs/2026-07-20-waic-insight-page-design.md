# WAIC 洞察页 设计 spec

**日期**: 2026-07-20
**目标**: 在端侧 AI 雷达站新增一个 WAIC 洞察页（WAIC 2026 专项调研报告），架构完全复用 SNN 洞察页模式。

## 目标与范围

`site/waic.html`——一个静态精选报告页，复用 SNN 页模式（左侧章节 TOC + 右侧 marked.js+KaTeX 渲染，同 RADAR 美学）。内容是 WAIC 2026（世界人工智能大会，2026-07-16/17 上海开幕，进行中）专项调研报告，由我调研产出（无源 md）。

**在范围内**：
- 一份 `data/waic-insight.md`（8 节 WAIC 2026 专项报告）
- `site/waic.html` + `site/waic/WAIC-insight.md`（静态产物）
- `app/waic_page.py`（= snn_page 模板，改标题/fetch 路径）
- `agent/build_waic.py`（= build_snn，源 data/waic-insight.md）
- index.html 加「WAIC」nav 链接
- gate_release 加 waic.html 存在检查 + 测试
- 我自己调研：WAIC 2026 新闻 + 厂商发布，WebFetch 权威源核实

**不在范围内**：
- 不覆盖 WAIC 历史脉络（2018 创办等）——用户选了「WAIC 2026 专项」
- 不做动态/数据驱动（静态精选，手动刷新，同 SNN）
- 不重写 SNN 页

## 架构（复用 SNN 页）

复用 `app/snn_page.py` + `agent/build_snn.py` 模式，区别仅标题 + fetch 路径：

```
data/waic-insight.md   (主 agent 调研产出)
        │ agent/build_waic.py
        ├→ site/waic/WAIC-insight.md   (拷贝，供 fetch)
        └→ site/waic.html              (app/waic_page.py 模板渲染)
```

页面结构（同 SNN）：左侧粘性侧栏 TOC（从渲染后 h2 自动生成 + IntersectionObserver 当前节高亮）+ 右侧 marked.js 渲染 + KaTeX auto-render（WAIC 报告含能耗/参数等数字，公式少但保留 KaTeX 一致）+ 顶部 `RADAR · WAIC 洞察` + `← 返回雷达` + 扫描动画条。

## 内容结构（data/waic-insight.md，8 节 WAIC 2026 专项）

1. **WAIC 2026 概览** — 时间（07-16/17 开幕·进行中）、地点（上海）、规格（习近平出席开幕式+主旨讲话+人工智能全球治理高级别会议）、主题
2. **主线：Agent 爆发 + 物理 AI** — 「AI 长出身体」叙事、AI 终端争夺战、印奇「行业三道必答题」
3. **国内厂商发布** — 华为昇腾950超节点真机、百度搭子+秒哒3.5、腾讯智能体、阿里秒悟团队版+魔法原子×速卖通、阶跃星辰 STEPX Neo+期智研究院、小米/字节等
4. **镇馆之宝** — 阶跃 STEPX Neo、百度搭子、对话式蛋白质设计智能体、智元机器人 等
5. **AI 终端争夺战** — 模型厂下场造机（阶跃 STEPX Neo 等，连雷达之前那条阶跃星辰 highlight）
6. **端侧/边缘相关信号** — 昇腾950 硬件、AI 终端、agent 手机（连雷达端侧主线）
7. **治理与开源** — 习近平主旨讲话、中国开源战略、全球治理高级别会议
8. **产业信号** — 「需求爆炸」、DAA 2030 全球 22 亿、资本/估值

## 调研与来源规则（硬）

- Google News RSS 已拿线索（见探索阶段）；**WebFetch 权威源核实事实**：新华网/央视网/财新/财联社/上观新闻/科学网/厂商官网。
- 每个发布/事实带**权威媒体直链**（不用 google news wrapper，吸取上轮阶跃星辰链接教训——wrapper 有「重新導向通知」中间页+长串易抄错）。优先厂商官方域名（华为 huawei.com / 百度 baidu.com / 阿里 alibaba.com / 腾讯 tencent.com / 阶跃星辰 stepfun.com）；官方域名取不到的用权威媒体直链（财新/财联社/上观/新华）。
- 不编造内容、不编造 URL。WebFetch 404 丢弃该条。
- WAIC 是公开事件，无内部内容需去化（不像 SNN 的华为内部图）。

## 构建 / 部署

- `agent/build_waic.py`：读 `data/waic-insight.md` → 拷到 `site/waic/WAIC-insight.md` → 用 `app/waic_page.py` 的 `WAIC_HTML` 模板渲染 `site/waic.html`。env 覆盖 SNN_SRC/SNN_SITE 对应 WAIC_SRC/WAIC_SITE（或复用同名 env）。
- index.html nav：在「SNN 洞察」旁加「WAIC ↗ → waic.html」（page.py 改 + build.py mirror re.sub 重写）。
- 部署：gh-pages worktree push（同 SNN/notes 流程）。

## 测试 / 验证

- `gate_release.py` 加 `check_waic_page`：`site/waic.html` 存在（否则 nav 404）。+ 1 测试（同 snn）。
- `tests/test_build_waic.py`：build_waic 产出 waic.html + waic/md（同 test_build_snn 模式）。
- chrome 实测：打开 waic.html → markdown 渲染（h2 ≥8）→ TOC 自动生成 → KaTeX → 无坏链 → 返回雷达 → nav 从 index 点入。

## 文件清单

- 新建 `data/waic-insight.md`（调研产出，8 节）
- 新建 `app/waic_page.py`（= snn_page 模板，标题/fetch 改 WAIC）
- 新建 `agent/build_waic.py`（= build_snn，源 data/waic-insight.md）
- 改 `app/page.py`（index nav 加 WAIC 链接）
- 改 `app/build.py`（render_page re.sub 重写 waic.html 链接）
- 改 `app/gates/gate_release.py` + `tests/test_gate_release.py`（waic.html 检查 + 测试）
- 新建 `tests/test_build_waic.py`
- 部署产物：`site/waic.html` + `site/waic/WAIC-insight.md`

## 非目标 / 取舍

- 不做搜索/筛选交互（静态报告，YAGNI）。
- 不覆盖 WAIC 历史（用户选 2026 专项）。
- 不做 WAIC 论文 sweep（WAIC 是会议/展会，发布是产品/政策，不是 arxiv 论文；厂商发布用新闻+官网核实）。
- 图片：WAIC 公开报道图若需引用用权威媒体图，v1 优先纯文本+表格+链接，不嵌外站图（避免坏链）。
