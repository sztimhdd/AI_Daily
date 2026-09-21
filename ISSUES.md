# LCW — 问题索引与逐项提示词评审台账

更新日期：2026-09-20（America/Halifax）  
范围：新版 n8n Long-Content-Writing（LCW）的提示词、数据交接与交付边界。  
当前阶段：第 01 项 topic_intent v1 已批准、未应用；当前会话未暴露 n8n MCP 工具，单元测试未执行；其余提示词继续逐项评审。

## 0. 文件性质与变更边界

[KNOWN] 本文件为本次新建的问题索引。读取 `sztimhdd/AI_Daily` 默认分支根目录的 `ISSUES.md` 返回 404；未取得可供合并的既有同名台账，因此不声称已导入其历史条目。这里记录的是本会话提供的审计材料，不是重新运行生产系统得出的新验收结果。

[KNOWN] 初始授权是记录问题并与编辑按 LCW 主线逐个评审提示词，不是批量部署此前优化包。后续用户已确认第 01 项 `topic_intent` 候选 v1，并请求通过 n8n MCP 修改及测试该单元；授权不扩展到其他提示词、全篇流程或发布。

[INFERRED] 本文件只作问题索引及评审进度记录，不替代仓库 `.scratch/<feature>/issues/<NN>-<slug>.md` 的独立实施票据。后续实施按仓库约定拆票；不改写 Codex-native 流程的既有定义，不修改只读历史工作流 JSON，不改变调度、人审渠道、研究车道、模型路由或人工发布边界。

## 1. 证据范围

[KNOWN] 基线来自本会话的 `Long-Content-Writing 提示词群：审计、重构规格与完整原文包`，以及 2026-09-20 形成的 `LCW-v2-review-20260920` 评审包。该评审记录了三条工作流的读取和历史执行 150（中文）、151（英文）；两次子执行来自测试父执行 146，不是公开发表文章的证明。

| 工作流 | 审计记录的版本标识 |
| --- | --- |
| [KNOWN] Long-Content-Writing | `6dfd3ccb-184e-4862-bdef-533695b484a0` |
| [KNOWN] [Atomic] Researcher_Skill | `761b6b75-ba30-43b9-8f8a-c335928bbb7a` |
| [KNOWN] [Atomic] Universal Draft Writing | `a69515a0-5dad-4ae4-a981-ce38eab504d9` |

[KNOWN] 审计包内部证据索引为 `evidence/findings.json` 的 E01–E15。包和原始回放不在本次 Git 提交中；本文件仅保留脱敏摘要，不包含凭据、上传删除链接、收件地址或原始模型日志。原始材料中的新闻陈述未在本轮重新对外核实。

[COMPUTED] 本次对收到的交付文件计算 SHA-256，用于识别材料版本：

```text
LCW-v2-review-20260920.zip
2908e32b4095fe59ac88acf283e09dee97b4e0fe10da90c297ba4861ffbd43c7
LCW-v2-review-20260920.md
b1311682e17fda1ec05e70bed849db057dafa21b531d0853f4738b2ea2c5300a
LCW-v2-prompts-20260920.md
6597efc109d30de56fd93fd486985f6c0b31d2f90b80cfaed551644959387048
```

[KNOWN] 原评审包报告了本地 4 类旧缺陷复现、8 份 Schema 定义检查和 10 个合成断言。它们不证明新提示词的成稿质量、线上节点兼容性或后半程交接已通过；本次文档提交没有重跑这些测试。历史 first-half 13/13 也不是本次结果。

## 2. 状态约定

[INFERRED] 以下仅是本索引的修复/评审进度，不是工作流引擎状态，也不是独立实施票据的 triage 标签：

- `OPEN`：有审计记录或已识别风险，尚未验证修复。
- `REVIEWING`：正在与编辑审阅候选方案，不能视为已批准。
- `APPROVED_NOT_APPLIED`：对应提示词已获明确确认，尚未应用。
- `APPLIED_NOT_VERIFIED`：已应用，但相应交接验收未完成。
- `VERIFIED`：有具体变更、测试对象、测试方法与结果；不能只依据引擎 success 或模型自报完成。

[INFERRED] 优先级是本轮提出的处理顺序：P0 为错误正文/状态放行与事实污染；P1 为其余编辑合同和资产可靠性问题；安全事项单独处理。优先级不代表已证明每条风险都发生过线上副作用。

## 3. 问题索引

| ID | 优先级 / 状态 | 位置 | 审计依据与修复验收目标 |
| --- | --- | --- | --- |
| LCW-001 | P0 / OPEN | `Code in JavaScript4/5`、`output_extractor`、出口 | [KNOWN] E01/E02/E04：执行 151 的分析及文本工具调用经 raw fallback 进入正文，末端仍含研究任务。 [INFERRED] 原始响应仅进诊断；缺失或不完整文章、待研究状态不得进入配图和“稿件就绪”。半篇正文同样拒收。 |
| LCW-002 | P0 / OPEN | 两个 `First Draft Writer` | [KNOWN] E01：提示词要求搜索，但执行 151 的真实工具调用计数为 0。 [INFERRED] Writer 只消费已审核材料；缺口返回结构化 `research_return`，不得把文本形式的调用当真实搜证。 |
| LCW-003 | P0 / REVIEWING | `Set Discovery Params1`、Narrative、Task Master、Writer、`Parse & Fan-out Tasks` | [KNOWN] 原审计附录及 E09：预设冲突、历史专题示例和代码内旧人设会继续塑造文章。 [INFERRED] 将分析维度改为调查问题，不预设厂商动机、丑闻或固定 CTO 结论；缺字段不能注入旧人格。 [KNOWN] 当前仅入口 `topic_intent` v1 已批准、未应用；其余字段未获批准，不能关闭整条问题。 |
| LCW-004 | P0 / OPEN | `Normalize Inputs`、`Post-Router Relational`、`Parse Selection1`、`Parse Editor Feedback`、`Merge Brief` | [KNOWN] E14：白名单及拼接式交接未保留完整结构化意图。 [INFERRED] 保留编辑原话、所选叙事、来源与版本；事实/来源观点/编辑推断/未知可区分。补证推翻核心前提须重新确认，不能以主编选择压过证据。 |
| LCW-005 | P0 / OPEN | `Prepare Persistence Data` → `Gateway Output Contract` | [KNOWN] E10：解析异常原文仍可能被包装成 `research_done`。 [INFERRED] 不以 `PARSE_ERROR` 替换正常业务 ID；错误原文进诊断，空证据或无效报告显式失败/待研究。 |
| LCW-006 | P0 / OPEN | 研究指令、补证、叙事与事实使用 | [KNOWN] E07：测试备注进入编辑指令，同名商业产品的行为被用于强化目标产品缺陷判断。 [INFERRED] 控制备注与编辑要求分离；实体相关性独立校验；类比不能充当目标系统实现或故障证据。 |
| LCW-007 | P0 / OPEN | 数字、时间、比较、图中文字 | [KNOWN] E05/E08：中文稿误述月份跨度，图片计划把缺失指标写成零。 [INFERRED] 数字保留单位、时间窗和比较基准；未知为 null；“材料未找到”不得升级成“没有”“为零”或“刻意隐瞒”。 |
| LCW-008 | P0 / OPEN | `Code in JavaScript1`、引用渲染 | [KNOWN] E06：代码会在加粗符号内部插空格，并包含删除编号引用的规则；执行 150 证实前者，不据此声称该次实际丢过编号引用。 [INFERRED] 删除破坏性全局替换；正文、代码块、数组、链接与引用分别验证。 |
| LCW-009 | P1 / OPEN | 两个 Writer、`Final Editor1`、`去AI味` | [KNOWN] E05 及附录：出现无输入依据的作者采访口吻，后续又以“初稿完美”为前提做排版。 [INFERRED] 保留有依据的判断与自然声线；不虚构亲测/采访；复核数字、日期、归因及证据是否支持措辞，不只加粗或加冷嘲。 |
| LCW-010 | P0 / OPEN | `Image Adder`、配图 parser | [KNOWN] E03：配图节点替分析稿补出标题、导语、转场和结尾。 [INFERRED] 冻结成稿后只输出视觉计划及位置；不得返回改写全文。caption 解释关系，alt 描述画面，生成图不冒充来源截图。 |
| LCW-011 | P1 / OPEN | 配图计划 → Split Out / Loop | [KNOWN] 原审计记录过空数组令语言支路终止；当前最小项数限制并非零生图旁路。 [INFERRED] 允许仅封面；来源封面可令生成任务数为零，但文章仍须交付。非必要图片失败不得丢失正文。 |
| LCW-012 | P1 / OPEN | `Generate an image`、`Generate URLs1`、`Aggregate1` | [KNOWN] E11：按数组位置回接资产，URL 字段不统一；请求尺寸与回放上传元数据并不相同。 [INFERRED] 按稳定 ID 关联，统一资产字段并检查实际尺寸；不得仅凭请求参数断言图片比例。覆盖乱序、缺图、重复 ID。 |
| LCW-013 | P0 / OPEN | `Final Editor (Universal)`、kit、出口 | [KNOWN] 原审计：最终节点兼任全文改写、组装和分发；回放 kit 含制作说明或未落实的链接措辞。 [INFERRED] 组装交代码，模型只写 kit；来源、图片插入之外的正文保持不变；无实际发布链接时保留 `link_pending`。 |
| LCW-014 | P0 / OPEN | `Close Ledger (Published)`、`Notify: Drafts Ready` | [KNOWN] E12：写 published 的节点仍在禁用发布节点下游。仅记录静态路径风险，未确认一次真实误写事件。 [INFERRED] 区分执行、编辑、发布状态；人工发布前不能写 published；单语成功可交付但不得冒称双语完成。 |
| LCW-015 | 安全 / OPEN | 图片上传配置 | [KNOWN] E13：上传 token 位于节点参数；值不进入本台账。 [INFERRED] 在单独授权的安全变更中凭据化并轮换，不与提示词评审混为隐式改动。 |

## 4. 已有修补与判断修正：不得误报

[KNOWN] 原审计记录 `brief_content` 曾被 ledger 主通路写入丢失，后来改成旁支；旧提取器的“空文”也加过 raw fallback。这些是历史修补，不能据此关闭 LCW-001 或 LCW-004：raw fallback 本身又形成了错误正文放行路径。

[KNOWN] E15 显示 Writer 入口已有 `brief_content` → `drive_markdown_content` 的显式桥接。字段名不同不等于当前必然 undefined；需要在真正边界检验非空与一致性，不能重复报告一个未证实的空值故障。

[KNOWN] 审计记录的图片请求体为 `1024x1024`，但执行 151 上传元数据含 `1672×941`、`941×1672`。不能声称所有图片实际都是方图；本轮也没有像素级画面验收。

## 5. 按 LCW 主线逐个评审

[KNOWN] 用户要求：先记录问题，再沿实际 LCW 主线逐个修改和优化提示词；不是一次批准整包。

[INFERRED] 审阅顺序如下。一个节点有多个提示词字段时，分别评审；进入子工作流时按其实际连接展开，不按文件附录的排列顺序。两个语言分支是并列职责，不互译。

| 顺序 | 主线位置 | 待审内容 | 评审进度 |
| --- | --- | --- | --- |
| 01 | `Set Discovery Params1` | `topic_intent`：发现什么值得继续研究的事件 | APPROVED_NOT_APPLIED；v1 已确认，当前 MCP 工具不可调用；测试未执行 |
| 02 | `Set Discovery Params1` | `triage_prompt`：怎样筛选并呈现候选 | 未开始 |
| 03 | `Topic Discovery` → Topic Survey | 实际子流程中的提示词及与入口的优先级；先重新读取，不猜节点 | 未开始 |
| 04 | 选题人审 → `Parse Selection1` | 所选事件、编辑原话及初次研究指令 | 未开始 |
| 05 | `Initial Research Phase` → Researcher | 路由提示词、任务输入、研究综合提示词分别审阅 | 未开始 |
| 06 | `Brief Data Extraction` → `Narrative Agent` | 证据条件化的叙事候选与现有二选项界面适配 | 未开始 |
| 07 | 叙事人审 → `Parse Editor Feedback` → 补证 | 定向补证要求，禁止默认寻找支持既定指控的“弹药” | 未开始 |
| 08 | `Merge Brief` → `Task Master Agent1` | 只把已选叙事转成双语写作 brief，不另起论点 | 未开始 |
| 09 | `Parse & Fan-out Tasks` | 清除代码字符串中的旧编辑人设和假兜底 | 未开始 |
| 10 | 中文/英文 Writer | 每个分支的 System 和 Task 分别审阅；共享事实边界与输出合同 | 未开始 |
| 11 | 中文/英文编辑复核 | 证据、声线、完整性与引用；不以排版代替质量验收 | 未开始 |
| 12 | Visual Director | System、Task、视觉功能和计划合同分别审阅 | 未开始 |
| 13 | 确定性组装 → Distribution | 组装权归代码；最终模型仅写 kit | 未开始 |
| 14 | 通知与状态出口 | 仅交付真实完成的稿件；继续人工发布 | 未开始 |

[INFERRED] 每个提示词都按相同方式讨论：当前职责及原文问题 → 保留/删除原则 → 一份候选替换文本 → 与相邻字段、parser 的依赖 → 编辑反馈。审阅通过不自动等于部署；接口格式变化须与接收代码成组验证，不能只替换半条链。

### 当前游标：01 / `Set Discovery Params1.topic_intent` — 已批准，待应用及测试

[KNOWN] 2026-09-20 审计记录的入口使用 `timeframe=72h`、`target_count=5`、`source_lane=auto`。早期规格中的“三个主题”不作为本次偷偷改发现条数的依据。

[KNOWN] 用户已确认上一轮展示的 `topic_intent` 候选替换稿 v1：保留读者价值、信息增量与十个可选调查视角，不预设负面结论；容纳新能力、实际改进及有证据的问题；区分官方发布、独立验证、社区材料及未知项。仅该字段获准修改，`triage_prompt` 和其他字段仍待审。

[INFERRED] 候选允许表达“最多返回目标数量，不为凑数虚构”；但实际启用少于五条的输出前，必须同步修复固定索引访问 0–4 的选题邮件/表单适配。相关接收逻辑未改之前，不把该文本称为可直接部署的无依赖替换。

[KNOWN] 当前没有该提示词已写入线上工作流或通过单元测试的证据。不得将本次 GitHub 台账写入等同于 n8n 提示词更新。

## 6. 下一次关闭问题需要的证据

[INFERRED] 关闭条目须记录：批准的提示词版本、受影响节点/字段、实际应用版本、对应交接测试以及未测边界。优先覆盖：仅分析的失败输出、半篇正文、普通产品发布、标题级社区材料、同名不同实体、未知数值、编辑原话保真、仅封面且零生图任务、资产乱序及人工发布状态。

[KNOWN] 本次补充授权仅覆盖第 01 项的修改和隔离单元测试，不含全篇 E2E、邮件通知、账本写入、正文/图片生成或发布。

[INFERRED] 测试备注、来源内容与系统指令必须隔离。历史绿色执行记录、静态 Schema 检查和模型声称“完成”都不能单独关闭编辑质量问题。

## Comments

### 2026-09-20 — 记录审计，开始逐项评审

[KNOWN] 本次仅新增本索引；未提交此前候选提示词包，未改线上工作流，未运行新的文章/配图/发布流程。当前评审停在主线第 01 项，下一项为同节点的 `triage_prompt`。

### 2026-09-20 — 用户批准第 01 项，MCP 修改与测试被当前工具可用性阻塞

[KNOWN] 用户原话：

> 我认同 你是否可以通过n8n mcp完成修改和这一个单元的测试？

[KNOWN] 实际能力探测：`api_tool.list_resources(paths=["n8n"])` 返回该路径下没有工具；`Plugin_Management.search_plugins(query="n8n")` 返回空列表。本结论仅针对当前这一轮暴露的工具，不能推断用户实例没有 MCP、未安装应用、服务宕机或账号缺少写权限。此前会话中的读取成功也不能证明当前有可调用写入工具。

[KNOWN] 本次没有执行 n8n 工作流读写、执行或发布；没有创建测试工作流或产生新的执行 ID。状态保持 `APPROVED_NOT_APPLIED`，测试记录为 `NOT_RUN`，阻塞原因为 `MCP_TOOL_UNAVAILABLE_IN_CURRENT_TURN`。

[INFERRED] 连接可调用后的拟定单元范围（尚未执行）：

1. **变更核验**：重新读取目标工作流和版本；仅替换 `Set Discovery Params1` 中名称为 `topic_intent` 的 assignment，值使用用户已批准 v1。保留其他 assignment、节点、连线、凭据、调度及发布状态。保存前后版本与差异，回读验证。版本发生冲突时不覆盖他人修改。
2. **字段/传递单测**：在不连接生产后续路径的独立测试环境执行参数节点，检查提示词逐字一致，`timeframe`、`target_count`、`source_lane` 及原有输入透传行为保持不变。测试只证明字段设置与交接，不证明模型选题质量。
3. **最小模型行为测试**：先读取实际消费 `topic_intent` 的下游节点，在隔离副本中用固定资料测试普通正面发布、真实问题、旧闻重发、同事件重复报道、只有标题的社区材料、未知指标和不足五条等情况。保留原模型和其余提示词，核实模型实际收到该字段；不另造一个理想化模型调用替代真实消费路径。未批准的 `triage_prompt` 如导致冲突，记录失败和依赖，不私自修改它来让测试变绿。

[INFERRED] 如果工具不支持安全的局部执行，应使用只含必要节点的独立测试工作流；不能触发生产 webhook 再依靠停在后续节点来冒充单元测试。若也没有创建隔离测试的能力，则保持测试阻塞。

[INFERRED] 在筛选提示词冲突和候选不足五条的接收边界修复前，只验证草稿或隔离副本，不自动提升为新的定时生产发布版本。最终报告需分别给出配置变更、字段单测、模型行为测试和生产生效状态；尚未执行的测试不能标 PASS。
