# AI Daily 精简重构：A 基线与续接点

[KNOWN][HIGH] 用户本轮重构要求取代旧 MVP 的多工单、重复授权、News/Deep 双提案和默认多轮编辑设计。此文件保存的是 live 版本定位与调用/隔离核查，不是含密钥的完整工作流导出。工作分支 n8n-v3-handoff-20261003；读取时 HEAD 为 9ac3600322cfb57a8aecb09a76f63af6d0ae8c61。时间按 America/Halifax，服务执行记录的 UTC 日期已跨入 2026-10-06。

## 新产品主线

[KNOWN][HIGH] 每日定时采集 → 最多5个真实题目供选（不足明确说明）→ 人选1题及补充方向 → 初轮研究 → 一次 Deep 适用性判断。News 自动确定报道方向、不做 Narrative 审批；Deep 提出标题、核心判断和大纲，由用户确认或修改一次。两条分支均必须经过定向补查规划与补充取材，再按模式生成中文知乎稿和英文 LinkedIn 稿 → 一次轻编辑 → 成稿后配图 → 返回图文草稿。Deep 正常路径不重复审批。

[KNOWN][HIGH] 保留两个模式主笔 News Writer / Deep Writer，各自通过 language 参数复用，不能用两套语言流程替代模式区分。News 重事件、背景、实际使用、人物原话和不同观点，不强制 thesis；Deep 按用户 Narrative 推进杂志式分析。News 优先真实新闻/产品/Demo/评测/社区图片，禁止伪造界面和帖子；Deep 优先解释机制与叙事的插图，真实数字图表使用已取得数据。图片无配额，失败仍完整返文，来源与图注保留。Kit 在主线重构后收尾，不默认增加正文改写轮次。

[KNOWN][HIGH] 授权覆盖 draft 修改、必要局部测试和所需图片生成上传；不覆盖真实邮件、公开发布或 production workflow publish。不得靠 disabled 节点隔离发布。两次修复同一问题仍失败就停止分支；不静默更换模型、供应商或访问路线。

## Fresh-read 定位（本轮已读取全部10个完整图）

| 对象 | workflow ID | draft version | active version |
|---|---|---|---|
| [KNOWN][HIGH] Mother，46节点 | xR7fM1ZhxlMTUy0L | e34aef91-eab3-4f25-bc2e-f853d4c920ba | c94debcc-2fe0-438a-a3df-a1d699740c99 |
| [KNOWN][HIGH] 当前 Writer V2，81节点 | nHxILnDVz541Cu5P | a89919a4-b110-4236-9398-ab716c965e0a | 无 |
| [KNOWN][HIGH] Topic Survey，21节点 | Tx1BkAxjods79f0z | 5128a885-58a3-4616-91c3-84f29805eb37 | 9e03561c-2703-41dc-976e-2fe075cbef07 |
| [KNOWN][HIGH] Researcher，25节点 | Xn3xoX9OVxCliOs4 | f2d47bfe-fed9-4366-94e7-fd03023c8cb2 | 6ec1fe2f-5eb1-41e0-97fd-e08e20c22232 |
| [KNOWN][HIGH] Browser，10节点 | lUzGBnb9I0T0WuLw | 9d4b5ad7-17b3-47ab-ac37-864c0d6fecdc | 0875e663-3bc2-449c-aeff-57724fc862f8 |
| [KNOWN][HIGH] News Editor，7节点 | erbgzbMR5oNmEX2S | 3aca5c56-fced-41e7-8a28-31ba781f5e52 | 无 |
| [KNOWN][HIGH] Deep Editor，8节点 | sXFTgr72EKZUUlWL | 9e7efcb7-933e-45d5-ba96-33878fc320e9 | 无 |
| [KNOWN][HIGH] Story Approval，5节点 | gFssJK9jikxTAtYY | 11991e30-660a-4f9b-93bf-07c57843f5ac | 无 |
| [KNOWN][HIGH] Shared Dispatch，8节点 | qAfs9BDFbdBotgaB | 6125e9ed-2270-42c4-b601-8a245adb7455 | 无 |
| [KNOWN][HIGH] 旧 Writer，仅查依赖，31节点 | 65KUDdo1G6k3VysU | 42ab4ad9-1cf9-4622-8256-ea679a1b0ae9 | bb6e38df-2a30-41fa-add2-de37fa254855 |

[KNOWN][HIGH] 原始图含凭据引用，旧 Writer 还含静态认证值，因此不将其原样提交公开仓库，也不在此复述。恢复使用上述原生 versionId；没有修改或轮换凭据。

## 实际可达性与旧调用

[KNOWN][HIGH] Mother draft 的 Schedule Trigger（每天09:00，America/Halifax）及 Manual Webhook → Set Discovery Params1 → Topic Discovery，目前以发现结果为终点。Topic Discovery 调用既有 Topic Survey。HITL: Topic Selection1 无入口连接；Parse Selection1 的原研究出口也已断开。当前 root 可达图没有真实邮件、浏览器写入或 published ledger 动作。

[KNOWN][HIGH] 尚待替换的旧研究/编辑岛：Initial Research Phase 调用 Researcher；Brief Data Extraction 分发 News Editor 和 Deep Editor；二者汇总后调用 Story Approval。旧人工 Narrative 出口经 Shared Dispatch、补查复评和重复 Writer invocation 准备到 V2 Writer。它们仍在画布上，但当前不从定时/手动根入口执行。

[KNOWN][HIGH] 另一个孤立旧岛含 Task Master、Parse & Fanout Tasks、Drafting Phase；后者调用旧 Writer 65K，不是 V2。Prepare Browser Tasks、浏览器发布调用、通知、Close Ledger (Published) 不在草稿根路径。后续按 F 清理，不把画布存在误报为正在执行。

[KNOWN][HIGH] V2 当前单语言主线从触发器经过 Context/Gate，再按语言分到两位主笔及对应编辑，然后共用视觉/上传/组装/Kit。冷读、收敛审核、旧 XML Writer 等是孤立业务支线；其模型连线不是主路径执行证据。后续 D 才把模式主笔迁入主流程并删除重复包装。

## 已发生的中断前工作：本轮重新核对

[KNOWN][HIGH] Mother 历史记录表明 A 与 B1–B3 已在上次中断前保存，而 GitHub 尚未记录。本轮不是从旧 e419a94d 重新开始。Topic Survey 的固定源分配已改为确定性逻辑，保留既有采集和排序；没有材料时跳过排序模型，最多5题，不足给提示。Parse Selection1 返回同一上下文，保留完整 materials 数组、用户原文和原始来源 target_urls，不再制造写作授权包。

[KNOWN][HIGH] 本轮实读 696 的 integrated 子执行697：实际执行终点为草稿专属 TEMP A Version Probe，输出 draft_marker=survey-20261005-A，external_calls=0，parentExecutionId=696。其输出内 execution_mode 字段为 production，但原生执行元数据为 integrated；判断版本依据专属节点/标记，不靠模式字符串。这个结果只证明该次 Survey 子调用命中测试草稿，不推论所有子流程都运行草稿。

[KNOWN][HIGH] 本轮实读 Mother708的 Parse Selection1：38条实际采集材料，5个题目，保留原始出处；测试选择第1题并保留完整测试补充方向，stage=initial_research，publication=NOT_PUBLISHED。其前驱为 TEMP B Selection Reply，最终节点为 TEMP B Selection Assert；这是明确的合成选题答复，不是真实邮件审批，也没有初轮研究。历史临时节点已从当前46节点草稿中清理。

## B 已完成与当前续接点

[KNOWN][HIGH] B 已以执行717关闭：真实Topic Survey、合成选题、公共正文抓取、真实Browser Pilot和同一上下文合并连续完成；失败来源显式保留，publication保持NOT_PUBLISHED。当前Mother draft 9e023eb2-3642-4eff-93b9-3dc3961318b5，49节点；旧activeVersion仍未切换。

[INFERRED][HIGH] C 从初轮研究上下文直接做一次Deep适用性判断：不再并行News/Deep编辑，不默认同时生成两个提案。News确定报道方向后直接进入补查；Deep输出标题、核心判断、叙事大纲并只进行一次人工Narrative确认/修改。两分支随后共享定向补查。


[INFERRED][HIGH] B4 从选题上下文接初轮源文读取，优先复用 Researcher 的原生搜索/提取能力到 Mother，去掉 LLM 固定路由和 dossier 重摘要。保留原始源文、检索错误与图片候选出处，已知登录墙仍用只读 Browser 工具路线；不得默默绕路或把抓取失败的摘要称全文。

[KNOWN][HIGH] A 的读取、版本定位与现有物理隔离已确认；B 的选题部分有708证据，但真实邮件选择往返未测试。B4/C/D/E/F 尚未在新主线上验收。不得称 E2E 完成、不得接通真实邮件来凑连续验收、不得发布旧生产版本以测试草稿。下一次每个完成环节记录独立检查点和真实 execution ID。
