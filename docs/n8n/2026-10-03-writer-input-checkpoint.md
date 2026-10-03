# AI Daily V3 — Writer 输入映射检查点

## STATUS

[KNOWN][HIGH] 本轮通过的是 T02 的 Writer 子流程输入映射与中文路由子单元，不是母子流程集成、调用授权或成稿验收。没有调用任何写稿模型，没有生成正文或图像。

[KNOWN][HIGH] 工作流 `nHxILnDVz541Cu5P`（Universal Draft Writing V2）仍为未发布草稿：76 节点，active=false，activeVersionId=null。最终回读版本 `dcd1c859-74ad-40f0-92c8-458e759412f8`。

## CHANGES

[KNOWN][HIGH] 唯一业务代码变更是 `Writer Context Builder`（节点 ID `1f7381ae-dd6f-4219-a5d0-bd485a731a6b`）。入口移除 `Execute Workflow Trigger → Normalize + Evidence Compiler`，新增 `Execute Workflow Trigger → Writer Context Builder`。后接既有 `V2 Language Switch`；三个输出仍无下游。未增加或删除节点，未改变提示词、模型、凭据、其他工作流或发布状态。

[KNOWN][HIGH] 变更前及回滚点：`7297a582-4db4-457f-99ed-bc71f28b15fe`。变更后：`dcd1c859-74ad-40f0-92c8-458e759412f8`。已用原生版本差异核对：一个节点修改、一条入口边删除、一条入口边新增。旧代码由原生版本历史保留；不把含凭据的整张工作流导出到仓库。

[INFERRED][HIGH] 此次有意迁移未发布 V2 的入口合同：只接收 prepared 的 `writing_work_order.v1`，不再接受旧的 Markdown/creative_blueprint 独立输入或模型重新生成的 Story Contract。旧编译器和策划节点保留但不在当前入口路径中；不维护额外兼容分支。这不是全实例调用依赖审计，也不证明所有历史调用方都已迁移。

## INPUT / OUTPUT

[KNOWN][HIGH] 输入要求既有 T01 工单，以及明确的 `task_config.language` 和 `task_config.content_type`。本地及原生样本显式补入任务配置；T01 生产者本身没有在本轮新增语言分发。支持语言精确为 zh-CN/en-US；其他存在的语言字段冲突即拒绝，不从标题语言猜测，也不由平台推导语言。

[KNOWN][HIGH] 输出复用 `writer_context.v1` 和 `writer_brief.v3`。标题、读者承诺、原始人工指令、Story 路径、事实原文、引语原文与归属由已有对象确定性投影。News 的 thesis 为 null；Deep 只接收已有非空且非 none 的 judgment，不生成新判断。

[KNOWN][HIGH] 收到的完整工单保存在输出 `writing_work_order` 中，不改写；历史授权 false、历史补查要求、原始/增量材料及初轮验证对象保留。该对象仅供审计和后续调用核对，不应发送给模型。`ready_for_writer=true` 仍仅表示当前映射成功，不代表允许调用、文章合格或发布。

[KNOWN][HIGH] 模型输入保留来源的 retrieval_status/source_note、事实状态和引语语境；问题与冲突保留在 evidence_boundaries，不因跳过策划模型而被静默丢弃。原始来源、引语的命名空间留在工单及 reviewer context；普通样本的 writer_brief 使用可读出处和 URL，不把工作流历史/授权对象灌入 Writer。原始问题/冲突对象可能带内部引用，它们仍是输入限定，不能据此声称未来正文已通过内部标记清理。

## EVIDENCE

[KNOWN][HIGH] 原生测试使用 `prepare_workflow_pin_data` 后调用 `test_workflow`：触发器输入固定；Code/Switch 正常执行；外部节点有固定空数据且位于既有物理断线之外。不是模型输出模拟成稿，也不是母流程真实审批回放。

| execution | 样本和预期 | 实际结果 |
|---|---|---|
| [KNOWN][HIGH] [580](https://ohca.ddns.net/workflow/nHxILnDVz541Cu5P/executions/580) | 旧入口，prepared 工单、空 brief_content | RED：`Evidence Compiler: brief_content is empty [line 21]` |
| [KNOWN][HIGH] [581](https://ohca.ddns.net/workflow/nHxILnDVz541Cu5P/executions/581) | 同一固定输入，修改后的入口 | success；真实映射结果进入 Switch 输出 1（中文），输出 0/2 为空 |
| [KNOWN][HIGH] [582](https://ohca.ddns.net/workflow/nHxILnDVz541Cu5P/executions/582) | 在同一输入只增加冲突的 creative_blueprint.language=en-US | 预期拒绝：`Writer input: conflicting language [line 3]` |

[KNOWN][HIGH] 已读 581 的实际路由输出：2 来源、2 claims、2 引语；两条 QT01 的原文、speaker、归属和 URL 不混同；原始人工指令、空文本、null title_override 与历史 false 都保留；News thesis=null。指定检查的策划、CN/EN Writer、生图、上传节点均无执行数据，最后节点为 V2 Language Switch。

[COMPUTED][HIGH] 本地最终运行 `node --test tests/n8n/*.test.cjs`：63 tests，63 pass，0 fail。包含原有 T01 的 28 项和本轮新映射的 35 项。新测试直接执行仓库中两个实际 Code 节点函数体：先生成工单，再映射；覆盖直接/补查 × 中英、Deep 判断、原文与完整工单保留、8/10/5 材料计数、引语命名空间、来源资格、语言冲突和缺失、零引语、未决问题与冲突、身份错误、授权升级和多项输入拒绝。

[KNOWN][HIGH] 候选实现的额外本地 RED 曾发现未决问题/冲突未进入中文 brief（35 项中 34 通过、1 失败），在唯一一次原生部署前补齐 evidence_boundaries 并重跑通过。原生部署后没有非预期失败；582 是期望拒绝，不计作一次错误修复重试。

## PAYLOAD PROVENANCE / REPRODUCE

[KNOWN][HIGH] 大样本复用分支 `n8n-v3-handoff-20261003` 的 `tests/n8n/fixtures/handoff.cjs`，已回读并核对 blob `4859d1116737b95e59ec3475d14fd7e4feb5b539`。它本身是历史 557 的裁剪衍生样本，不是完整原始导出。

[KNOWN][HIGH] 原生 2/2/2 样本由新文件 `tests/n8n/fixtures/writer-input-native.cjs` 复用同一来源文本构造；测试标题、读者承诺和审计 envelope 有意缩减，验证对象只是映射。因此该样本不是完整 T01 真实收据、正式 HITL 批准或可直接用于成稿验收的材料。没有在本轮重新核实其中新闻。

```sh
node --test tests/n8n/*.test.cjs
node tests/n8n/fixtures/writer-input-native.cjs
node tests/n8n/fixtures/writer-input-native.cjs --conflict
```

[KNOWN][HIGH] 原生重跑先 fresh-read 工作流与隔离状态、准备 pin data。将上述生成 JSON 包为 `Execute Workflow Trigger: [{json: payload}]`，其余需固定数据的断开节点采用空对象。不得发布工作流来绕过直接执行入口限制。

## REPOSITORY

[KNOWN][HIGH] 沿用原分支，不合并 main。新增：`src/n8n/writer-context-builder.js`、`tests/n8n/writer-input.test.cjs`、`tests/n8n/fixtures/writer-input-native.cjs` 和本文件。原有 T01 实现、测试及 fixture 未改写。代码和样本的远端 blob 已与本地文件哈希比对一致。

| 文件 | git blob |
|---|---|
| [COMPUTED][HIGH] writer-context-builder.js | `8861fd6b665fe44a127aaca33355186ee04b4751` |
| [COMPUTED][HIGH] writer-input.test.cjs | `5de4d40e2340f2195e0a2d1ba78f6bf41071db75` |
| [COMPUTED][HIGH] writer-input-native.cjs | `928b8ec80b7fd2f89802ea10fea2929e28eb87f4` |

## RISKS / NEXT

[KNOWN][HIGH] 本轮为自审，未进行独立 reviewer 验收。完整仓库克隆本轮再次被 `Could not resolve host: github.com` 阻断（一次尝试）；未运行全仓其他测试或 CI。连接器读写正常。有一次回读误带 branch 参数被工具拒绝，移除该参数后读取成功，未造成写入。

[KNOWN][HIGH] 母流程的两个入口、原始审批真实性、父子版本和正文/编辑/图像链仍未验收；不要直接接回 Writer 输出。英文虽有输入映射测试，旧英文提示词和后续节点的完整语义兼容性仍待实际执行验证。全景稿不强制 thesis 的 prompt 行为也尚未检验。

[INFERRED][HIGH] 下一单元是显式 Writer 调用边界，先选 News 中文。应取得完整研究/补查材料及可核查原批准，或记录新的局测授权；不能拿本轮缩减映射样本冒充完整成稿测试。历史 false 不改写，为本次新调用单独记录依据。母入口连接、语言配置生成和母子透传尚需后续验证，不把孤立子流程映射通过标为全链完成。

[KNOWN][HIGH] 回滚仅使用本轮变更前版本，保留前轮安全断线与语言路由修复；回滚前先确认没有他人后续变更。无新增生产副作用，无需清理 TEMP 节点，因为本轮没有添加临时节点。
