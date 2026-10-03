# AI Daily V3 — T01 准备节点检查点

## STATUS

[KNOWN][HIGH] 本单元通过：既有 `Prepare Writing Handoff` 节点接受直接 ready 与 News 补查 ready，输出 `writing_work_order.v1` / `writing_handoff.v1`，没有调用 Writer。仅证明此节点的准备行为，不表示母流程接通、正式审批成功或文章验收。

[KNOWN][HIGH] 2026-10-03 用户明确授权使用 GitHub 保存代码、历史 payload 和回执；因此本轮在独立分支 `n8n-v3-handoff-20261003` 保存，不沿用旧计划中的 Git 禁令。没有合并 main。

## CHANGES

[KNOWN][HIGH] 工作流：[Shared Dispatch](https://ohca.ddns.net/workflow/qAfs9BDFbdBotgaB)。唯一业务节点：`Prepare Writing Handoff`，ID `580afa80-66a6-4646-9fa2-92a59144418c`。

| 阶段 | draft version |
|---|---|
| [KNOWN][HIGH] 变更前 / 回滚点 | `c27d7a21-49b0-4a0c-93ea-28fd5dd8cc2b` |
| [KNOWN][HIGH] 加入临时探针 | `bdc93df7-a683-4e95-8711-80cee0f437dd` |
| [KNOWN][HIGH] 业务代码修复 | `902a46a1-b857-4baa-8653-c7cfe081c090` |
| [KNOWN][HIGH] 清理后最终草稿 | `e621d10c-6bbf-47d2-893f-f9b411d5af05` |

[KNOWN][HIGH] 最终 fresh-read：7 个节点，`active=false`、`activeVersionId=null`。基线到最终版本差异：无节点增删、无连线增删，仅该节点的 `jsCode` 改变。三个 TEMP 节点已删除；原生测试在删除前运行，删除后验证的是版本差异与配置状态。

[KNOWN][HIGH] 新节点使用当前候选判断研究是否完成；历史补查要求不重新变成待办。合并材料与原始材料、接受的增量逐项比较；检查完整命名空间引用、来源资格、引语原文及归属。空 `brief_content` 不再成为拒绝结构化准备的理由。

## EVIDENCE

[KNOWN][HIGH] 原生执行使用隔离临时入口：Webhook → 固定测试输入 → 原业务节点 → 输出断言。路径没有模型、研究调用、邮件、HTTP Request、写表或发布节点；没有启用工作流。

| execution | 输入 | 实际结果 |
|---|---|---|
| [KNOWN][HIGH] [572](https://ohca.ddns.net/workflow/qAfs9BDFbdBotgaB/executions/572) | 旧节点 + reassessed | RED：`writing is not ready` |
| [KNOWN][HIGH] [573](https://ohca.ddns.net/workflow/qAfs9BDFbdBotgaB/executions/573) | 相同 reassessed 输入 | prepared；输出断言通过；2 来源、2 claims、2 引语；两个授权标志仍 false |
| [KNOWN][HIGH] [574](https://ohca.ddns.net/workflow/qAfs9BDFbdBotgaB/executions/574) | direct 合成正例 | prepared；输出断言通过；1/1/1；未新增 writing_authorized |
| [KNOWN][HIGH] [575](https://ohca.ddns.net/workflow/qAfs9BDFbdBotgaB/executions/575) | 删除补查来源 | 拒绝：`merged material count changed` |
| [KNOWN][HIGH] [576](https://ohca.ddns.net/workflow/qAfs9BDFbdBotgaB/executions/576) | 篡改选中引语 | 拒绝：`selected quotation drift` |
| [KNOWN][HIGH] [577](https://ohca.ddns.net/workflow/qAfs9BDFbdBotgaB/executions/577) | 当前 required research 未解决 | 拒绝：`unfinished current research` |
| [KNOWN][HIGH] [578](https://ohca.ddns.net/workflow/qAfs9BDFbdBotgaB/executions/578) | 历史授权改成 true | 拒绝：`historical authorization must remain false` |
| [KNOWN][HIGH] [579](https://ohca.ddns.net/workflow/qAfs9BDFbdBotgaB/executions/579) | 候选身份错配 | 拒绝：`candidate/context identity mismatch` |

[KNOWN][HIGH] 575–579 的引擎状态为 error，但都是期望拒绝；停在准备节点，未运行输出断言。573/574 的断言验证原输入快照、材料、空文本及授权字段，不只看节点绿色。

[COMPUTED][HIGH] 本地相同 28 个用例：旧代码 9 通过 / 19 不通过，修复后 28 通过 / 0 不通过。其较大 fixture 保留 8 来源、10 claims、5 引语及 3 个选中引语，覆盖标题、承诺、人工原话、Deep none、重复引用、来源资格和验证计数等边界。

[KNOWN][HIGH] 这些是从母执行 557 的公开材料裁剪构造的衍生 fixture，不是原始完整导出。原生探针进一步缩为 2/2/2；direct 输入明确标为合成。没有把测试数据视为正式 HITL，也没有本轮重新核实其中新闻。原始 execution 以系统记录为准；仓库不保存 resume token、凭据或原始运行栈。

## REPRODUCE

[KNOWN][HIGH] Node 内置测试，无第三方依赖；`src/n8n/prepare-writing-handoff.js` 是 n8n Code 节点函数体，不是可直接运行的命令行模块。

```sh
node --test tests/n8n/handoff.test.cjs
# 回归对照：预期非零退出，9 pass / 19 fail
HANDOFF_CODE=tests/n8n/fixtures/prepare-writing-handoff.before.js node --test tests/n8n/handoff.test.cjs
```

[KNOWN][HIGH] 原生夹具位于 `tests/n8n/native-probe.js`，断言位于 `tests/n8n/native-assert.js`。重跑前须重新核对 live 版本及副作用，临时节点名称必须对应断言中的引用；请求体用 `test_case` 选择上表案例。不要发布临时入口，也不要覆盖其他人在工作流上的新改动。

## RULINGS / RISKS

[INFERRED][HIGH] 先完成 T01 准备节点，而不是同时推进 writer brief 映射：live 节点尚不接受补查输入。代价是本轮没有产出正文，但避免将两个未验证环节一起修改。

[KNOWN][HIGH] 新增 `preparation_source` 仅保留收到的完整输入，供后续审计；不能发送给 Writer 模型。它不会恢复上游已经丢失的审批 bundle，也不证明审批真实性。正式调用仍需后续 T03 独立核对批准来源。

[KNOWN][HIGH] 补查输入没有 `title_override` 时输出 null，不虚构标题覆盖决定；直接 ready 的既有字符串保持不变。后续映射须处理 null。原始 quotation_validation 仍只代表初轮，补查验证记录保留在 preparation_source 中，不能把它说成一个覆盖全部材料的新验证结果。

[KNOWN][HIGH] 当前正式路由仍只有直接 ready 可到该节点；补查输入本轮通过临时入口测试，母流程 reassessment 接线没有修改。Deep 补查仍拒绝；直接 Deep 的结构正负例只在本地测试，不代表分析判断质量已验收。

[KNOWN][HIGH] 这是自审，不是独立 reviewer 验收。完整仓库克隆因运行环境 DNS 失败，本地只运行此单元 Node 测试，未运行仓库其他测试或 CI。GitHub 文件通过连接器保存并逐项核对 blob SHA；没有借此声称全仓回归通过。

[KNOWN][HIGH] 未修改母工作流、新版 Writer、Researcher、提示词、模型或凭据；没有邮件、图片、发布或生产 ledger 操作。没有修复后非预期的原生失败；上述 RED 和负例错误均按预期保留。

## NEXT

[INFERRED][HIGH] 下一单元：fresh-read 新版 Writer `nHxILnDVz541Cu5P`，把准备工单确定性映射到写作输入；复用本分支 fixture，不再调用旧 Story Contract Builder 重选叙事。先验证 News 中文输入材料、引语、标题/承诺和语言，再单独处理调用边界；本检查点不授权正式发布。

[KNOWN][HIGH] 回滚此节点可使用上表基线或仓库 before.js；回滚前确认没有他人后续变更。此前母流程和 Writer 的安全断线不在本单元回滚范围内。
