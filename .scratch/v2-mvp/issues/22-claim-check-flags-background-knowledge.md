# 22 — claim-check 把背景知识与自报的降级措辞误判为 unsupported

**Status:** needs-triage

## 现象（2026-08-21 E2E 实测）

英文稿 claim-check 判定 `unsupported`，21 条断言里 10 条被判 unsupported。但逐条看，这些多数不是事实错误，而是三类误判：

1. **通用背景知识**：`Speculative decoding uses a smaller draft model to propose tokens…`、`Standard autoregressive decoding selects one next token at a time`——这是领域常识，文章已明确标注“describes the conventional mechanism, not a confirmed map of Liquid AI’s implementation”，不应要求证据包逐字覆盖。
2. **文章自身的诚实降级措辞**：`The official Hugging Face page's technical body could not be independently reviewed`、`The available reports provide neither raw benchmark tables nor an independent reproduction`——这些是“我拿不到/没证据”的如实陈述，却被当成需要证据支撑的事实主张来判。
3. **对“未独立确认”的元陈述**：`The 3.18x and 2.87x results are vendor-reported and not independently confirmed` 被判 unsupported，但这句话恰恰是正确标注了来源等级。

## 根因判断

claim-check 的 prompt 让模型“逐条核对断言 vs 证据包”，但没有区分：
- 需证据支撑的“本次事件事实主张”；
- 无需证据的“通用领域解释”；
- 本身就是“无证据”的降级/元陈述。

结果 claim-check 把编辑的诚实措辞当成事实错误来扣。

## 建议修复方向（待主编确认，本轮不实现）

- claim-check prompt 增加三类豁免规则：领域常识、文章已声明的“未独立审阅/无复现”降级语、对来源等级的元陈述不算 unsupported。
- 或将 claim-check 输出从 `unsupported` 细分为 `unsupported_fact`（真错误）/ `unverified_label`（正确降级）/ `background`（常识），让编辑信号可区分。

## 关联

- 与 issue 20/21 同属“判定层过严/未校准”一类，建议和“产出优先、风险标签化”原则一起在下一轮统一校准。
