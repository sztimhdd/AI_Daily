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
