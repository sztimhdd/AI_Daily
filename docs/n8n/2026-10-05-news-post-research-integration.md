# News 补查后写作集成验收 — 2026-10-05

## 结论与范围

[KNOWN][HIGH] 本单元完成的是：已取得的 News 补查后 ready 回执 → 现有 Shared Dispatch → 母流程调用准备 → 原 Writer → 中文编辑 → 真实配图 → GitHub 上传 → 图文预览返回母流程。母执行 652、Writer 子执行 654 均为 success，母流程末端验收断言 passed=true。

[KNOWN][HIGH] 这是完整历史写作材料回放，加明确标记的合成审批来源；不是新的现场研究，不是一次真实 Gmail 人工选稿，也不是生产上线。测试入口在现有 News Reassessment Ready?，未重跑它之前的 Receive Selected News Reassessment、News 编辑复评或研究服务。

## 基线与清理

[KNOWN][HIGH] 仓库 sztimhdd/AI_Daily，分支 n8n-v3-handoff-20261003；开始时 HEAD 为 2e6ef29abaa18141fffc64d4995ea236980a9c04。

[KNOWN][HIGH] Mother xR7fM1ZhxlMTUy0L：基线草稿 082f4ce5-8c94-4fae-a442-e180d46e330f；临时测试版 3b87b80c-d6aa-4efe-a733-aabd3162f9c3；清理后草稿 4eab367f-e19e-4d39-b8c7-e2a661998a52，46 节点。原生版本差异确认基线到清理版的 nodesAdded / nodesRemoved / nodesModified / connectionsAdded / connectionsRemoved 全为空。

[KNOWN][HIGH] 五枚临时节点及其连接已移除：TEMP News Integration Entry、TEMP Read Handoff Fixture、TEMP Read Writing Fixture、TEMP Prepare News Replay、TEMP Assert News Integration。没有保留测试 webhook、加载器、断言终点或 Writer 副本。

[KNOWN][HIGH] Mother 的 activeVersionId 仍为 c94debcc-2fe0-438a-a3df-a1d699740c99。Writer nHxILnDVz541Cu5P 仍为 e2fe8fc5-ba30-430b-8a33-403fb8e89b87，81 节点、inactive、无 activeVersion；Shared Dispatch qAfs9BDFbdBotgaB 仍为 6125e9ed-2270-42c4-b601-8a245adb7455，8 节点、inactive、无 activeVersion。本轮没有发布、合并 main、修改凭据、模型或业务提示词。

## 回放来源

[KNOWN][HIGH] 两个已有 fixture 从不可变提交 2e6ef29abaa18141fffc64d4995ea236980a9c04 读取：tests/n8n/fixtures/handoff.cjs 与 tests/n8n/fixtures/writer-news-557.cjs。后者恢复写作需要的来源说明、断言支持、引语上下文和编辑材料；它不是执行 557 的逐字节原始导出，也不代表本轮独立核实了新闻。

[KNOWN][HIGH] 材料包含 8 来源、10 断言、5 引语；其中初轮为 6 / 6 / 3，补查增量为 2 / 4 / 2。仅标题来源仍标为不适合支持断言。选用引语为 supplementary:QT01、initial:QT01、initial:QT02；相同局部编号不能跨命名空间合并。

[KNOWN][HIGH] 加载器只向测试副本添加合成 approval_bundle 与 selected decision，保留原 title、reader_promise、研究任务和 next_action=targeted_research。test_context 明确 synthetic_approval=true、formal_hitl=false。现有调用准备器生成 formal_hitl 形状的当前调用决定，只证明合同兼容，不证明真实人工审批发生过。原 fixture 文件和历史执行没有被改写。

## 本轮原生执行

| 执行 | 输入 / 路径 | 实际结果 |
|---|---|---|
| [KNOWN][HIGH] 649 | 完整材料，删除测试审批对象 | 在 Prepare Writer Invocation 报 selected approval provenance missing；未进入 Writer。此 error 是预期拒绝。 |
| [KNOWN][HIGH] 651 | needs_editor_decision / editor_review | Finalize Reassessment Hold 原样返回回执；断言 passed=true、writer_called=false。 |
| [KNOWN][HIGH] 652 → 654 | ready_for_writer_handoff / prepare_writing_handoff | 经现有 Shared Dispatch 和原 Writer 连续返回图文；母执行验收 passed=true。 |

[KNOWN][HIGH] 母执行 652 时间：18:53:18.553–18:55:37.443 UTC；Writer 654 时间：18:53:18.938–18:55:36.830 UTC。654 为 integrated，parentExecutionId=652；没有原 Writer 的临时同代码副本，没有使用 pin-data 测试替代模型。

[KNOWN][HIGH] 正例实际返回：writing_preview.v1、editing_status=completed、assembly_status=completed、publication.state=NOT_PUBLISHED、publication.url=null。原稿 4239 字符、编辑稿 3427 字符（JavaScript string.length，非中文字数）。Planner 本次选择 1 封面 + 1 正文图；requested=2、succeeded=2、failed=0，正文实际插入 1 图。这不是图片数量配额。

[KNOWN][HIGH] 末端断言确认：全量 preparation_source、初轮与补查材料、选用引语保持；writing_authorized=false、research_loop_authorized=false 与历史 targeted_research 不被改写；身份和目标语言一致；初稿保留；从组装稿去除每个精确图片插入块后，文本与编辑稿逐字符一致；封面保持独立字段。

## 实际上传回执

[KNOWN][HIGH] 两张图片均通过既有原生 Upload Image to GitHub 节点写入开发分支。本轮没有匿名下载、像素解码或用户设备显示验收；上传回执不替代这些证据。

| 图片 | 仓库路径 | Blob SHA | 回执字节数 |
|---|---|---|---|
| [KNOWN][HIGH] COVER_IMG | n8n/images/20261005/test_full-source-dossier-20261002-r2/COVER_IMG-654.png | e785f2a044cc28fe8d043a555f837934e3701975 | 2878408 |
| [KNOWN][HIGH] IMG_1 | n8n/images/20261005/test_full-source-dossier-20261002-r2/IMG_1-654.png | a36e1f2566c6afbc404c510c72567c237b59e170 | 3132598 |

[KNOWN][HIGH] 图片上传提交分别为 5b212ae4d7ea4d4f66d71d9bbed78fb73a7868c6、e26c2a1fff81e85fb92f7d57579e202d24b1ac64。唯一返回警告为 image_geometry_warning:COVER_IMG。归一化器尺寸仍来自 requested_size；1536×1024 不是本轮解码测量。16:9 裁切继续后置。

## 验收代码与本地检查

[KNOWN][HIGH] tests/n8n/native-news-integration-loader.js 保存临时回放加载逻辑；两个 HTTP 读取节点使用上述固定提交 raw 路径、无凭据、文本 data 字段、30 秒超时。加载器只限临时测试，不能接到产品入口。

[KNOWN][HIGH] tests/n8n/native-news-integration-assert.js 保存原生验收断言；tests/n8n/news-integration-acceptance-controls.test.cjs 用完整与损坏的模拟回执测试断言本身。

[COMPUTED][HIGH] 本轮本地控制测试 14 通过 / 0 失败，涵盖正文图 0 / 1 / 3 的合法数量，以及材料丢失、历史授权变化、身份错配、初稿丢失、发布状态变化、图片失败、错误图床、组装改文和图片丢失等拒绝条件。运行命令：node --test tests/n8n/news-integration-acceptance-controls.test.cjs。这不是全仓测试或模型质量评分；本轮没有声称全仓 CI 通过。

## 保留边界与下一步

[KNOWN][HIGH] 测试路径未连接真实邮件、生产 ledger 或浏览器发布；未重新执行研究、News 复评或其他语言。Deep 补查的现有 hold 路径没有修改，本轮不把先前的 Deep 负例当作重新运行结果。

[INFERRED][HIGH] 阅读检查仍能看到局部研究过程残留（如正文提及某报道只取得标题与两段）与后段重复。它不否定技术交付通过，也不应被包装成文学性或最终出版验收已通过；本单元不重抽初稿、不扩建评审层。

[INFERRED][HIGH] News 补查后 ready 到中文图文返回的受控集成待办可关闭。按既定顺序继续 News 英文、Deep 中文、Deep 英文；真实审批到发布的全流程以及封面裁切、Social Kit / 交付收尾仍单独处理。
