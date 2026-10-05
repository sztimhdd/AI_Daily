# Deep 中文：接口通过，编辑质量仍待修复

## 结论

[KNOWN][HIGH] 2026-10-05，母执行 672 → 原 Writer integrated 子执行 674 → 母末端断言成功。复用原中文主笔、一次原中文编辑和共用视觉尾部，返回中文深度图文预览。不是重新研究、真实选稿审批或生产发布。

[KNOWN][HIGH] 不能关闭出版质量验收：674 主笔初稿有四条读者向来源链接，编辑稿全部删除；全文仍有超出提供材料的技术概括和动机直述。接口断言只证明交接、结构、保稿与组装，不证明正文事实或文学质量。下一步先修原编辑的局部纠错与链接保留，再继续 Deep 英文；不新建审核器，不重抽全文或重做图片。

## Ponytail 裁决与最小改动

[KNOWN][HIGH] 本轮先读取原 ponytail 技能、当前分支计划、Writer/Shared Dispatch/Deep Editor/Mother。Writer 已支持 deep_analysis，并把 proposal.analysis_judgment 映射为 writer_brief.article_intent.thesis；无须新建 Deep 写作分支。实际缺口是 CN 编辑输入不携带完整简报，CN 预览丢配置/调用回执，失败编辑直接进入 Visual Input 后抛错。

[KNOWN][HIGH] 只修改四个既有中文节点：CN Edit Input 加入简报和模式/语言一致性检查；CN Preview 透传配置与调用回执；CN Lead Writer 补一段体裁规则；CN Line & Rhythm Editor 接收完整简报并补对应规则。主笔其余文义保留，空行压缩。所有英文节点、模型、凭据、共用视觉与 Shared Dispatch 不变。永久节点净增为零。

[KNOWN][HIGH] 复用现成且不限定语言的 V2 EN Preview Route / V2 EN Review Required。历史 EN 名称暂留，避免额外改名；正常稿去原视觉入口，失败稿原样返回。唯一永久接线替换：

```text
remove: V2 CN Preview -> V2 Visual Input
add:    V2 CN Preview -> V2 EN Preview Route
```

[KNOWN][HIGH] 保存映射：src/n8n/cn-edit-input.js、cn-preview.js 分别写入对应 Code 节点；cn-lead-writer.system.txt 写入 V2 CN Lead Writer.options.systemMessage；cn-line-editor.prompts.json 写入同名编辑节点的 parameters。主笔原 task prompt 不变。没有新增评分、重试服务、研究循环或平行工作流。

## 输入材料与授权

[KNOWN][HIGH] 复用本轮实读的历史 Deep Editor 执行 548 中 story_2 / deep_analysis / ready 提案，不是把 News 改个标签。工作标题为“从帮企业收钱到替企业选模型：Stripe 要进入 AI 的花钱环节”；既有判断讨论从收款向 AI 支出分配延伸。提案、读者承诺、判断、四个推进任务和归属边界未改。

[KNOWN][HIGH] 材料来自固定提交 92390c227e6a5a4ca5e7dfca02eedecc30496459 的现有 handoff.cjs 与 writer-news-557.cjs，只使用其 initial 部分：6 个来源条目、6 条断言、3 条引语。6 条目含 2 个 title_only，不等于 6 个可用来源。保留来源说明、原引语与上下文；没有将后来的 News 补查材料塞回 Deep。引语核验回执是复用历史 fixture，不是本轮新核实。

[KNOWN][HIGH] 为测试构造的 selection 明确 synthetic；本次调用决定是 controlled_test / user_chat_authorization，绑定 content/story/mode/title/reader promise/zh-CN，不冒充 formal_hitl。该直接 ready 工单历史授权字段未提供，回执 historical_writing_authorized=null；不把它说成历史 false 已转 true。原 prepared service_invoked=false 保持。Deep supplemental 继续 hold。

## 验证结果

| 执行 | 作用 | 结果 |
|---|---|---|
| [KNOWN][HIGH] 667 → 668 | 删除 analysis_judgment 的负例 | 原 Prepare Writing Handoff 报 Deep judgment missing；未调用 Writer 或模型。 |
| [KNOWN][HIGH] 669 → 671 | 编辑错误传输 | 合成固定初稿＋实际抛错 Code，使用 continueRegularOutput；原适配/预览/共用路由返回 review_required，原稿、配置、回执保留，无写作/编辑/视觉模型调用。不是一次真实模型故障。 |
| [KNOWN][HIGH] 672 → 674 | 一次真实正例 | 原 CN 主笔、原 CN 编辑、共用视觉规划、生图、上传、组装连续成功；母末端 passed=true。没有重跑研究或重抽主笔。 |

[COMPUTED][HIGH] 本地 node --test tests/n8n/cn-writing-context.test.cjs：原代码 7 项中 1 通过、6 失败；修改后及收尾复跑均 7 通过、0 失败。测试覆盖 Deep/News 简报原样传递、错误语言拒绝、空初稿拒绝、正常/错误/无效编辑响应的原稿与元数据保留。只算该接口测试，不是全仓 CI。原两份 Code 文件字节的 Git blob 与仓库基线一致。

[KNOWN][HIGH] 672 起止 21:43:01.574–21:44:56.422 UTC；674 起止 21:43:01.928–21:44:56.061 UTC，parentExecutionId=672、终点 V2 Article Assembler。主笔、编辑执行各一次，均无工具调用。

[COMPUTED][HIGH] 初稿 2977、编辑稿 1901 字符（JavaScript string.length，非纯中文字数）；请求/成功/失败图片 2/2/0，封面独立，正文插入 1 张。正文图数量来自本次 Planner 决定。移除精确插图块后，组装正文与编辑稿逐字符一致。母断言 judgment_preserved 指输入 proposal 未改变，不是模型正文语义自动验收。返回 publication.state=NOT_PUBLISHED、url=null。

## 上传与可见性边界

[KNOWN][HIGH] 原 Upload Image to GitHub 两份回执成功，目录 n8n/images/20261005/test_full-source-dossier-20261002-r2/。

| 文件 | Blob SHA | 回执字节数 |
|---|---|---|
| [KNOWN][HIGH] COVER_IMG-674.png | 11cdcab282135da8c25d5bdae98b8bd785abbde9 | 2918769 |
| [KNOWN][HIGH] IMG_1-674.png | e965917b2e4c85fa01595b67b78dd10c6a246776 | 2539642 |

[KNOWN][HIGH] 图片提交 2ca6c7ac0f326c76bf75a3506a4177753d423e9c、3379fc1350467e36bce489e07ac5baf21fb8d437。唯一警告 image_geometry_warning:COVER_IMG。尺寸仍来自 requested_size，本轮未做匿名图片下载、解码或设备显示验证；不得把回执当成可见性证明。封面目标比例和实际像素验证仍待收尾。

## 清理与恢复点

[KNOWN][HIGH] Writer nHxILnDVz541Cu5P：起点 3f6c0030-d572-4ec1-8ba6-e2d27486326f；永久补丁 876ed9bb-7ec8-4edd-9283-04ffb1d84bc1；两枚故障探针清理后 e99399b8-e083-4ad4-b820-58b20933a116。补丁→清理版原生 diff 全空；起点→清理版仅四节点参数变化、一条移除/一条新增主连接。81 节点、inactive、无 activeVersion。

[KNOWN][HIGH] Mother xR7fM1ZhxlMTUy0L：起点 5a2a9835-bf50-497b-a6b8-0c0a362e68f8；临时测试版 426f5bd0-5d2d-47a2-a2ed-43a81ed695d7；八节点清理后 458e8a54-26e7-4eb9-a14b-903cc8085e4a。起点→清理版原生 diff 全空，46 节点，activeVersionId 仍为旧 c94debcc-2fe0-438a-a3df-a1d699740c99。未发布、未改凭据、未合并 main。

## 已定位而未修复的编辑问题

[KNOWN][HIGH] 初稿四条链接指向已有公司公告、卖方说明和两份媒体报道；编辑时删除了全部链接，虽然相应事实与转述仍在。不是上游没有来源，也不是组装器删除链接。

[INFERRED][HIGH] 原稿与编辑稿把路由概括成平台普遍替用户自动选择模型，并扩展出一行配置、输入输出计费等未在本次材料里建立的细节；重试成本的条件推理可以保留，但不能附带未经材料支持的产品行为。部分“看中的正是”措辞也将分析判断说成确定动机。收尾应在现有编辑中就地修复，保留已生成稿件和图片，不再跑主笔/视觉来掩盖问题。

[INFERRED][HIGH] 本次产物确实围绕选定的支出分配判断展开，不是 News 的逐句翻译；但开头与结尾重复，标题和若干总结句仍可收紧。正文结构断言不是这项判断的证据，裁决来自阅读实际两稿的作者自审，没有第二名独立审查者。

[KNOWN][HIGH] 公开仓库保存代码、7 项局测、可删除测试节点配置和本检查点；正文、原始执行全集、恢复令牌、凭据不入库。预览交付文件为原自动产物，不能当作已经完成最终编辑的版本。测试配置再次使用须取得新授权，不能挂到生产入口。
