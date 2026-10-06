# 来源 URL 保留与表达强度：759–762 局部修复

[KNOWN][HIGH] 2026-10-06。本轮仅修复来源 URL 丢失及表达强度增强。fresh-read Mother xR7fM1ZhxlMTUy0L、三个目标节点及执行757/758；原配置保存在会话证据包 baseline/target-nodes.json，原生基线为3644e58e-247d-4c8e-82c9-42cd611b4680。原配置保存范围为三个节点完整参数/设置与工作流版本元数据，不是假称全工作流导出。

## 分开裁决

[KNOWN][HIGH] 链接保留逻辑通过本轮局部检查：不再允许“丢一个但还有其他链接”。丢失任何被原有解析器识别的原稿来源URL，返回failed/review_required、明确原因和缺失URL、原始初稿及未经修正的编辑候选。不自动再调模型。

[INFERRED][HIGH] 表达强度尚未完全通过：新合成测试762在通用可能性、倾向、目标和条件性计划上保留了原强度，但英文将一次具体漏检的原因写得比来源更确定。错误始于Deep Writer，Light Editor未纠正。保留原输出并停止，没有第二轮或手改结果。

[KNOWN][HIGH] 本轮检查中原稿始终保留：759–761失败回退原稿，同时保留被拒候选；762正常编辑仍分别保存drafts和preview.draft_markdown。所有publication均NOT_PUBLISHED。

## 永久修改：三个已有节点，三个参数字段

- [KNOWN][HIGH] Capture Light Edit /parameters/jsCode：从“原稿无链接或编辑后至少一个链接”改为removed.length===0，并保留原非空/H1/标题语言及调用错误检查。新增preview.editor_candidate_markdown和preview.editing_error，后者包含reason、message、missing_source_urls；link_changes继续记录before/after/removed。
- [KNOWN][HIGH] Deep Writer /parameters/options/systemMessage：增加一段通用发生概率、适用范围、时间和条件规则，不将可能、倾向、目标、承诺升级为必然或实测，不机械替换can/may/会，不把确定事实全部弱化。
- [KNOWN][HIGH] Light Editor /parameters/options/systemMessage：增加主动逐语义维度对照原材料、将过强表述恢复到支持强度的规则；旧“被删段落的链接可删除”改为保留原稿全部URL，允许集中到文末。

[KNOWN][HIGH] 没有新增任何节点，包括测试节点。无新增审核Agent、来源注册表或状态框架；模型、凭据、分流、一次轻编辑和双语循环均未改变。测试临时借用原有孤立Code节点及手动入口，之后完整恢复。最终57节点，基线到最终原生diff仅上述三个字段；连接增删和节点增删均为空。

[KNOWN][HIGH] URL解析器按本次要求复用原有简单inline HTTP Markdown实现，支持现有[label](URL)形式和将这类链接移至文末。不声称这是覆盖全部Markdown方言、裸URL或复杂括号的通用解析器；URL保留也不证明其事实支持关系。缺失检测不依赖链接数量相等，替换成另一个URL也会失败。

## 先链接回放，无模型

[COMPUTED][HIGH] 本地8项测试：修改前4通过/4失败，修改后及最终复跑8通过/0失败。使用757保存的完整中文编辑前后文本，不是重新生成的近似例子。另覆盖文末搬移、无URL、空稿、错误及部分输出、同数量替换URL、原样通过、错语种标题。不是全仓CI。

[KNOWN][HIGH] 仓库中的source-url-retention.test.cjs使用明确标记的最小同类输入，方便无网络复现；移植版也已运行8通过/0失败。完整757文本回放保存在会话证据包与原生759，不把仓库的最小输入冒称完整757。

| 执行 | 实际输入与输出 |
|---|---|
| [KNOWN][HIGH] 759 | 中文精确回放757：原3URL剩2，tester网址缺失。现返回editing_status=failed，warnings含source_urls_missing_original_retained；editing_error.reason=source_urls_missing，missing_source_urls明确列出https://example.org/fixtures/fixturedesk/tester；article_markdown回到原稿，editor_candidate_markdown保留被拒文本。英文合成对照把全部链接搬到文末，completed。 |
| [KNOWN][HIGH] 760 | 中文原稿无URL，正常编辑通过；英文空返回，invalid_output并保留原稿。 |
| [KNOWN][HIGH] 761 | 中文注入error对象和部分输出，返回model_error及Injected editor-call failure，原稿与部分候选分别保留；英文原样对照通过。 |

[KNOWN][HIGH] 759–761运行实际Capture Light Edit和Aggregate Drafts，无主笔/编辑模型执行；错误对象是控制输入，不冒充真实供应商事故。三次都返回edits_partial，成功语种未被失败语种抹掉。

## 一轮新语义测试：762

[KNOWN][HIGH] 输入是与旧案例不同的虚构档案检索试点：试点公告、索引说明、档案员记录，共三条合成来源。example.org网址只是测试标识，未发起访问。human_instructions为空，未提供light_edit_notes；预期判定单独保存，不在模型输入中。Narrative明确标为合成测试，不冒充真实发布审批。

[KNOWN][HIGH] 762于17:49:19.297至17:50:12.010 UTC执行。实际Deep Writer中英文各一次，Light Editor中英文各一次，共2次主笔和2次编辑；没有二次纠错调用。直接运行母流程节点，没有子工作流版本问题。测试前草稿为d75d8e65-171a-44cc-b07b-abf5100ac6ab。

| 维度 | 原材料 → Writer → Editor |
|---|---|
| [KNOWN][HIGH] 条件与可能性 | 原文“When ink is faint or a scan is skewed, recognition may omit a date; omission is not inevitable.” 中文主笔“当墨迹淡或扫描倾斜时，识别可能漏掉一个日期；但漏掉并非必然。”编辑“墨迹较淡或扫描件倾斜时，识别可能漏掉日期，但并非一定会漏。”英文主笔与编辑均保留may omit及faint/skewed条件。 |
| [KNOWN][HIGH] 倾向与范围 | 原文“Spelling normalization tends to improve matching of place names on typewritten pages.” 两语主笔和编辑均保留倾向/tends和typewritten范围，没有断言手写稿也有同样效果。 |
| [KNOWN][HIGH] 目标与实测 | 原文“Project director Morgan said the project aims to reduce the time spent locating relevant records.” 中文主笔和编辑均写“项目旨在”，英文均写“said the aim is”；没有改成已测出节时。 |
| [KNOWN][HIGH] 时间与条件性计划 | 原文“The project plans a wider rollout in November 2026, subject to agreements with participating archives.” 中文主笔保留“计划，但取决于…协议”，编辑保留“项目计划…但这取决于…达成协议”；英文两稿均保留plans及subject to agreements。 |
| [KNOWN][HIGH] 确定事实 | 12家档案馆、2026年9月24日启动、原始扫描件不变等，仍直接陈述，未被统一加上“可能”。中文保留CSV导出能力；英文编辑删去该枝节，并非弱化成未知能力。 |

### 未通过：具体原因被强化

[KNOWN][HIGH] 记录原文只说：“Search found the target date on 22 pages and missed it on two faint pages.” 索引说明说淡墨或倾斜可能造成遗漏，并没有核定这两页的具体漏检原因。

[KNOWN][HIGH] 英文Writer开头写：“The other two pages were faint enough that the system missed the date—but Rao found both by opening and reading the original scans.” Editor保留“were faint enough that the system missed the date”，只调整了后续标点和措辞。

[INFERRED][HIGH] 这把“这两页较淡且漏检”及“一般情况下淡墨可能导致遗漏”合并成“这两次就是因为淡到足以造成遗漏”。原因可能合理，但并未由记录证实，不能作为已核定原因直述。因此强度验收不全通过，问题定位为Writer新增、Editor未消除。没有修稿、再喂答案或重跑。

[INFERRED][MED] 中文编辑另把“在两页…漏掉日期”简写成“漏掉两页”，有对象范围歧义；保留在原输出，不把该项单独判成全文失败或擅自修正。其他文风问题不在本轮修复范围。

[KNOWN][HIGH] 两语原稿各3个不同来源URL，编辑候选均保留3个，removed=[]。结构/URL门禁返回completed不等于语义通过。完整未修正源输入、主笔、编辑和候选保存在原生执行762；会话证据包另存关键原句对照与人工判定，不假称完整原始执行导出。

## 恢复点与停止状态

[KNOWN][HIGH] 修改前3644e58e-247d-4c8e-82c9-42cd611b4680；代码修复57e35e4c-7ad7-4fca-b25d-5a0f769f3255；链接测试04d4c840-46a4-47ef-b491-2315646708e1，清理1b5a181d-699b-41c1-acef-04cff3b4950a；永久代码+提示词9f8459ff-5bfe-43ae-b591-e707d99da352；语义测试d75d8e65-171a-44cc-b07b-abf5100ac6ab；最终清理3dae201c-7456-478a-ab30-e8492a12e98f。

[KNOWN][HIGH] 永久修复9f8459ff到最终3dae201c原生diff全空。旧生产activeVersionId仍c94debcc-2fe0-438a-a3df-a1d699740c99；没有发布新草稿、发送邮件、调用选题/研究/配图/Kit或变更凭据。母流程仍active=true，不把“新草稿未发布”说成实例没有生产工作流。

[KNOWN][HIGH] 源码映射保存于src/n8n/source-strength-repair.mapping.json；应用顺序在历史D/E1/writing-feedback覆盖之后。完整两个systemMessage存于source-strength.*.system.txt，Capture代码直接更新已有文件。该映射是仓库源码索引，不是新运行时合同。

[KNOWN][HIGH] 本轮停止在“两项修复已落入草稿，链接门禁局部通过，表达强度有明确未通过例”。语义规则只是提示词，不存在确定性语义保证；未新增后置审计来遮盖结果。
