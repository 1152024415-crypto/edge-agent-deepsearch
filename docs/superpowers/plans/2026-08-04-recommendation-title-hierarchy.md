# Recommendation Chinese Title Hierarchy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让桌面端推荐卡片按照“中文项目名 → 中文介绍 → 关键词 → 推荐理由 → 英文原标题”展示，并在后续每周发布中机械阻止缺少中文项目名的推荐。

**Architecture:** 在 research run 契约中新增 `title_zh`，自动采集阶段留空，只有主 agent 策展推荐时填写。字段经过校验、SQLite、API、静态构建进入页面；research run 校验与真实构建发布门共同防止缺失或把摘要冒充名称。

**Tech Stack:** Python 3、SQLite、原生 HTML/CSS/JavaScript、unittest、GitHub Pages 静态构建。

---

### Task 1: Research run 中文项目名契约

**Files:**
- Modify: `tests/test_research_pipeline.py`
- Modify: `agent/research_run.py`
- Modify: `agent/build_run_week.py`
- Modify: `agent/build_run_from_arxiv.py`

- [ ] **Step 1: 写推荐缺少 `title_zh` 的失败测试**

在 `valid_paper()` 默认数据加入 `title_zh: ""`，新增测试：

```python
def test_recommended_paper_requires_short_chinese_title(self):
    path = write_json(run_payload(valid_paper(
        recommendation="推荐",
        recommendation_reason="端侧收益明确，而且给出了真实设备上的验证结果。",
        title_zh="",
    )))
    with self.assertRaises(ValidationError) as ctx:
        load_and_validate(path, check_links=False, check_arxiv_dates=False)
    self.assertIn("title_zh", str(ctx.exception))

def test_rejects_abstract_used_as_chinese_title(self):
    abstract = "这项工作让端侧智能体在手机本地完成规划与执行。"
    path = write_json(run_payload(valid_paper(
        abstract=abstract,
        title_zh=abstract,
        recommendation="推荐",
        recommendation_reason="端侧收益明确，而且给出了真实设备上的验证结果。",
    )))
    with self.assertRaises(ValidationError) as ctx:
        load_and_validate(path, check_links=False, check_arxiv_dates=False)
    self.assertIn("title_zh", str(ctx.exception))
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python tests/test_research_pipeline.py`

Expected: 新测试失败，因为当前规范化结果没有校验 `title_zh`。

- [ ] **Step 3: 实现最小校验和规范化**

在 `agent/research_run.py` 中读取 `title_zh`；非空时要求至少 2 个 CJK 字符、长度不超过 40、无内部占位词且不等于 `abstract`。推荐条目必须非空，并在规范化 paper 中返回该字段：

```python
title_zh = text_value(paper.get("title_zh"))
if title_zh:
    if len(CJK_RE.findall(title_zh)) < 2:
        raise ValidationError(f"{paper_id}: title_zh must contain at least 2 Chinese characters")
    if INTERNAL_PLACEHOLDER_RE.search(title_zh):
        raise ValidationError(f"{paper_id}: title_zh 含内部占位/流程标记")
    if len(title_zh) > 40:
        raise ValidationError(f"{paper_id}: title_zh must be at most 40 characters")
    if title_zh == abstract:
        raise ValidationError(f"{paper_id}: title_zh must be a project name, not the abstract")
if recommendation == "推荐" and not title_zh:
    raise ValidationError(f"{paper_id}: title_zh is required when recommendation=推荐")
```

让两个自动转换脚本显式输出：

```python
"title_zh": "",
"recommendation": "纳入",
"recommendation_reason": "",
```

- [ ] **Step 4: 运行测试并确认 GREEN**

Run: `python tests/test_research_pipeline.py`

Expected: 全部通过。

- [ ] **Step 5: 提交（`.agent/config.yml` 缺失，`auto_commit` 默认为 true）**

```powershell
git add tests/test_research_pipeline.py agent/research_run.py agent/build_run_week.py agent/build_run_from_arxiv.py
git commit -m "feat: require Chinese titles for recommendations"
```

### Task 2: SQLite 与 API 字段贯通

**Files:**
- Modify: `tests/test_research_pipeline.py`
- Modify: `app/storage.py`

- [ ] **Step 1: 写存储与旧库迁移失败测试**

扩展现有 API 往返测试，断言：

```python
title_zh = "端侧记忆管理框架"
paper = valid_paper(title_zh=title_zh)
storage.upsert_run(run_payload(paper))
self.assertEqual(storage.list_papers()[0]["title_zh"], title_zh)
```

扩展旧数据库迁移测试：删除 `title_zh` 列后重新初始化，断言旧行保留且 `title_zh == ""`。

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python tests/test_research_pipeline.py`

Expected: SQLite 没有 `title_zh` 列或返回结果缺少该字段。

- [ ] **Step 3: 实现列、迁移和 upsert**

在 `app/storage.py` 的 paper 字段、建表、旧库迁移、INSERT 和冲突更新中加入：

```python
title_zh TEXT NOT NULL DEFAULT ''
```

```python
if "title_zh" not in columns:
    conn.execute("ALTER TABLE papers ADD COLUMN title_zh TEXT NOT NULL DEFAULT ''")
```

- [ ] **Step 4: 运行测试并确认 GREEN**

Run: `python tests/test_research_pipeline.py`

Expected: 全部通过，旧行未丢失。

- [ ] **Step 5: 提交（提交前再次检查 `.agent/config.yml`）**

```powershell
git add tests/test_research_pipeline.py app/storage.py
git commit -m "feat: persist recommendation Chinese titles"
```

### Task 3: 推荐卡片三层主信息

**Files:**
- Modify: `tests/test_page_recommendations.py`
- Modify: `app/page.py`

- [ ] **Step 1: 写 DOM 顺序和关键词失败测试**

新增页面测试，截取 `shown.map` 渲染器并断言：

```python
title_pos = renderer.index('class="rec-title"')
summary_pos = renderer.index('class="rec-summary"')
tags_pos = renderer.index('class="rec-tags"')
why_pos = renderer.index('class="rec-why"')
original_pos = renderer.index('class="rec-original"')
self.assertLess(title_pos, summary_pos)
self.assertLess(summary_pos, tags_pos)
self.assertLess(tags_pos, why_pos)
self.assertLess(why_pos, original_pos)
self.assertIn("p.title_zh", renderer)
self.assertIn("关键词", renderer)
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python tests/test_page_recommendations.py`

Expected: 缺少 `.rec-title` 和 `.rec-tags`。

- [ ] **Step 3: 实现卡片名称、介绍和关键词层级**

在 `renderRecommendations()` 中生成关键词 chip，并按固定顺序渲染：

```javascript
const titleZh=(p.title_zh||'').trim();
const summary=(p.abstract||'').trim();
const tags=(p.tags||[]).map(t=>`<span class="rec-tag">${escapeHtml(val(t))}</span>`).join('');
```

```html
<span class="rec-title">${escapeHtml(titleZh)}</span>
<span class="rec-summary">${escapeHtml(summary)}</span>
<span class="rec-tags"><b>关键词</b>${tags}</span>
<span class="rec-why"><b>值得优先看：</b>${escapeHtml(reason)}</span>
<span class="rec-original">原标题：${escapeHtml(p.title)}</span>
```

CSS 让 `.rec-title` 成为卡片唯一主标题，`.rec-summary` 使用正文层级，关键词使用紧凑 chip；hover 跟随主标题，不再强调摘要。

- [ ] **Step 4: 运行页面测试并确认 GREEN**

Run: `python tests/test_page_recommendations.py`

Expected: 全部通过。

- [ ] **Step 5: 提交（提交前再次检查 `.agent/config.yml`）**

```powershell
git add tests/test_page_recommendations.py app/page.py
git commit -m "feat: show project names before recommendation summaries"
```

### Task 4: 构建发布门防回归

**Files:**
- Modify: `tests/test_gate_release.py`
- Modify: `tests/test_build.py`
- Modify: `app/gates/gate_release.py`

- [ ] **Step 1: 写真实构建门失败测试**

给有效推荐 fixture 增加 `title_zh`，新增缺失名称和名称等于摘要两个失败用例：

```python
def test_fail_when_recommendation_title_zh_is_missing(self):
    papers = [valid_recommendation(title_zh="")]
    errs = check_papers_contract(build_site(papers))
    self.assertTrue(any("title_zh" in error for error in errs), errs)

def test_fail_when_title_zh_repeats_abstract(self):
    abstract = "这是一条可以直接阅读的中文项目介绍。"
    papers = [valid_recommendation(title_zh=abstract, abstract=abstract)]
    errs = check_papers_contract(build_site(papers))
    self.assertTrue(any("项目名" in error for error in errs), errs)
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python tests/test_gate_release.py`

Expected: 新用例失败，因为发布门尚未检查 `title_zh`。

- [ ] **Step 3: 实现真实产物检查**

在 `gate_release.py` 的推荐循环中检查：

```python
title_zh = str(paper.get("title_zh") or "").strip()
if cjk_count(title_zh) < 2 or len(title_zh) > 40:
    _err(errors, f"{pid}: title_zh 缺失或不是简短中文项目名")
if has_internal_marker(title_zh):
    _err(errors, f"{pid}: title_zh 含内部占位/流程标记")
if title_zh == abstract.strip():
    _err(errors, f"{pid}: title_zh 不能直接复用项目介绍")
```

- [ ] **Step 4: 运行发布门与构建测试并确认 GREEN**

Run: `python tests/test_gate_release.py`

Run: `python tests/test_build.py`

Expected: 两个测试文件全部通过。

- [ ] **Step 5: 提交（提交前再次检查 `.agent/config.yml`）**

```powershell
git add tests/test_gate_release.py tests/test_build.py app/gates/gate_release.py
git commit -m "test: block recommendations without Chinese project names"
```

### Task 5: 强入口文档与当前周策展数据

**Files:**
- Modify: `AGENTS.md`
- Modify: `.agents/skills/edge-agent-research-pipeline/SKILL.md`
- Modify: `docs/harness.md`
- Modify: `docs/agent-guide/main-agent-workflow.md`
- Modify: `docs/agent-guide/research-prompt.md`
- Modify: `docs/agent-guide/output-contract.md`
- Modify: `docs/agent-guide/validation-rules.md`
- Modify: `docs/site/api-contract.md`
- Modify: `research_runs/run-20260804-104118.json`

- [ ] **Step 1: 同步流程契约**

所有强入口统一写明：自动汇集 `title_zh=""`；主 agent 推荐时必须填写简短中文项目名；项目名不能是摘要；页面层级为名称、介绍、关键词、理由、原标题。

- [ ] **Step 2: 给当前 15 条推荐补写名称**

逐条读取当前推荐来源和摘要，为每条写 40 字以内、至少 2 个中文字符的 `title_zh`，例如：

```json
{
  "title": "ResKV: Reconstructing Omitted Attention Contributions for Fixed-Budget KV Cache Compression",
  "title_zh": "ResKV 固定预算 KV 缓存重建",
  "abstract": "ResKV 在固定 KV 预算里保留一块精确主缓存……"
}
```

- [ ] **Step 3: 校验并发布当前 run**

Run: `python agent/validate_research_run.py research_runs/run-20260804-104118.json`

Expected: 校验成功；网络不可用仅允许现有验证器定义的 warning，不能有内容失败。

Run: `python agent/publish_results.py research_runs/run-20260804-104118.json --server http://127.0.0.1:8001`

Expected: `ok=true`，accepted 数与当前完整收录一致，自动部署在 release gate 通过后触发。

- [ ] **Step 4: 提交文档（当前 run 默认不提交；提交前再次检查 `.agent/config.yml`）**

```powershell
git add AGENTS.md .agents/skills/edge-agent-research-pipeline/SKILL.md docs/harness.md docs/agent-guide/main-agent-workflow.md docs/agent-guide/research-prompt.md docs/agent-guide/output-contract.md docs/agent-guide/validation-rules.md docs/site/api-contract.md
git commit -m "docs: require Chinese project names in weekly curation"
```

### Task 6: 合并、部署与线上验收

**Files:**
- Verify: `site/index.html`
- Verify: GitHub Pages production URL

- [ ] **Step 1: 运行完整项目验证**

Run: `python tests/test_research_pipeline.py`

Run: `python tests/test_build.py`

Run: `python app/gates/gate_all.py`

Run: `git diff --check`

Expected: 所有测试和门禁通过，无 whitespace error。

- [ ] **Step 2: 合并功能分支并推送 master**

```powershell
git merge --ff-only codex/project-title-hierarchy
git push origin master
```

- [ ] **Step 3: 检查真实线上页面数据**

从 GitHub Pages 加随机查询参数绕过缓存，解析 `window.__PAPERS__`，断言：

- 完整收录数和推荐数未改变。
- 每条推荐都有合格 `title_zh`、`abstract`、`tags`、`recommendation_reason`。
- 页面模板中 `.rec-title` 位于 `.rec-summary` 和 `.rec-tags` 之前。
- 推荐详情链接、原文链接、notes/SNN/WAIC 链接返回 HTTP 200。

- [ ] **Step 4: 清理临时工作区**

在功能分支已合并且工作区干净后运行：

```powershell
git worktree remove C:\Users\11520\.config\superpowers\worktrees\edge_agent\project-title-hierarchy
git branch -d codex/project-title-hierarchy
```
