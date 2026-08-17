# 社区雷达来源扩展 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把社区雷达升级为九类平台级来源覆盖，并在每周发布门和桌面页面中稳定展示。

**Architecture:** `app/community.py` 继续作为来源词表和数据校验的唯一入口；页面从经过校验的 `coverage/items` 动态渲染，不给正式 research run 增加任何社媒字段。测试、发布门、文档和本周 JSON 同步更新，保证下周刷新不能退回旧五来源结构。

**Tech Stack:** Python `unittest`、JSON、服务器渲染 HTML/CSS/JavaScript、现有 `gate_release.py`。

---

### Task 1: 扩展社区来源契约

**Files:**
- Modify: `tests/test_community.py`
- Modify: `app/community.py`
- Modify: `tests/test_gate_release.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_community.py` 的合法 payload 中使用完整来源集：

```python
COMMUNITY_SOURCES = (
    "X", "Bluesky", "Reddit", "Hacker News", "Mastodon",
    "GitHub Discussions", "Hugging Face", "YouTube / Bilibili", "厂商论坛",
)

"coverage": [
    {"source": source, "status": "no_match", "note": "窗口内已完成检索"}
    for source in COMMUNITY_SOURCES
]
```

并增加断言：`validate_community()` 返回的 coverage 来源集合等于上述九类。

- [ ] **Step 2: 运行测试确认旧契约失败**

Run: `python -m unittest tests.test_community -v`

Expected: FAIL，错误说明 `Bluesky` 等来源不在允许词表中。

- [ ] **Step 3: 最小实现新词表**

在 `app/community.py` 中把 `SOURCES` 改为：

```python
SOURCES = (
    "X", "Bluesky", "Reddit", "Hacker News", "Mastodon",
    "GitHub Discussions", "Hugging Face", "YouTube / Bilibili", "厂商论坛",
)
```

同步把 `tests/test_gate_release.py` 的合法 coverage 夹具改为从 `app.community.SOURCES` 构建，避免测试复制一份会漂移的词表。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest tests.test_community tests.test_gate_release -v`

Expected: PASS。

- [ ] **Step 5: 提交契约修改**

检查 `.agent/config.yml`；文件不存在，按默认 `auto_commit: true` 执行：

```powershell
git add -- app/community.py tests/test_community.py tests/test_gate_release.py
git commit -m "feat: expand community radar source coverage"
```

### Task 2: 更新桌面页面与流程文档

**Files:**
- Modify: `app/page.py`
- Modify: `tests/test_page_recommendations.py`
- Modify: `AGENTS.md`
- Modify: `.agents/skills/edge-agent-research-pipeline/SKILL.md`
- Modify: `docs/harness.md`
- Modify: `docs/agent-guide/main-agent-workflow.md`
- Modify: `docs/agent-guide/research-prompt.md`
- Modify: `docs/agent-guide/validation-rules.md`
- Modify: `docs/agent-guide/release-check.md`
- Modify: `docs/site/api-contract.md`
- Modify: `docs/site/display-spec.md`

- [ ] **Step 1: 写失败的页面契约测试**

在 `tests/test_page_recommendations.py` 中增加：

```python
def test_community_radar_names_expanded_public_sources(self):
    for label in ("Bluesky", "Mastodon", "GitHub Discussions", "Hugging Face", "YouTube", "Bilibili"):
        self.assertIn(label, INDEX_HTML)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest tests.test_page_recommendations -v`

Expected: FAIL，旧板块说明没有列出新增来源。

- [ ] **Step 3: 更新页面最小实现**

把 `app/page.py` 的板块说明改为明确列出 Bluesky、Reddit、HN、Mastodon、GitHub Discussions、Hugging Face 与视频来源；将 `.community-coverage` 从固定五列改为：

```css
.community-coverage{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));margin:0 0 12px;border:1px solid var(--rule);background:var(--panel)}
```

- [ ] **Step 4: 同步仓库流程文字**

在列出的流程文档中统一写明九类来源、公开可访问和日期核验规则、社区与正式周报隔离规则；不改变正式 run 的来源契约。

- [ ] **Step 5: 运行页面测试**

Run: `python -m unittest tests.test_page_recommendations -v`

Expected: PASS。

- [ ] **Step 6: 提交页面与文档**

检查 `.agent/config.yml`；文件不存在，按默认 `auto_commit: true` 执行：

```powershell
git add -- app/page.py tests/test_page_recommendations.py AGENTS.md .agents/skills/edge-agent-research-pipeline/SKILL.md docs/harness.md docs/agent-guide/main-agent-workflow.md docs/agent-guide/research-prompt.md docs/agent-guide/validation-rules.md docs/agent-guide/release-check.md docs/site/api-contract.md docs/site/display-spec.md
git commit -m "feat: show platform-level community coverage"
```

### Task 3: 写入本周数据并完成发布验证

**Files:**
- Modify: `data/community_radar.json`
- Modify: `data/weekly_summary.json`
- Modify: `data/.last_run`
- Create: `research_runs/run-20260817-*.json`
- Create: `data/weeks/2026-08-12.json`

- [ ] **Step 1: 写本周社区 JSON**

窗口固定为 `2026-08-11..2026-08-17`，用户阅读重点为 `2026-08-12..2026-08-17`。九类 coverage 全部填写状态和中文说明；只有日期、原帖直达 URL 与主题都能核验的内容才进入 items。

- [ ] **Step 2: 验证社区数据**

Run: `python -m unittest tests.test_community -v`

Expected: PASS；`validate_community(data, today=date(2026, 8, 17))` 返回九类 coverage。

- [ ] **Step 3: 构建并跑机械门**

Run:

```powershell
python app/build.py
python tests/test_research_pipeline.py
python tests/test_build.py
python app/gates/gate_all.py
```

Expected: 所有命令退出码均为 0，`gate_release` 不报告 coverage、快照或社媒污染错误。

- [ ] **Step 4: 发布与桌面浏览器验收**

发布正式 run，归档本周快照，部署 GitHub Pages；硬刷新线上桌面页，检查推荐、完整资料库、九类覆盖卡、社区来源筛选、外链和浏览器 console。

- [ ] **Step 5: 提交本周发布产物**

检查 `.agent/config.yml`；文件不存在，按默认 `auto_commit: true`，只暂存本次生成和修改的受版本控制文件，不包含用户已有的 `research_runs/livefix.html`、`research_runs/live0807.html`、`tmp/` 或 `data/weeks/2026-08-05.json` 变更：

```powershell
git add -- data/community_radar.json data/weekly_summary.json data/.last_run data/weeks
git commit -m "content: publish weekly edge AI radar for 2026-08-17"
```

最后 `git push origin master`，并再次打开线上页面核对部署结果。
