# D — 母流程内 News / Deep 双语起草：复核检查点

[KNOWN][HIGH] 2026-10-06。用户本轮授权只完成一个大环节后停下。本次 fresh-read 时 D 的实现和执行 747–750 已存在；因此本次复核现有草稿、读取实际输出并保存本检查点，没有重复搭建、再次调用模型或推进 E。历史主计划在本次读取的仓库提交 23f79870714aa91346dde20812603548117c980b 仍把 D 列为未完成；D 的最新状态以本检查点和实际 n8n 草稿为准。本文不是全工作流导出或全仓测试报告。

## 当前结果与范围

[KNOWN][HIGH] D 的模式分流、双语起草、非空结构检查及单语失败保留已具备原生局部执行证据。两种模式的中英文实际草稿已阅读。正文仍需下一环节的一次轻编辑；不能把 drafts_ready 当成出版质量通过。

[KNOWN][HIGH] 工作流 Long-Content-Writing：xR7fM1ZhxlMTUy0L；本次读到 53 个节点，草稿版本 f9e054b5-62d8-4a7b-bcb9-0ace1ed8dd85。生产 activeVersionId 仍为 c94debcc-2fe0-438a-a3df-a1d699740c99，不是新草稿。当前真实选题邮件及 Deep Narrative 邮件的输入连接仍隔离，根入口在 Topic Discovery 返回处结束；不得把局部写作测试称为已经启用每日完整出稿。

## 本环节的实际主线

```text
Attach Targeted Browser Sources
  -> Draft Languages (zh-CN/zhihu_longform + en-US/linkedin_article)
  -> Draft Language Loop (batchSize=1)
       loop -> Writer Mode
                 news          -> News Writer
                 deep_analysis -> Deep Writer
               -> Capture Mode Draft
               -> loop
       done -> Aggregate Drafts (terminal)
```

[KNOWN][HIGH] 两个 Writer 是母流程中的不同 Agent 节点，不是两个独立工作流。每个节点通过 language 复用中英文；输入来自同一份材料与方向，不把中文文章交给英文节点翻译。Draft Languages 和 Aggregate Drafts 复用原母流程节点位置/身份。输出保留原始材料、初轮/补查信息、用户意见和 Narrative，并在 drafts['zh-CN'] / drafts['en-US'] 保存各自标题、正文与状态。

[KNOWN][HIGH] 本阶段不调用旧 Universal Draft Writing，也不调用 V2 Writer 子流程，因而本段起草不涉及父子工作流草稿版本选择。两种模式共用 Draft Model，当前配置按语言选择 zh 的 deepseek/deepseek-flash 和 en 的 gpt-6-luna；本次未修改模型、供应商或凭据。版本历史声明这些配置沿用原 Writer，本文不把该声明扩展成已重新核对所有旧模型配置。

[KNOWN][HIGH] News Writer 的提示词要求多来源全景新闻，不强制 thesis；Deep Writer 要求保留用户修改后的标题含义、核心判断、叙事顺序与反证。原文直接进入模型，不经过 Work Order、Receipt、Writer Invocation Gate 或新的逐 claim 合同。Capture Mode Draft 的自动检查仅针对 H1、非空正文和标题文字体系，不是全文语言检测、事实审核或文风评分。

## 节点变化与恢复点

[KNOWN][HIGH] 原生 diff：52bcc8e0-414e-4f2e-9d53-af16fca74034 -> f9e054b5-62d8-4a7b-bcb9-0ace1ed8dd85。

- [KNOWN][HIGH] 新增六个节点：Draft Language Loop、Writer Mode、News Writer、Deep Writer、Draft Model、Capture Mode Draft。
- [KNOWN][HIGH] 移除两个旧调用节点：Drafting Phase、Call Universal Draft Writing V2；没有删除所指向的旧子工作流。
- [KNOWN][HIGH] 两个既有节点修改：Prepare Writer Invocation 改为 Draft Languages；Aggregate Drafts 改为收集本地主流程的两稿。

[COMPUTED][HIGH] 节点净增 4，即 49 -> 53；这是起草环节移入母流程的局部变化，不是宣称整个项目节点总数减少。

[KNOWN][HIGH] 永久 D 补丁版本为 5d701ed6-216e-478a-a872-7f839da9898a。本次重新比较该版本与最终清理版 f9e054b5，nodesAdded / nodesRemoved / nodesModified / connectionsAdded / connectionsRemoved 全为空。当前完整图无 TEMP D 节点，Aggregate Drafts 没有下游连接。旧邮件和 published ledger 节点仍在画布上但没有进入本段可达路径。

## 实际执行结果

| 执行 | 输入性质 | 实际输出 | 证明边界 |
|---|---|---|---|
| [KNOWN][HIGH] 747 | News 合成材料，首语种原生故障注入 | 中文 failed，英文合成稿 completed，drafts_partial，original_context_preserved=true，末端 passed=true | 失败传输与兄弟版本保留；不是模型故障率测试。 |
| [KNOWN][HIGH] 748 | Deep 合成 Narrative，中文空输出 | 中文 failed，英文合成稿 completed，原材料及修改意见保留，末端 passed=true | 空稿拒绝与保留；不是正式人工审批。 |
| [KNOWN][HIGH] 749 | 既有研究的缩减原文回放，News 方向，core_judgment=null | 两种语言 completed，Aggregate 输出 drafts_ready | News 节点通过双语局部起草，不是重新研究或全流程。 |
| [KNOWN][HIGH] 750 | 同题原文回放，明确标记的合成人工修改 Narrative | 两种语言 completed，末端 passed=true，original_context_preserved=true | Deep 保留测试 Narrative 的接口与实际文本表现，不冒充用户真的审批该篇。 |

[KNOWN][HIGH] 749/750 使用执行 715/716/743 衍生的缩减原文材料；共三个材料条目，其中一个只是同一位工程师说明的转载，另一个帮助页是测试摘录。未在本次重新核实新闻，也没有把转载视为独立实测或第二个独立观点。原生输出包含真实模型生成正文；747/748 则是合成传输测试。所有返回均为 NOT_PUBLISHED。

[KNOWN][HIGH] 749 中文题为“Cowork 把虚拟机搬上云：合上笔记本，AI 还能继续干活吗？”，英文题为“Cowork is moving its virtual machine to the cloud—but local files still need your desktop app”。750 中文题为“任务搬上云，电脑没有消失”，英文题为“Tasks Move to the Cloud. The Computer Hasn’t Disappeared.”。这些是保存测试产物的标题，不是本次新核实的新闻结论。

## 阅读验收：保留问题，不以绿色节点替代成稿

[INFERRED][HIGH] News 两稿围绕事件、旧版/新版执行位置、文件访问条件、迁移范围与工程师反馈展开，没有被强制写成商业 thesis。但这份缩减样本主要是官方说明及其转载，不能证明“不同独立观点和实际使用报道的新闻广度”已充分验收；后续完整材料 E2E 验收仍需检查这一点。

[INFERRED][HIGH] Deep 两稿保留了测试 Narrative 的“持续执行与本地资源访问是两种依赖”主线，包含无需本机文件时云端仍有价值的反证，没有改写成安全审计或支付商业模式。中文 H1 与测试修改标题一致，英文保持其含义。

[INFERRED][HIGH] 下一次的一次轻编辑需要就地处理：News 中文的“新版把两样东西一起搬走”容易忽略模型推理原先已在云端；末尾“这些说法目前来自哪里”将研究过程写进正文，并把测试材料的摘录状态写得像网站本身不可读；Deep 中文的“照常跑完”“谁在线都无所谓”把执行位置条件说成了结果保证。原样保留自动稿，不人工修完后冒称 Writer 自动通过。

[KNOWN][HIGH] 749/750 四稿有实际来源链接；没有生成 Kit、Caption 或图片。下一环节必须保留正文和来源，不得因轻编辑失败而丢稿。News 的真实新闻图片策略和 Deep 插图策略均仍待 E，不能用旧 V2 配图路径的历史成功替代新母流程验收。

## 本次停止点

[KNOWN][HIGH] 本次只做 D 的实读复核和本检查点保存，没有新的 n8n 写入或执行；没有发送邮件、浏览器发布、写 published 状态、启用生产或合并 main。没有运行新的本地测试，因此不把版本历史里的 15 项本地测试记成本次复跑成绩。复核是作者自审，没有第二名独立审查者。

[INFERRED][HIGH] 下一大环节：E 中的一次轻编辑与失败保稿，按用户要求另起一轮。配图及 Kit 不在本次处理。本检查点不声称 C2/C3 的所有代码已经同步到仓库，也不声称整条定时到最终草稿的 F 验收通过。
