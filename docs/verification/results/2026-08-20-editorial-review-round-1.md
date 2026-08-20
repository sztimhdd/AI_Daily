# 主编双模型评审：AI_Daily 英文最终产品（Round 1）

**日期：** 2026-08-20｜**评审对象：** 全自动跑出的 Stripe × OpenRouter 英文稿及完整包

- 包：`outputs/2026/08/20/stripe-didn-t-buy-the-singularity-it-bought-the/`
- 终稿：`articles/2026-08-20-stripe-didn-t-buy-the-singularity-it-bought-the-en.md`
- 质量门：pass（1109 词），保守降级已接受（审计 `needs_research`，缺口已标注）

**评审身份：** 用户 n8n 工作流中的主编（Final Editor1 The Verge/Wired 级主编 +
Final Editor3 De-AI Protocol 硅谷老兵架构师 + 组装规则），原文提取自
`workflows/reference/公众号选题写稿配图一体化工作流.json`。

**双模型：**
- DeepSeek（主代理，主编 persona）：`minor_revision`，12 条
- GPT-5.6（gpt-5.6-sol，同 prompt）：`major_revision`，33 条

## 合并问题清单（按根因归组）

| # | 严重度 | 类别 | 问题（两模型共识标注） | 根因 |
|---|---|---|---|---|
| 1 | P1 | 证据 | 推断被写成既成能力：「Stripe holds a live, per-request view of unit economics」（分析师假设）；「The buyer already owns the bill」（过度）【双】 | 提示词只有原则性规则，无推断句式约束；质量门只查确定性词不查能力陈述 |
| 2 | P1 | 证据 | 事实性小错：「four words」实为 8 词且是连续性承诺非中立承诺；「both companies confirmed」只挂 OpenRouter 单方链接；Deedy「co-founder」身份未核实；「everywhere」夸张【G】 | draft 后无 claim↔evidence 事实核对环节 |
| 3 | P1 | 证据 | 引语截断：「stays driven by what」半句引语仍发布，正文自曝截断【双】 | 证据摘录按字符硬截断，不保护句尾/引号；质量门无引语完整性检查 |
| 4 | P1 | 格式 | 关键数字全部未加粗（$7B/10T+/5.4x/$1.3B），加粗全给了段落引导语【双】 | 视觉高亮规则（UDW·去AI味）从未编译进提示词/质量门 |
| 5 | P1 | 格式 | 直接引语未转 blockquote（same mission…）【双】 | Final Editor3 组装规则未编译 |
| 6 | P1 | 去AI味 | 逐段「加粗断言+随后退让」同构模板；中立 vs 账本主题无新证据重复 4 次【双】 | 提示词把加粗引导语当每段模板 |
| 7 | P1 | 去AI味 | Fence-sitting：反复「unresolved/not disclosed」而不给立场，与 persona「take a stand」冲突【G】 | 保守降级指令（never assert）与主编立场规则冲突，缺消解协议 |
| 8 | P1 | 节奏 | 首段 50+ 词、多处 25–33 词长句；被动语态（was not fetched/is unresolved）【双】 | EN 节奏契约（20 词句长/主动语态/缩写）未编译 |
| 9 | P1 | 管线 | HTTP 403、fetched text 等抓取诊断泄漏进正文【G】 | 提示词未区分 provenance 层与正文层 |
| 10 | P1 | 包 | metadata.json 缺质量门结果/证据裁定/降级标记/SEO 字段【双】 | assemble_en 未落 spec §5「最终接受结果记入 metadata」 |
| 11 | P1 | 包 | 无 LinkedIn 分发套件（主编 Persona C 要求）【G】 | 范围决策：spec 延后至 delivery 适配器，未实现也未留占位 |
| 12 | P2 | 包 | slug 48 字符硬截断（丢了标题 punchline「meter」）【双】 | slugify 按字符截断不按词 |
| 13 | P2 | 包 | sources.md：failed 来源标题是裸 URL；中文标题混入英文包【双】 | _render_sources_md 无标题 fallback 与语言归一 |
| 14 | P2 | 证据 | 链接过密、同源重复挂链、无标点分隔【双】 | 「每事实一链接」规则过度执行 |
| 15 | P2 | 证据 | 「25% 折扣」在两价未核实前给出；「price math is inconsistent」标题诊断错病因【G】 | 降级标注覆盖了数字，但未覆盖衍生计算 |

## 两模型分歧

- 总判定：DeepSeek `minor_revision` vs GPT-5.6 `major_revision`。分歧集中在证据精度——GPT-5.6 更严格地要求「推断句式」「身份核实」「绝对否定限定范围」。合并裁定：**major_revision**（P1 证据类问题须在发布前修复）。
- 已按约定而非问题：`articles/<date>-<slug>-en.md` 终稿路径与包内 `<slug>.md` 并存（用户 2026-08-20 拍板的命名方案），GPT-5.6 未获得该上下文，此条不计入。

## 归因结论（ask-matt 路由）

15 个问题全部归因到 4 处流程/提示词资产：

1. **knowledge 资产缺口（迁移矩阵 §2「待补编译」项）** → 问题 4、5、8：视觉高亮、EN 节奏契约、组装规则三项从未编译。
2. **draft_en 提示词** → 问题 1、6、7、9、14：推断句式、模板结构、降级-立场冲突、管线词、链接密度。
3. **确定性质量门** → 问题 2、3：无引语完整性检查、无 claim-check。
4. **打包层** → 问题 10、11、12、13：metadata 字段、slug、sources 归一、LinkedIn 套件。

完整原始评审：`.local/review/deepseek-review.json`、`.local/review/gpt56-review.json`。

---

## Round 1b：表达力重评（按用户反馈补做）

第一轮评审偏执于证据/逻辑/事实，忽略了主编 prompt 里对普通读者更重要的
「high-burstiness、sensory detail、punchy、叙事爆发力」。用同一主编身份、
同一篇稿，双模型只评文字表达力（修辞、节奏、张力、画面感、普通读者体感）：

**共同裁定：`workable`——有杀手级意象，但被埋没。**

**共同优点：**
- 标题「Stripe Didn't Buy the Singularity — It Bought the Meter」：反题 + 具象，一眼记得住
- 「The demand ledger, not the singularity, is what changed hands」：全文最强句（可惜提前花掉了）
- meter / switch / ledger / toll booth 意象群：把一笔抽象的收购变成了可看见的物
- 结尾有威胁感和前推力

**合并表达力问题清单：**

| # | 严重度 | 方面 | 问题 | 修法方向 |
|---|---|---|---|---|
| 1 | P1 | 钩子 | 标题刚钩住人，首段就用交易摘要 + HTTP 403 取证细节打断魔法；前 10 秒读到的是合规语言不是冲突【双】 | 第一句先给碰撞画面（Stripe 看得见账单，现在连每笔 prompt 成本也看得见）；403 细节移出正文 |
| 2 | P1 | 节奏 | 14 段同构（加粗断言+限定+链接），节拍器式；没有单句成段、没有长短交替、没有加速【双】 | 拆模板：合并同类段、最好的一句单独成段、长短交替 |
| 3 | P1 | 张力 | 中心冲突前 1/3 就讲完，后面换词重述；「opposite directions」出现 3 次成口头禅；峰值太早【双】 | 把冲突做成 crescendo：先埋事实，后收判断；只保留一次对仗 |
| 4 | P1 | 声线 | 「demand-side telemetry / unit economics / spend visibility」咨询腔；全篇无具体的人、场景、五感【双】 | 画面先于术语：先「看得见每笔 prompt 的成本在闪」，再上术语 |
| 5 | P2 | 可读性 | (*) 成本公式三个变量踩急刹车，普通读者直接跳过，而它是论点支点【双】 | 换成画面：「看得见哪个模型接了活、烧了多少 token、花了多少」 |
| 6 | P2 | 结尾 | 收费站意象好，但结尾吊在抓取截断的半句引语上；最强句（demand ledger）开头就用掉【双】 | 结尾回扣标题意象「Stripe 买的不是奇点，是表——现在轮得到它决定收费站摆在哪」；截断引语留证据层 |
| 7 | P2 | 修辞 | 「Which one wins / Which one survives」两次对仗、same reason 重复，只有回音没有推进【双】 | 保留一次最强对仗，其余换句式 |

**对 ticket 的影响：** 表达力问题全部归因到 draft_en 提示词（叙事弧线、意象先于术语、
节奏多样性、最强句压轴）+ knowledge 资产缺口（叙事节奏契约）。已并入 09/10 两张票，
Round 2 复评（ticket 15）须同时验收「事实精度」与「表达力」两个维度。
