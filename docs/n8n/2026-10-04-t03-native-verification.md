# T03 受控调用边界：原生正例验证

## 状态与范围

[KNOWN][HIGH] 本轮完成受控测试输入通过写作调用校验的原生验证。此前“没有 native positive Gate execution”的阻塞已解除；正式人工审批、母子流程集成与文章生成仍未验收，不把本次结果标为全链完成。

[KNOWN][HIGH] 本轮没有修改任何 n8n 节点、连线、提示词、模型、凭据或发布状态。写作草稿 `nHxILnDVz541Cu5P` 始终为 `ee17d426-9bd3-4325-bb3c-8527c93a808c`，77 节点，active=false，activeVersionId=null。没有新增授权生成器或临时入口。

## 原生证据

| 执行 | 输入 | 实际结果 |
|---|---|---|
| [KNOWN][HIGH] [587](https://ohca.ddns.net/workflow/nHxILnDVz541Cu5P/executions/587) | 既有 2 来源 / 2 claims / 2 引语样本，加本轮受控测试决定 | Gate 实际执行成功；Switch 输出 1（中文）含一个 item，输出 0/2 为空；最后节点为 V2 Language Switch |
| [KNOWN][HIGH] [588](https://ohca.ddns.net/workflow/nHxILnDVz541Cu5P/executions/588) | 相同样本，仅 decision.target_language 改为 en-US | Gate 报 `Writer invocation gate: target language mismatch [line 4]`；未执行 Switch 或 Writer |

[KNOWN][HIGH] 两次均使用 prepare_workflow_pin_data 后的 test_workflow，固定触发器输入与外部服务输出；Mapper、Gate、Switch 不固定输出，由原节点代码执行。完整草稿检查确认 Switch 没有下游连线；指定读取的策划、中文/英文 Writer、生图、上传节点均无运行数据。

[KNOWN][HIGH] 587 的实际输出保留空 brief_content、null title_override、原人工指令、两个不同命名空间的 QT01 及其原文/归属/URL。News thesis=null；原工单及其 preparation_source 的 writing_authorized/research_loop_authorized 仍为 false；新 receipt 为 controlled_test，service_invoked=false。

[KNOWN][HIGH] 本次直接提交被工具接受，没有修改 Gate 来放行，也没有把样本改称 formal_hitl。历史工具拦截记录保留；本次成功不能证明历史拦截的原因。

## 样本与复现

[KNOWN][HIGH] 新文件 tests/n8n/writer-invocation-native.test.cjs 复用已有 fixtures/writer-input-native.cjs；后者复用 handoff.cjs 的历史衍生材料。材料、标题和报道路径未重新编造。它仍是缩减的接口样本，不是完整成稿材料，也不是正式审批。

```sh
node --test tests/n8n/*.test.cjs
node tests/n8n/writer-invocation-native.test.cjs --payload positive
node tests/n8n/writer-invocation-native.test.cjs --payload wrong-language
node tests/n8n/writer-invocation-native.test.cjs --payload missing-decision
```

[KNOWN][HIGH] CLI 只输出归档测试输入，不执行网络调用。原生重跑需先确认当前用户批准、草稿版本和服务断线，重新准备 pin data，并将输入置于 Execute Workflow Trigger 的 [{json: payload}]。不得固定 Gate 输出以冒充验证。归档 reference 字符串和 side_effects_isolated 布尔值本身不是身份认证或安全隔离的证明。

## 本地验证与保存

[COMPUTED][HIGH] 从挂载包恢复代码，并按连接器返回的 blob 校验当前 Gate、Shared Dispatch 及对应测试。原有 n8n seam 测试 72/72 通过；新增一个组合检查后，完整 tests/n8n/*.test.cjs 为 73 tests / 73 pass / 0 fail。组合检查运行真实 Mapper/Gate 函数体，验证原输入不变、历史 false 不变、引用保留、成功路径，以及错语言/缺决定的拒绝行为。

[KNOWN][HIGH] 本轮不是业务代码 RED→GREEN 修复；既有实现无需修改。只在 n8n-v3-handoff-20261003 分支新增上述测试/样本文件和本检查点，不合并 main，不保存凭据、resume token、原始运行栈或完整工作流。

[KNOWN][HIGH] 一次完整仓库克隆仍失败：Could not resolve host: github.com。已运行上述 n8n seam 集合，未运行其他仓库测试或 CI；本轮为自审，没有独立 reviewer。测试日志只留本地 .local，不提交 Git。

## 下一环节

[INFERRED][HIGH] 下一单元改为中文新闻稿的一次真实模型调用：使用完整研究材料、明确本次局测范围、仅接中文撰稿路径，正文后停止。不能将本轮缩减样本或归档 reference 当作新调用的正式批准。正式母入口的调用决定来源、语言任务配置、父子版本及发布仍需独立集成验证。
