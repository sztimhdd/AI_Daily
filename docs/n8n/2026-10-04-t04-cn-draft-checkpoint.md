# T04 中文初稿检查点 — 真实产出，内容验收未通过

## 状态

[KNOWN][HIGH] 2026-10-04，本单元已经取得两次真实中文模型输出，但两版均未通过内容验收。两次失败后停止生成，未进入审稿、英文、图片或发布。执行计划见 `writing-mvp-execution-plan.md`。

[KNOWN][HIGH] 本轮最终工作流 `nHxILnDVz541Cu5P` 草稿为 `33f58d70-6b60-4fc8-b98f-32ce2aa73d73`，77 节点，active=false，activeVersionId=null。相对起点 `ee17d426-9bd3-4325-bb3c-8527c93a808c`，原生 diff 只有一条连接：`V2 Language Switch` 的中文输出 1 → `V2 CN Lead Writer`。没有节点增删、节点参数差异或其他连线变化。中文 Writer 后无下游。

## 输入选择

[KNOWN][HIGH] 使用历史 557 的写作材料而非 587/588 的两来源简化样本。`fixtures/writer-news-557.cjs` 复用 `handoff.cjs` 并补回写作所需来源说明、支持摘录、引语上下文、报道路径及未决问题。数据包含 8 来源（2 个不具事实使用资格）、10 条断言、23 条支持摘录、5 条引语（选中 3 条）、6 个报道段落任务、1 个未决问题。

[KNOWN][HIGH] 这是历史衍生的写作材料回放，不是完整原执行字节导出，不是当前新闻核验，也不是正式人工审批。原历史审计包仍留在 557；原生 Writer 局测使用明确的新 controlled_test envelope，未给 557 补造 selected receipt。仓库生成器与部署的紧凑脚本是等价写作输入的两种表示，不宣称脚本逐字相同。

## 原生执行

| 执行 | 输入/实际行为 | 验收 |
|---|---|---|
| [KNOWN][HIGH] [589](https://ohca.ddns.net/workflow/nHxILnDVz541Cu5P/executions/589) | 临时输入正确，原 Mapper 却输出旧的另一篇稿件；runData 中明确存在该节点旧 pinData。Gate 报 prepared work order missing。 | 暴露原手动入口阻塞；未调用模型。 |
| [KNOWN][HIGH] [590](https://ohca.ddns.net/workflow/nHxILnDVz541Cu5P/executions/590) | 临时节点执行与仓库相同的 Mapper 代码，再走原 Gate/Switch；最后节点 Switch，无 Writer。 | 中文接线前基线；不是成稿成功。 |
| [KNOWN][HIGH] [591](https://ohca.ddns.net/workflow/nHxILnDVz541Cu5P/executions/591) | 中文接线后，以合成负例删除调用决定；外部服务固定输出，逻辑正常运行。 | 预期 explicit invocation decision missing；无 Writer。 |
| [KNOWN][HIGH] [592](https://ohca.ddns.net/workflow/nHxILnDVz541Cu5P/executions/592) | 完整材料经临时 Mapper、原 Gate/Switch 进入现有 CN Writer；manual，真实模型输出。 | 调用成功；内容 FAIL。 |
| [KNOWN][HIGH] [593](https://ohca.ddns.net/workflow/nHxILnDVz541Cu5P/executions/593) | 同一材料、同一模型，只增加四条短提示规则后重跑。 | 调用成功；内容仍 FAIL。 |

[KNOWN][HIGH] 592/593 的 Writer 和模型均有真实运行记录，结束原因为 stop，未以 pin 固定它们的结果；两个执行均在中文 Writer 结束。原 Gate 没有绕开或放宽。现有模型 `deepseek/deepseek-flash`、温度 0.5、凭据和系统提示词未变。

## 内容问题（相对输入材料，不是外部新闻核查）

[KNOWN][HIGH] 592：从来源 URL 推导报道日，从来源标题引入未进入 proposition 的交易金额；把两次已给日期写成不准确的“两个月后”；标题把一种提供商路由泛化为所有路由；把 source_context 拼入直接引语；结尾又把应用自有账户功能归入另一服务的集成功能。

[KNOWN][HIGH] 593：部分元数据扩写消失，但出现“还没有被任何一方测量过”。输入只说未提供/未独立验证测量结果，并不支持“任何一方都没有做过”。结尾仍混淆应用自身账户功能与外部服务集成；一处直接引语还把弯撇号改成直撇号，未满足逐字保护。主要否决依据是事实范围和归属，不只是标点。

[INFERRED][HIGH] 因此不能因正文完整或排版正确而放行。四条提示词补丁没有证明解决问题，已回退到原文本；不进行第三次随机抽样，也不换模型/供应商掩盖失败。

## 测试和保存

[COMPUTED][HIGH] 本地最终 `node --test tests/n8n/*.test.cjs`：74 tests / 74 pass / 0 fail。该集合验证准备、映射、Gate、完整材料和负例，不意味着实际文章正确。

[COMPUTED][HIGH] 两版本地 Markdown（含末尾换行）分别为 3771 / 3382 字符，包含 5 / 3 个不同来源链接；结构检查通过。`--regressions` 对两版均返回 exit 1：592 首先命中来源日期扩写，593 首先命中引语原文不一致。上述更广泛的范围/归属问题来自逐篇阅读，不冒充正则能完成语义核验。

```sh
node --test tests/n8n/*.test.cjs
node tests/n8n/cn-writer-native.test.cjs --payload '<fresh user permission reference>'
node tests/n8n/cn-writer-native.test.cjs --native-payload '<fresh user permission reference>'
node tests/n8n/cn-writer-native.test.cjs --probe '<fresh user permission reference>'
node tests/n8n/cn-writer-native.test.cjs --article .local/t04/stripe-openrouter-cn-run-592.md
node tests/n8n/cn-writer-native.test.cjs --regressions .local/t04/stripe-openrouter-cn-run-592.md
node tests/n8n/cn-writer-native.test.cjs --regressions .local/t04/stripe-openrouter-cn-run-593.md
```

[KNOWN][HIGH] 最后三条需要本地候选正文；正文不提交 Git，故仓库测试不依赖这些文件。CLI 本身没有网络调用。reference 文本与 side_effects_isolated 字段不是实际权限或隔离的证明；原生回放前仍须核对当前批准、工作流版本、真实接线和 pin 状态。

## 版本与回退

| 版本 | 内容 |
|---|---|
| [KNOWN][HIGH] `ee17d426-9bd3-4325-bb3c-8527c93a808c` | 本轮起点/恢复点。 |
| [KNOWN][HIGH] `24037c70-9a0f-4c6a-b3da-d1b7bd9eee99` | 临时 Manual 和完整 Payload。 |
| [KNOWN][HIGH] `d1dfe393-76d1-4f2e-be26-800404200b42` | 临时同代码 Mapper，隔离旧 pin。 |
| [KNOWN][HIGH] `9b28e1bd-519b-4f28-a254-1cd9ea5447c1` | 接通中文输出。 |
| [KNOWN][HIGH] `c54c78c2-25ef-44bd-8b7e-12fbb0a43069` | 未通过内容验证的提示词试验。 |
| [KNOWN][HIGH] `33f58d70-6b60-4fc8-b98f-32ce2aa73d73` | 提示词回退、三个临时节点删除，仅留中文连接。 |

[KNOWN][HIGH] 仓库试验提示词保存在 commit `528b265dea175d8773e60b2e111ef19def9013cb` 的历史中；`bc1bba857486c70c539b07eed4b9de1a380e6475` 恢复原提示词。当前 `src/n8n/cn-lead-writer.prompt.txt` 对应回退后的 live 文本，不代表修复成功。

[KNOWN][HIGH] 母流程和 Shared Dispatch 未改；英文、审稿、图片、上传、邮件、ledger、发布未执行。没有生产启用、凭据变更或正式审批测试。

## 未解决事项 / 下一环节

[KNOWN][HIGH] 原 `Writer Context Builder` 的旧 saved pinData 尚未清除。当前可用更新动作没有显式 unpin 字段；不能因隔离副本成功就声明原手动入口修复。副本已删除，没有留下平行生产实现。

[INFERRED][HIGH] 下一环节先确认受支持的 unpin 操作并验证原材料身份，再据两版保存失败稿检查事实范围/归属的最小修复。实际正文通过以前不扩展后续模块。恢复任何历史版本前须再次回读当前版本，避免覆盖他人变更。

[KNOWN][HIGH] 完整仓库 clone 因 DNS 错误失败；本轮只对恢复的 n8n 接口集合运行测试，未运行其他仓库测试或 CI，也没有独立 reviewer。原始运行栈、凭据与 resume token 不保存至仓库或交付包。两版文章仅作为未通过候选供审阅，不作为新闻发布成品。
