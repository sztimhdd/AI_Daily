# 20 — 叙事原型坍缩 + 标题腔与「人味」校准未同步

**Status:** needs-triage

## 现象（用户报告，2026-08-21 E2E）

叙事候选 2 的标题「LFM2.5-DSpark刚发布，工程负责人只需要看三件事」读起来像咨询报告，没有文学性和新闻性。怀疑 legacy n8n 的多套叙事模板没有被完整套用到多叙事逻辑里，导致 `决策快讯`（decision_brief）出现过于频繁。

## 已核实的根因（代码证据）

1. `src/ai_daily/narrative.py` 的 `route_archetypes`：当证据清单无法命中任何原型的触发条件时，白名单坍缩为 `["decision_brief"]`——它是唯一兜底原型。见 `route_archetypes` 末尾 `if not allowed: allowed = ["decision_brief"]`。
2. `_ARCHETYPE_ANATOMY["decision_brief"]` 的标题公式字面量仍是「[X just changed]，只有三件事值得工程负责人看」——这正是被用户判定为咨询腔的标题，与 `knowledge/narrative-contract.md` 里 2026-08-17「作者声线与『人味』规则（优先级最高）」要求的「大白话 punchline / 咨询腔黑名单」相矛盾：校准写进了契约，但没有同步回八原型的标题公式。
3. 触发条件分布不均：`decision_brief` 只需 `primary_signal`，而 `mechanism_teardown` 需 `mechanism_signal + tech_artifact`、`cost_ledger` 需 `cost_data` 等。OSINT 一旦没有源码/架构/账单级一手材料，就落到兜底原型，导致 decision_brief 频繁出现——这是「模板没被完整套用」的真实机制：模板在代码里，但证据路由的门槛把多数选题推回兜底。

## 建议修复方向（待主编确认优先级，本轮不实现）

- 把「人味」标题规则落到 `_ARCHETYPE_ANATOMY` 的标题公式，至少替换 decision_brief 的「只有三件事值得看」句式。
- 复查 `route_archetypes` 的兜底策略：是收紧 signal 提取，还是允许生成候选时带「证据不够只能简报」的显式降级标注，避免 silent fallback。
- 加回归：断言候选标题不含咨询腔黑名单词；断言路由在证据弱时不静默坍缩。

## 关联

- 本次 E2E 采用叙事 1（mechanism_teardown），不采用叙事 2（decision_brief）。
