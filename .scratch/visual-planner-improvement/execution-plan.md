# 配图 MVP 执行计划

Status: 本轮局部功能完成 — 03/EPIC02 的限定本地结果已由主控接受，不表示生产 E2E、稳定质量认证或整个项目完成。

本计划覆盖现有 n8n 配图增量；Codex-native 迁移属于独立任务。01「共同视觉规划」保留为已完成的历史切片，不改其原文。02/04/05/03 在本轮限定范围已交付，已知非阻塞项保留。恢复快照和 docs 收尾后停止，不扩框架或新测试。

## 历史状态与证据边界

01 可复用共享 Planner、下载/生成、Markdown 交付路径。最近历史验收曾观察 draft `a1bcbe17-0d47-45a3-bf0f-4d0a32912183`、active `96042bba-9621-4571-98b6-976dc819c4fc`、92 节点、未发布；实施前必须重新读取线上权威工作流和活动/草稿关系。历史事实不代表当前状态。

执行 874：News 计划 1 source + 1 generated cover。执行 876：source 下载、上传、解码并进入双语 Markdown。执行 875 是缩减且漏掉编辑意见的无效回放输入，不作为原 856 行为证据。执行 877 才是校正输入下的单次观察：57 个候选、79 字符 note，结果 3 generated / 0 source；未实际生图，模型内因 UNKNOWN。不得据此判定程序失败或宣称 Deep 社区选图解决。禁止将测试样本专用答案写入提示或生产路径。

2026-10-10 executions 883/884 add bounded evidence for 02. 883 reused 879–882, retained 75 candidates / 19 materials / 79-character editor note / three read descriptions, and planned 1 source plus 3 generated tasks. 884 delivered only the selected source screenshot through the existing native asset and bilingual Markdown path. The screenshot is a community repost of an official Haiku 5.5 release post. It is release background, not a community task benchmark or pricing comparison. The three generated items remain plans; no new generated image was created. Community task-test image breadth and generated-image delivery remain unverified. The controller accepted Issue 02 within its bounded scope. The source follows a pricing paragraph, and its caption notes that tiered prices are absent; the controller found this less readable. Record this as a non-blocking Issue 03 observation. Do not reopen Issue 02 for it. See [02 issue evidence](issues/02-community-image-sourcing.md).

## 共用交付与验证入口

最高现有 seam 为保存稿件及已授权材料到配图后的双语 Markdown。保留稿、素材和凭据边界；局部验证不触发邮件或生产发布。只复用必要回执，遇新错误记录首个完整错误、提出一个有证据的假设并做一次最小修正；第二次尝试必须有新证据。不得静默换模型、provider 或 harness。

人工读最终双语 Markdown 是本计划最高的内容交付检查；不要求为文章写专用答案，不设图片数或字数配额，不进行程序创作审核。所有成功结论需基于实际执行结果，而非配置意图或节点状态。

## 建议顺序

### 02 — 主动取材与混合配图（局部通过，仍开放）

**用户看到的成果：** 默认源图与生成图混搭并主动寻找贴题源图，Deep 不默认全生成；按文章需要组合并交付双语 Markdown。没有合适源图时可不含 source 并记录，或收窄表达，不硬凑。

**最小触点：** 在 01 已有规划入口复用知乎 API/CLI、Browser Pilot、用户提供明确 URL 时的微信正文取图能力，以及已有图片候选结构。候选旁语境随素材传递；只有实际取得图片或从实际图像读取的可靠视觉摘要才视作理解图片，旧 prompt 仅辅助创作意图。不得以 URL 或文字标签假装看过图。结合 [Article Illustrator](../../docs/research/ai-daily-visual-reference-kb-2026-10-10.md) 的内容结构/视觉意图先行方法与 qiaomu-ppt 的 source/生成用途区分，转写为 Planner 的短指导；不照搬逐章配额、shotlist 或评分流程。无授权或能力缺失时明确 BLOCKED。

**局部成功 / 必要失败：** 用一个确有需要且已授权的真实 Deep 样本，观察主动取材与规划到双语 Markdown；只给模型真实任务和完整材料，不提示某张图必须被选中，不强制图片数或每篇必须有 source。若有贴题 source 且作者要求仍未采用，记录原因，该效果仍标为未验证/未解决；不得以下载通路或旧 Deep 生成输出替代。工具不可用或未授权时报告 BLOCKED 并确认保存稿仍在。

**停止点：** 需要新视觉服务、扩张补查预算、未经授权登录或静默切换模型/provider/harness；或图片失败会丢正文时停止受影响路线。

**当前状态：** 02 在本票范围局部通过。883/884 证明一项相关 source 已进入双语 Markdown，且源图上下文交接保留。社区任务实测图的广度和三项 generated 计划的实际生成/交付仍未证明。价格段后的 source 插入与 caption 读感留待 03 实际成品观察，不在 02 返工。

### [04 — 三平台共享无字封面](issues/04-shared-text-free-cover.md)（本票通过）

**Blocked by：** 01。02 与本票可独立，不构成依赖。

**用户看到的成果：** 按文章内容从源图或生成图中选择合适图片。LinkedIn、知乎、微信的双语稿复用同一张无字封面；不裁切，来源/Alt 等素材信息仍可追溯，最终 Markdown 可读。

**最小触点：** 在现有封面角色中选择合适已有源图或生成图；只在 fresh-read 证明必要时对当前 `source-cover` 角色做最小扩展。借鉴 Baoyu Cover Image 与 KarenSpinner 对含义/具体对象到主体、动作、背景、构图和配色的拆分，写成本项目简短画面指导；不照搬默认文字、字体维度、固定角色或无限修图。封面围绕文章真实主题规划，不叠标题/Caption、不裁切，语言版本及平台复用同一 asset。

**局部成功 / 必要失败：** 检查一份文章双语 Markdown 的共享封面身份、无字未裁切、图片可打开；沿现有错误路径确认封面失败时稿件保留。无需每篇重新生图。

**停止点：** 当前角色无法表达需求且改动会扩大到新服务/平台适配；实施需生产发布或发送邮件；或失败导致稿件丢失。

**当前状态：** 主控已验收 886/887 的实际封面结果：一次自由 Planner、一张实际生成封面，PNG 1672×941，无可见文字，未裁切，双语同 URL、Caption 空，正文源图及受控失败保稿路径保留。Alt“计数器”与实图手刨工具的小差异为非阻塞，不重抽。UAT clean draft `83a9ba97-8d03-4127-9c3f-d062cae56372` 对永久 baseline `04cc31a4-c7fa-4a5f-9510-0f375221c880` 业务 diff 空，99 节点、active `96042bba-9621-4571-98b6-976dc819c4fc` 不变。其他新规划正文图未完成，本 EPIC 未完成。

### [05 — 内容驱动风格与近期封面参考](issues/05-content-driven-style-history.md)（本票局部通过）

**Blocked by：** 04。此依赖表示先有共享封面交付，不表示 02 是 04 的前置。

**用户看到的成果：** 封面先表达文章内容，再选择合适风格；近期封面提供有限的软参考，帮助减少相似观感但不强迫轮换。

**最小触点：** 为现有风格库补充适用表达/气氛说明；封面计划包含简短视觉表达、主体、构图、配色和手法。参考 Baoyu 的 type/palette/rendering 区分与实际图像参考条件，将其压缩为本项目指导，不引入其 font 维度或固定映射。实施前核查当前模型与节点真实支持的图片输入能力；Gemini 文档只说明该 API 示例，不能证明现有链路支持。仅参考现成保存包中最近三篇不同文章的实际封面图像，或从实际图像读取的可靠视觉摘要；旧 prompt 只辅助理解创作意图，不作视觉参考，也不能替代成图。双语同封面计一篇。此三篇规则是本项目自拟软参考，调研来源未报告同类机制。只有确有必要且现有字段不足时，才增加最小 visual brief 字段。

**局部成功 / 必要失败：** 用实际封面图像或从实际图像读取的可靠视觉摘要作软参考；检查共享封面及 Markdown 交付。历史不足时使用已有图像；读取历史失败时保留正文并如实注明未参考。源图保留原内容，不重画成假实测。

**停止点：** 需要新 provider、向量库、历史 ledger、评分或轮换表；图片输入能力未经当前链路证实；或参考读取失败会阻断正文。

**当前状态：** 主控接受 05 的局部范围。888 实际同文件夹 9 metadata、4 包、2 references（839/832）；当前 856 排除，832/827 按实际 content_id 去重，815 无 cover。889 实际两历史视觉读取加一自由 Planner，独立 references、75/19/79 与 3 当前描述保留。首次 client 流中断已原位恢复，恢复阶段新增模型/测试 0；旧大响应分支保持停止。05 阶段未生成新图；03 后续实际产物已由主控查看，结论仍限本轮局部功能。UAT clean draft `5f4cc08c-b248-47cf-852e-61dcdcd2d86a` 对 `3a57eea3-2ca1-4a5e-9c81-a55e1e0a8697` 业务 diff 空，105 节点、active 不变。

### [03 — News/Deep 成品验证与冻结](issues/03-visual-validation-and-freeze.md)（本轮局部功能完成）

**Blocked by：** 02、04、05。仅依赖实际必需切片，不重复全链。

**用户看到的成果：** News 与 Deep 各有保存稿件和可读的双语 Markdown；复用 02 的真实 Deep 取材/规划观察及既有 News 实际源图通路，失败不会丢稿，可恢复增量可检查。源图与生成图按内容需要选择，不强迫每篇必须有 source。

**最小触点：** 复用 02 的真实 Deep 观察和既有 News 实际源图通路；只对必要的新边界补证，不额外制造测试轮次。检查实际交付中的图片、封面和图注可打开/可读，无 TEMP 残留，增量可恢复。

**局部成功 / 必要失败：** 复用两种模式已有真实稿件回执；News 源图实际通路与 02 Deep 取材/规划观察可复核，只对必要的新边界补验。若 Deep 有贴题 source 且作者要求仍未采用，记录原因并将默认混搭效果标为未验证/未解决；News 下载通路或旧 Deep 生成输出不能替代该效果。失败时正文保留。节点 success、候选 URL 数量或单次模型响应不单独代表效果成功。

**停止点：** 需要未授权凭据、生产发布、邮件发送或全仓/逐句事实审计；无法恢复或稿件丢失时停止并报告首个证据。

**恢复快照：** fresh Mother `88b6ec3f-3738-42e7-82cf-e500a1355fd3` 为 105 节点、零 TEMP，原生业务 diff 对 `5f4cc08c-b248-47cf-852e-61dcdcd2d86a` 全部为空。完整 native draft 与旧 active `96042bba-9621-4571-98b6-976dc819c4fc` 的 93 节点图均已保存到 ignored freeze/，600，并校验 JSON/hash。依赖快照复用，不重扫。新 draft 尚未激活，没有恢复、publish、原 Drive 文件修改或 Git 提交。

**已保存依赖：** 保存基线只有 Topic Survey `Tx1BkAxjods79f0z` 与 Browser Pilot `lUzGBnb9I0T0WuLw` 两个可达 workflow 依赖，均无下一层 workflow 调用。已捕获 draft=active 分别为 `e7633a3d-a446-489d-b429-1fe84526a781`（21 nodes）和 `817e70f0-dc2f-4154-a7e2-5c02200b4780`（10 nodes）。本轮复用 native draft/active 图及校验和，不重查依赖。881 小 metadata 回执不含执行版本 ID，历史精确绑定仍 UNKNOWN；不重开旧大响应分支。

**最终 checkpoint：** 890 Deep 实际 3 generated / 1 source，891 无模型机械组装，892 News 实际 1 generated / 1 source；6 资产和 Deep/News 共四份双语 MD 已本地保存。News 仅一次小 Normalize metadata 读取后，以真实资产 per_language/provenance/placement、完整 fixture 和原版 Assemble/MD 代码纯机械组装，标记 replayed-from-observed-assets，非原生 MD 回读，无新模型/执行/生成。主控已查看六实际资产，确认混搭、不同画法与两封面无可见字，并接受本轮局部功能。News 原生大响应回读未解决、个别视觉选择仍需使用改进，均为明确非阻塞项。Deep 原图为发布素材，News 为既有鹈鹕自行车示例图，不能推为每篇都会取得核心实测图。不是生产 E2E 或稳定质量认证。Harvey client 失败计数 2 与旧大响应分支停止记录保留，数据量相关仍只是推测。

## 外部参考研究（已完成，2026-10-10）

来源方法、直接链接、项目自拟适配与不照搬项见[一手参考研究](../../docs/research/ai-daily-visual-reference-kb-2026-10-10.md)。该研究没有测试源项目或 AI Daily 的图像效果，也没有确认现有 n8n/GPT-6 Sol 链路支持图像输入。
