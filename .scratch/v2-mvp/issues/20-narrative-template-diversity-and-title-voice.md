# 20 — 叙事原型坍缩 + 标题腔与「人味」校准未同步

**Status:** resolved

## 现象（用户报告，2026-08-21 E2E）

叙事候选 2 的标题「LFM2.5-DSpark刚发布，工程负责人只需要看三件事」读起来像咨询报告，没有文学性和新闻性。怀疑 legacy n8n 的多套叙事模板没有被完整套用到多叙事逻辑里，导致 `决策快讯`（decision_brief）出现过于频繁。

## 已核实的根因（代码证据）

1. `src/ai_daily/narrative.py` 的 `route_archetypes`：当证据清单无法命中任何原型的触发条件时，白名单坍缩为 `["decision_brief"]`——它是唯一兜底原型。见 `route_archetypes` 末尾 `if not allowed: allowed = ["decision_brief"]`。
2. `_ARCHETYPE_ANATOMY["decision_brief"]` 的标题公式字面量仍是「[X just changed]，只有三件事值得工程负责人看」——这正是被用户判定为咨询腔的标题，与 `knowledge/narrative-contract.md` 里 2026-08-17「作者声线与『人味』规则（优先级最高）」要求的「大白话 punchline / 咨询腔黑名单」相矛盾：校准写进了契约，但没有同步回八原型的标题公式。
3. 触发条件分布不均：`decision_brief` 只需 `primary_signal`，而 `mechanism_teardown` 需 `mechanism_signal + tech_artifact`、`cost_ledger` 需 `cost_data` 等。OSINT 一旦没有源码/架构/账单级一手材料，就落到兜底原型，导致 decision_brief 频繁出现——这是「模板没被完整套用」的真实机制：模板在代码里，但证据路由的门槛把多数选题推回兜底。

## 复核补充（2026-08-21，与 issue 21 联动）

坍缩还有一个隐藏放大器：机制信号检测的关键词是中文的（架构/机制/上下文），英文证据（speculative decoding / draft model checkpoints）不命中，机制类一手材料存在也拿不到 `mechanism_signal`/`tech_artifact`；叠加 issue 21 的摘录截在导航，机制信号被双重饿死。

## Answer（已修复）

- `_ARCHETYPE_ANATOMY["decision_brief"]` 标题公式改为「[X] 刚变，别被热搜带节奏——真正要盯的就三处」，去除「工程负责人只需要看N件事」咨询句式。
- 叙事提示词新增标题声线硬规则（语气人味第 5 条）：标题必须是大白话新闻 punchline，明确禁止「值得关注的N件事 / 工程负责人只需要看N件事 / 一份决策简报/快讯」句式。
- 机制信号补英文关键词：`mechanism_signal` 增加 speculative decoding / draft model / decoding path；`tech_artifact` 增加 checkpoint / model card / speculative decoding。
- 真实复核（用修复后的 HF 摘录重跑本 E2E OSINT）：`mechanism_signal=True, tech_artifact=True`，白名单从坍缩为 `[decision_brief]` 变为 `[first_hand_test, mechanism_teardown, decision_brief]`。
- 回归测试：`test_english_mechanism_evidence_opens_mechanism_teardown`、`test_prompt_bans_consulting_title_phrasing`、`test_decision_brief_anatomy_title_is_not_consulting`。

## 关联

- 本次 E2E 采用叙事 1（mechanism_teardown），不采用叙事 2（decision_brief）。
