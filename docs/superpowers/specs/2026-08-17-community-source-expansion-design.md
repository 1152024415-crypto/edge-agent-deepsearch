# 社区雷达来源扩展设计

## 目标

把社区雷达从五个宽泛来源桶扩展为可审计的平台级来源覆盖，补足正式周报较难捕捉的真实设备反馈、项目苗头和发布演示。正式周报仍只接受符合一手来源契约的内容；社区条目不能直接抬升为正式收录。

## 来源范围

每周固定检查下列来源，并逐一展示 `found`、`no_match`、`limited` 或 `unavailable`：

- X：只保留无需登录即可打开、且能核验发布时间的公开原帖；受限时如实标记。
- Bluesky：使用公开搜索或作者公开 feed，优先研究人员与项目账号。
- Reddit：重点检查 LocalLLaMA、LocalLLM、MachineLearning、Android 等社区。
- Hacker News：通过官方 Firebase API或 Algolia 检索 Show HN、产品和开源项目。
- Mastodon：检查公开账号与 `#OnDeviceAI`、`#EdgeAI`、`#LocalLLM` 标签。
- GitHub Discussions：检查白名单大项目和高价值端侧项目的讨论、公告与路线图。
- Hugging Face：检查 Discussions、Models 与 Spaces 的本周新增或更新，并区分模型卡证据和复制模板噪声。
- YouTube / Bilibili：只收官方频道或可回链一手项目的演示视频，并核验发布日期。
- 厂商论坛：保留 NVIDIA、Qualcomm、Arm 等论坛作为独立来源，不与 GitHub/HF 混为一类。

## 数据契约

`data/community_radar.json` 继续保持独立于 research run。`coverage` 的规范来源改为以上九类，每类必须有状态和中文说明；`items[].source` 必须命中同一词表。条目仍必须具备中文名称、中文总结、价值判断、设备范围、核验状态、原帖直达 URL 和窗口内发布时间。

其中 `Hugging Face` 同时覆盖 Discussions、Models 与 Spaces，`YouTube / Bilibili` 作为视频来源合并展示，避免来源卡数量过多。具体子来源写入条目的 `author`、`topic` 或 coverage 说明。

## 页面呈现

社区雷达保持在“完整资料库”之后、“GitHub 待核验线索”之前。覆盖卡从固定五列改为自适应网格，桌面宽度下可完整显示九类平台；来源筛选由实际条目动态生成。板块说明直接列出新增平台，避免用户把“没有条目”误解成“没有检索”。

条目仍按手机 > PC > 其他端侧 > 通用技术排序。手机和 PC 的真实 Agent 闭环、端侧模型实测、工具调用与离线运行优先展示；普通讨论或无法回链的转述不收。

## 错误处理与发布门

- 平台无法访问不允许省略，必须写 `limited` 或 `unavailable` 及原因。
- 日期无法核验、登录墙不可绕过、只有二手转述的内容不进入 items。
- X、Reddit、Bluesky 等讨论链接不得出现在正式 papers 的 `paper_url`。
- `gate_release` 继续校验完整 coverage、静态快照一致性和社区/正式层隔离。
- 历史周继续冻结当周 community 快照，不随本周来源词表回写。

## 验证

先增加失败测试，证明旧五来源契约不能接受新的完整来源集；再更新社区校验、空状态、测试夹具、发布门和页面文案。最后运行社区单测、研究 pipeline、静态构建和 release gate，并在部署后用桌面浏览器实点来源筛选、讨论链接和一手材料链接。
