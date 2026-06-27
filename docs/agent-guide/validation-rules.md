# Agent Validation Rules

这些规则给主 agent 和调研子 agent 使用。任何违反规则的内容都不能发布到服务器。

## 硬规则

1. `source_type` 必须是 `学术论文` / `官方技术博客` / `官方产品发布`。
2. 非论文条目只允许大厂官方来源，必须设置 `is_major_vendor_official: true`，且链接必须是官方域名。
3. 官方大厂条目排序优先于普通论文。
4. `paper_url` 必须指向论文原文、权威论文页或官方来源页。
5. 标题、摘要、链接必须对应同一篇论文或同一条官方动态。
6. `date` 必须在当前日期过去 7 天内。
7. `effects` 必须来自论文原文或官方来源；没有报告就写 `未报告`。
8. 非官方博客、新闻、社媒、二手解读不能进入 `research_runs/*.json` 的 `papers[]`。
9. `category` 必须是 `应用` / `框架` / `算法` 之一。
10. `keywords` 必须是 1 到 8 个关键词，中文优先，避免整句。
11. 首页展示字段必须易读：`abstract` 写「这是什么」，`effects` 写「有什么结果」，`mechanism` 写「怎么做到的」。详细技术解释放 wiki。
12. **死链检查**：`paper_url` 必须 HTTP 可访问。validate 时对每个 URL 发 HEAD 请求，404 或不可达的条目不发布；HEAD 不支持时 fallback GET 取状态码；单 URL 超时 5 秒；离线/断网时 warning 跳过并标记「死链未检」，不 fail。
13. **内容匹配抽检**：`is_major_vendor_official=true` 的条目，主 agent publish 前必须 fetch URL 核验页面内容与标题摘要对应。URL 能打开不等于内容对题；标题摘要与页面不符的条目丢弃。可用 `agent/verify_links.py` 辅助。
14. **学校项目顶会门槛**（agent 侧策略，非代码硬校验）：学校项目（无公司 affiliation）必须发表在顶会顶刊：NeurIPS / ICML / ICLR / MobiSys / SenSys / ASPLOS / ACL / CVPR / ICCV / EMNLP / AAAI / IJCAI / TPAMI / TNNLS / ToN。学校项目的纯 arXiv 预印本（非顶会）不收。公司项目 arXiv 或顶会均可。判断 affiliation 命中公司靠调研 agent 读作者机构，不靠代码识别。
15. **排除常见方法无明显创新**（agent 侧策略，非代码硬校验）：纯前缀缓存+投机解码堆砌、普通量化/剪枝、常规 benchmark，除非有显著新意，否则不收。即使中了顶会也不要，或给低分。

## 评分口径参考

6 维的参考区间，质量判断由调研 agent 给分，不是代码硬排。最终排序靠 `score` 体现：

- `score_vendor`（0-25）：大厂官方 20-25；公司项目 15-20；公司+学校合作顶会 10-15；学校顶会 5-10；纯学术无公司 3-8
- `score_contribution`（0-15）：创新度高 12-15；常见方法/工程整合 5-10
- `score_open`（0-10）：有开源仓库/数据集/模型开源 5-10；不开源 0
- 6 维上限：`score_relevance`(30) + `score_vendor`(25) + `score_contribution`(15) + `score_quality`(15) + `score_recency`(5) + `score_open`(10) = 100，`score` = 6 维加总

## 三个方向分类口径

- `应用`：手机、桌面、GUI 自动化、真实任务、安全隐私、具体产品功能或用户场景。
- `框架`：agent runtime、benchmark、训练环境、评测框架、系统架构、数据管线。
- `算法`：强化学习、记忆、蒸馏、不确定性量化、过程奖励、规划、工具调用等方法。

## 允许的论文链接

- arXiv：`https://arxiv.org/abs/...`
- DOI 或出版商论文页
- OpenReview
- ACL Anthology
- ACM Digital Library
- IEEE Xplore
- CVF Open Access
- PMLR
- 会议 / 期刊官方论文页
- 作者或机构提供的论文 PDF 页面，前提是能明确对应标题

## 不允许作为论文

- 厂商博客
- 产品发布
- 新闻稿
- GitHub release
- Reddit / 社媒帖子
- 二次解读文章
- 无法核对标题和摘要的页面

## 主 agent 发布前检查

主 agent 必须运行自动校验：

```powershell
python agent/validate_research_run.py research_runs/<run_id>.json
```

自动校验覆盖：必填字段、`source_type`/`category` 枚举、`date` 7 天窗口、`score`=6 维之和、官方源必须 `is_major_vendor_official=true` + 官方域名白名单、`keywords` 1-8 中文、**`paper_url` HTTP 死链检查**（HEAD 404/不可达 fail，HEAD 不支持 fallback GET，单 URL 超时 5 秒，离线 warning 跳过）。

### 大厂条目内容抽检（半自动）

自动校验只拦死链，拦不住「URL 能开但内容不对题」。主 agent publish 前对每个 `is_major_vendor_official=true` 的条目：

1. fetch 该 URL，读页面内容。
2. 核验页面标题/正文与 run 里的 `title`、`abstract` 对应。
3. 对不上就丢弃该条，不许带病发布。

可用 `agent/verify_links.py` 辅助（fetch 大厂 URL 返回页面摘要供核验）。

### 失败处理

- 不是论文：删除该条。
- 链接不匹配 / 内容对不上题：删除或重新核验。
- 死链：删除或换权威链接。
- 超出一周窗口：删除。
- 字段缺失：要求子 agent 补全。
- 效果缺失：保留时必须写 `未报告`。

不能为了凑够 10 到 20 篇发布不合格内容。
