# Narrative Contract（v2026 编译版）

本文件是 04 叙事候选阶段的执行知识，编译自 2026-08 三方独立调研
（docs/research/AI自媒体叙事方法论报告_2026*.md，合并裁决见
docs/research/narrative-survey-merge-notes.md）与 legacy 资产
（REF NarrativeGenerator、LCW Narrative Agent、HITL Narrative Approval）。
运行时只读本文件与 narrative.py 内的编译常量，不直接解析 n8n JSON。

## 核心范式

从「热点 × 叙事模板」改为：

**热点 × 可验证冲突 × 证据资产 × 读者决策。**

叙事候选的任务不是选文风，而是回答：这篇稿子有什么是读者用普通 AI
摘要得不到、又可以亲手核验的。

## 八原型（N1–N8）与触发条件

| key | 原型 | 触发条件（证据资产） |
|---|---|---|
| N1 | first_hand_test 一手实测翻车 | 有可复现实测/实验证据，含失败案例 |
| N2 | contrarian_audit 反共识拆台 | 存在被大量重复的共识命题 + 反证数据 |
| N3 | mechanism_teardown 工程机制拆解 | 有源码/trace/架构级一手材料 |
| N4 | cost_ledger 成本与供应链账本 | 有定价/账单/成本/供应链数据 |
| N5 | workflow_playbook 工作流配方 | 有可复制的多步工作流/组合用法信号 |
| N6 | power_map 生态权力图 | 有人事/组织/资本/控制权变动且可验证 |
| N7 | compliance_risk 政策合规风险 | 有法规原文/官方 guidance/生效日期 |
| N8 | decision_brief 决策快讯 | 至少一条一手事实（兜底原型） |

证据决定叙事：没有对应证据资产的原型不允许被选择；全部不满足时
按 KILL 条件拒绝生成，如实报错，不编造。

## KILL 条件（硬拒绝）

- 只有公关通稿/发布会摘要 → 拒绝深稿。
- 只有社区传闻，无一手机源 → 拒绝或等待。
- 无证据的 Hot take → 拒绝。
- 无方法学 benchmark → 降级为引子，不得作为主论点。
- 无路线/预算/控制权后果的人事新闻 → 拒绝。
- 没有 denominator 的成本百分比 → 拒绝该论据。
- 没有法条原文的政策稿 → 拒绝。

## 硬性结构规则

1. 开头三段必须依次承担：**Observable（可观察事实）→ Conflict（与常识/发布会/benchmark/主流说法冲突）→ Decision（改变哪个工程/产品/商业决策）**。禁止前三句全部用于背景介绍。
2. 每条关键论据走五段证据链：**Claim → Observable → Source → Limitation → Decision**。
3. 结尾用 **Decision Rule + 改变判断的触发条件**，禁止金句升华与万能提问。
4. 真信度四件套（每篇强制）：≥1 失败案例 + ≥1 limitation + ≥1 可核验 artifact + 1 句只有真正调查过才写得出的句子。
5. Evidence Object（EO）：可独立核验的证据 = 数据点+来源 / 源码/commit / 测试日志 / 账单 / 截图 / 官方文档 / 法条 / 具名内部信 / 带上下文社区原话。
6. EO 密度：中文深度稿每千字 4–6 EO；LinkedIn 单帖 2–4 EO；至少 1 个作者亲自产生的 artifact。

## 作者声线与「人味」规则（2026-08-17 用户校准，优先级最高）

问题：过度执行证据纪律会把叙事写成咨询报告——证据链、判定表、五段式
结构直接暴露在候选表面，丢失了 n8n 原版「大白话 + 吃瓜体质 + 反直觉
钩子 + 敢下判断」的人味。

校准原则（调整语气，不改结构；三份调研的纪律仍然全量保留）：

1. **结构纪律不变**：Observable→Conflict→Decision 开头、五段证据链、
   denominator、证据等级阶梯、decision_rule + 触发条件、真信度四件套
   全部保留为硬规则——它们决定候选质量。
2. **语气人味层**：上述结构必须用大白话写，实锤像饭桌吐槽的
   punchline，而不是报告条目；证据是 punchline，不是骨架。
3. **作者人设**（编译自 knowledge/author-style.md + 2026 practitioner
   姿态）：15 年科技大厂与
   AI 架构老兵，冷峻、犀利、大白话、专业傲慢、爱看热闹；厌恶公关辞令
   与八股文；同时是 I tested / we changed / trade-off 的 practitioner。
   候选必须以第一人称思考。
4. **咨询腔黑名单**：综上所述 / 值得注意的是 / 一方面…另一方面 /
   我们认为 / 从 XX 维度来看 / 需要指出的是 / 赋能 / 闭环 / 颗粒度等。
5. **允许并鼓励**：讽刺、自嘲、冒犯、吃瓜；敢说「我不同意 / 我判断 /
   我的体感」。
6. **候选新字段（必填）**：narrative_focus（一句大白话这个角度讲什么）、
   author_stance（作者立场一句）、personal_scene（具体场景/瞬间）、
   kicker（冷结尾一句）。schema 校验强制这四个字段非空。

## 2026 最佳实践执行矩阵（调研报告3 重点集成）

以下规则已注入 narrative.py 的生成提示（PromptBestPracticeMatrixTests 锁定）：

### 五类高潜力 hook（HookPatternConfidence）

1. 同任务对照：Same task. Same prompt. X vs Y，分数不是最有意思的部分。
2. 感知 vs 实际：大家以为提升 X，实测却是 Y。
3. 跑分 vs 实战：榜单第 N，真实项目却……
4. 标价 vs 真账单：$X/token 看起来便宜，但一个成功任务实际 $Y。
5. deadline + 纠错：[日期] 生效，但你听到的流行解释是错的。

### 证据等级阶梯（按语境）

- 产品好不好用：可复现实测 artifact > 方法公开的独立研究 > 官方技术材料 > 多源社区交叉印证 > 媒体转述 > 单个匿名用户 > AI 摘要。
- 法律规定什么：法规/官方 guidance > 专业法律分析 > 可靠媒体 > 专家帖 > 社区讨论。
- 公司内部发生什么：公司公告/内部信/filing > 具名当事人 > 多源报道 > 单一媒体匿名 > 传闻。
- 引用研究必须写：[机构],[日期],[样本/方法],发现[结果];但[limitation]。

### 两个强制细节规则

- **denominator 规则**：任何成本百分比必须回答分母——每 token/每请求/每任务/每成功任务/是否含人工 review；没有分母的百分比一律降权。
- **人事事实状态标注**：每条敏感信息必须标 Confirmed / Reported / Inferred / Unknown；核心人事事实至少双源。

### 原型解剖速查

每个原型的标题公式、段落骨架、EO 密度与 takeaway 公式见 narrative.py 的
`_ARCHETYPE_ANATOMY`（只在白名单内的原型注入提示词），与报告3 第3节解剖卡
一一对应。

## 平台核心要点

### LinkedIn（practitioner memo）

- 读者任务：这会改变我的团队/架构/预算决策吗。
- 姿态：practitioner/operator（I tested / we changed / trade-off），非 thought leader。
- 开头结论先行，1–3 行完成 tension；feed 帖 150–450 词，深内容走 document。
- 证据少而硬（2–4 个关键 artifact）；价值密度 = 每次换行推进 new fact / implication / tension / decision。
- 评分权重：Evidence .35 / Decision .30 / Conflict .20 / Freshness .15。

### 微信公众号（editor-analyst）

- 读者任务：今天这件事意味着什么，值不值得花十分钟看。
- 新闻性开门、分析性留人；开头强场景/冲突/硬数字并立即解释为什么值得看。
- 1800–4000 字、短段落是硬指标。
- 标题允许「刚刚 + 已验证事件 + 具体后果」，禁止「刚刚 + 情绪形容词 + 模糊未来」；形容词一律换成 constraint。
- 评分权重：Conflict .30 / Evidence .25 / Decision .25 / Freshness .20。

### 知乎（knowledgeable peer）

- 允许复杂、禁止假深度；把 reasoning chain 展开（Problem → Thesis → Mechanism → Evidence → Counterargument → Conclusion）。
- 评分权重：Evidence .35 / MechanismDepth .30 / Conflict .20 / Freshness .15。

## 反模式黑名单（三报告合并版）

LinkedIn：`Stop X. Start Y.` / `It's not X, it's Y` / `The key is…` /
无据 `Hot take:` / `Unpopular opinion:` 开场 / `Let that sink in.` /
`I'm humbled/thrilled to announce` / delve、leverage、transformative、
holistic、game-changer / 均匀短句+三段万能教训 / 结尾 `What do you think?`。

中文：`震惊/炸裂/颠覆/史上最强` 标题 / `保姆级/最全/终极/一文看懂/收藏不亏` /
空洞排比与工整对仗 / `值得注意的是/不得不说/众所周知` 万能过渡 /
无信源 `业内人士透露/专家表示` / `未来已来/唯一不变的是变化/你准备好了吗` 结尾 /
无数字的 `效率提升 X%`。

替代总原则：具体数字替代形容词；前后对比数字 + 可复现方法 + 失败边界；
每千字至少 1 个可核验数字/代码/原话。

## 诚实边界

- 平台无公开 CTR 数据：系统字段用 `HookPatternConfidence`，禁止 `ExpectedCTR`。
- 证据信任排序（一手实测 artifact > 方法公开的独立研究 > 官方材料 > 多源社区交叉印证 > 媒体转述 > 匿名用户 > AI 摘要）是编辑策略推断，非统计结论。
- 法律类内容 primary source（法规/官方 guidance）优先级绝对最高。

## Legacy 附录（历史参考，不再作为主规则）

REF NarrativeGenerator 双角度结构、LCW 十维度/六原型映射表仅作历史参考；
双角度互斥约束保留：两个候选必须在维度/论证上互补或对立，不得同义重复。
