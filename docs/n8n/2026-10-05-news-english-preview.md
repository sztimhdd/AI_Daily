# News 英文预览接口 — 2026-10-05

## 结论与范围

[KNOWN][HIGH] 已完成显式 en-US 写作工单 → 原 Writer integrated 子调用 → 英文主笔 → 现有编辑器一次 → 共用视觉规划/生图/上传/组装 → 母流程返回的受控技术验收。正例母执行 664、Writer 子执行 666 均 success，母末端断言 passed=true。

[KNOWN][HIGH] 本轮不是新研究、真实邮件选稿、生产双语分发或最终出版验收。永久母流程的 Prepare Writer Invocation 仍指定 zh-CN；本轮用可删除测试分支传入 en-US / linkedin_longform，不能把它说成已经部署了双语生产调度。Deep 中文、Deep 英文尚未验收；Deep 补查继续 hold。

## 基线、改动与恢复点

[KNOWN][HIGH] 仓库 sztimhdd/AI_Daily，开发分支 n8n-v3-handoff-20261003，起点 HEAD 303bd34d6941ce015fd0d2644fede362b11c9f86。

[KNOWN][HIGH] Writer nHxILnDVz541Cu5P 起点 e2fe8fc5-ba30-430b-8a33-403fb8e89b87，81 节点。实读发现 V2 Language Switch 的英文出口未连接；旧英文分支仍使用多轮审稿、Convergence 和旧返回格式。

[KNOWN][HIGH] 只改六个现有节点的参数/用途：V2 EN Lead Writer；V2 EN Polish Input Builder → V2 EN Edit Input；V2 EN Line & Rhythm Editor；V2 Semantic Gate → V2 EN Preview；V2 Review Gate → V2 EN Preview Route；V2 Review Decision Builder → V2 EN Review Required。永久节点数不变。原两轮审稿及 Convergence 与执行主路断开，未新增平行 Writer、评分器或补查循环。

```text
V2 Language Switch (English)
 → V2 EN Lead Writer
 → V2 EN Edit Input
 → V2 EN Line & Rhythm Editor
 → V2 EN Preview
 → V2 EN Preview Route
    ├─ completed → 原 V2 Visual Input → 原视觉/生图/上传/组装
    └─ failed → V2 EN Review Required（原稿直接返回）
```

[KNOWN][HIGH] 主笔和编辑使用 writer_brief.v3；News 的 thesis=null 合法。编辑可以按材料修正文中局部偏差、调整推进，不再只接受旧 review_issues；结构适配不声称是事实验证或文学评分。没有添加研究工具。现有两个英文模型节点、模型参数、凭据不变。

[KNOWN][HIGH] 永久补丁版 e77c7aa4-a8f2-4275-9acd-17de4621de70；故障注入清理后的 Writer 草稿 3f6c0030-d572-4ec1-8ba6-e2d27486326f。原生 diff 确认两者业务图为空差异。相对起点 e2fe8fc5，只有上述六节点变化、5 条新增/7 条移除主连接；没有新增/删除永久节点，没有修改中文、共用视觉节点或模型/凭据。Writer 保持 inactive，无 activeVersion。

[KNOWN][HIGH] Mother xR7fM1ZhxlMTUy0L 起点 4eab367f-e19e-4d39-b8c7-e2a661998a52；临时测试版 ace58514-9e44-4a62-86ca-556db44ccdd5；清理后 5a2a9835-bf50-497b-a6b8-0c0a362e68f8，46 节点。原生起点→清理版 diff 全空。八个 TEMP EN 母流程节点及两枚 Writer 故障探针均已移除。activeVersionId 仍是旧 c94debcc-2fe0-438a-a3df-a1d699740c99，没有发布或合并 main。

## 授权与材料

[KNOWN][HIGH] 复用固定提交 303bd34d6941ce015fd0d2644fede362b11c9f86 中的 tests/n8n/fixtures/handoff.cjs 和 writer-news-557.cjs。它们是执行 557 衍生的历史材料，不是原始完整导出，也不是本轮独立核实的新闻。

[KNOWN][HIGH] 原始工单材料含 8 来源、10 断言、5 引语，保留 initial / supplementary 身份。采用当前用户继续开发指令产生 controlled_test，decision_source.type=user_chat_authorization，绑定 content/story/mode/title/reader promise/en-US；不伪造 formal_hitl，不向历史材料补写审批对象。历史 writing_authorized=false、research_loop_authorized=false 不改。测试分支物理隔离真实邮件、生产 ledger 和浏览器发布，远程图片只走既有开发分支托管。

## 本轮原生验证

| 执行 | 目的 | 实际结果 |
|---|---|---|
| [KNOWN][HIGH] 655 → 657 | 修改前 RED | 原英文出口未连接，子流程返回 writer_context.v1；母末端报 English preview missing。不是模型写作失败，没有主笔或生图调用。 |
| [KNOWN][HIGH] 658 → 660 | 语言授权错配 | en-US 工单配 zh-CN 调用授权，在 Writer Invocation Gate 报 target language mismatch；没有进入写作模型。 |
| [KNOWN][HIGH] 661 → 663 | 编辑异常保稿 | 固定测试初稿 + 实际抛错 Code 节点的原生 continueRegularOutput；原 EN Preview/Route/Hold 返回 review_required，article_markdown 与 draft_markdown 相同。主笔、编辑模型和 Visual Planner 均未运行。模拟的是编辑错误传输，不是一次真实模型故障。 |
| [KNOWN][HIGH] 664 → 666 | 修改后真实正例 | 原英文主笔、原英文编辑、原共用视觉尾部连续完成，母末端 passed=true；只跑一次真实英文正例，不重抽初稿。 |

[KNOWN][HIGH] 正例母执行 19:50:27.466–19:52:40.601 UTC；子执行 19:50:27.795–19:52:40.227 UTC，integrated、parentExecutionId=664，终点 V2 Article Assembler。语言 en-US，返回 writing_preview.v1、assembly_status=completed、publication.state=NOT_PUBLISHED、url=null。

[COMPUTED][HIGH] 正例断言计数：原稿 5436 字符，编辑稿 4784 字符（JavaScript string.length，非英文词数）；请求/成功/失败图片 3/3/0，正文实际插入 2 张，封面独立。全量 preparation_source 与写作材料保持；去掉精确图片插入块后，组装文字与编辑稿逐字符相同。英文正文及图注没有中文字符或测试检查到的内部标签。正文图数是 Planner 的本篇选择，不是固定配额。

## 图片上传证据

[KNOWN][HIGH] 原 Upload Image to GitHub 节点的三份回执均成功，目录 n8n/images/20261005/test_full-source-dossier-20261002-r2/。

| 文件 | Blob SHA | 回执字节数 |
|---|---|---|
| [KNOWN][HIGH] COVER_IMG-666.png | 0e9fc90226d6feccdb2c2d73b51cb474954047c6 | 1822918 |
| [KNOWN][HIGH] IMG_1-666.png | d790b98958726d9005768008139971fe3df39ed7 | 1687310 |
| [KNOWN][HIGH] IMG_2-666.png | 95161d792aa8125203238db39b239114518111bc | 1611300 |

[KNOWN][HIGH] 上传提交 dc8a34dd9d90203d76c75cfa57b9cf269df7945e、b995e36a0623f8cbef47936cb798ccd01ff511b0、279e6a7ebe25c01f902836fb327b750eaa66eed3。唯一返回警告 image_geometry_warning:COVER_IMG。归一化尺寸仍来自 requested_size；本轮未做匿名下载、像素解码或用户设备显示验证，不把上传回执等同于可见性证明，16:9 裁切继续后置。

## 保存与检查

[KNOWN][HIGH] src/n8n/en-writing.nodes.json 是六个现有节点的参数/接线补丁，不是新工作流。tests/n8n/en-writing.test.cjs 是本地接口测试。tests/n8n/native-news-en-acceptance.nodes.json 归档临时母流程、明确测试授权、验收断言及无模型故障注入，不能挂到生产入口，复用须重新取得测试授权。

[COMPUTED][HIGH] 本地 node --test tests/n8n/en-writing.test.cjs：16 通过、0 失败，涵盖英文上下文/简报绑定、News 空 thesis、缺稿/多稿、错误语言、编辑异常和无效响应保留原稿、身份/授权/发布状态透传、原生路由表达式及现有提示词字段。原生 655 是实际修改前失败证据，不把本地新代码测试冒充全旧系统 RED。本轮没有全仓克隆或全仓 CI；容器下载遭一次 DNS 失败后未盲目重试。

[KNOWN][HIGH] 收尾做了独立步骤的作者自审，没有第二名 reviewer：核对六节点原生 diff、母流程清理空 diff、编辑失败返回、语言门禁和真实生成/上传收据。公开仓库不保存文章正文、私有原始 payload、执行全集或恢复令牌。

## 裁决与待办

[INFERRED][HIGH] 裁决：保留母流程中文调用策略，只验证显式英文工单；代价是生产双语分发仍需独立接线验收。复用六节点而不清扫所有旧岛；代价是画布仍有不执行的旧审稿节点。用 controlled_test 而不补造历史审批，真实 HITL 留待单独验收。

[INFERRED][HIGH] 本篇英文自动产物还不是最终出版稿：结尾重复交割限定，媒体解读段和缓存更新段未提供足够直接的读者向来源链接，标题和推进仍可加强。最终编辑还应避免把 Cline 自身账户功能统称为 OpenRouter 的承诺范围。技术结构检查并不能证明无事实漂移；本轮不因此新建审核层或重复整篇生成。

[INFERRED][HIGH] 本单元技术接口可关闭。下一步按顺序 Deep 中文、Deep 英文；随后统一处理生产语言调度、封面裁切、Social Kit/交付和真实审批发布。原 CN 链未改，不把未重跑的中文结果算成本轮新验收。
