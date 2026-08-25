# Narrative v2 叙事模块设计

## Problem Statement

04 叙事候选阶段把“读者决策”误当成所有文章的共同终点。全局的
`Observable → Conflict → Decision`、`Claim → ... → Decision`、必填
`decision_rule` 与默认 `decision_brief`，会把收购传闻、技术事件和行业争议
都压成 CTO 行动清单。两个候选因此经常只是同一条建议换了标题，缺少新闻性、
故事弧线和真正不同的解释角度。

原始 n8n `NarrativeGenerator` 已经提供了更宽的能力：调查/隐性成本、地缘
战略、长期影响和 genuinely different angles；`Final Editor` 与“去 AI 味”
资产也要求个人场景、鲜明判断、失败与真实经验。重构必须恢复这些能力，同时
保留当前证据边界，不允许模型把传闻写成事实。

## Solution

将 narrative 拆成三个正交选择：

1. `narrative_form`：报道、反共识、机制拆解、成本账本、工作流、权力图、
   合规解释、战略展望或决策快讯。它回答“这篇文章用什么方式讲”。
2. `reader_move`：`understand`、`reframe`、`watch`、`prepare`、`act` 或
   `imagine`。它回答“读者读完发生什么变化”，不默认是行动。
3. `ending_mode`：`open_tension`、`implication`、`forecast`、
   `decision_rule` 或 `scene_kicker`。只有需要行动的原型才要求
   `decision_rule`。

全局写作骨架改为：`hook/scene → observable → central tension →
mechanism/actors → counterargument or unknown → ending_mode`。证据仍然
约束事实、归因和不确定性，但不再强迫每一段输出决策。

保留旧字段和旧消费者的兼容性；`decision_rule` 为空对非行动型叙事合法。
候选对增加相似度门：核心 thesis、reader_move 和 action language 过度重合
时拒绝整对候选，要求重新生成。

证据路由改为语义更窄的类型判断：估值/融资不自动成为成本证据，收购报道不
自动成为控制权证据，社区观点不自动成为可复制工作流。`decision_brief` 只在
存在已确认且会改变近期动作的事件时作为优先候选，不再作为无差别兜底风格。

## User Stories

1. As an editor, I want a reported event to produce a readable news-led angle,
   so that the article does not begin as a consulting memo.
2. As an editor, I want a rumor to support `watch` or `reframe` without a forced
   migration command, so that unknowns remain visible.
3. As an editor, I want a technical artifact to unlock mechanism writing,
   so that deep analysis is earned by evidence rather than keywords.
4. As an editor, I want a strategic or geopolitical angle when the evidence
   supports actors, incentives and second-order effects, so that not every story
   ends in a checklist.
5. As an editor, I want two candidates to differ in their central question,
   not merely in title or archetype label, so that HITL choice is meaningful.
6. As a reader, I want a concrete scene, human stance and memorable ending,
   so that the article feels written by an experienced practitioner.
7. As the pipeline, I want old selected-narrative artifacts to remain readable,
   so that sufficiency, drafting and Telegram resume do not break during rollout.

## Implementation Decisions

- Extend candidate schema with `narrative_form`, `reader_move`, and
  `ending_mode`; keep `decision_rule` optional and display it only when present.
- Keep the existing eight evidence archetypes as routing capabilities, and add
  `reported_story` and `strategic_outlook` as forms rather than multiplying
  evidence gates.
- Add explicit prompt language that `decision_brief` is exceptional and that
  a candidate may end with an implication, forecast, unresolved tension or scene.
- Make prompt structure form-specific. The evidence chain remains available to
  each argument, but `decision` is not a required slot for every argument.
- Add a deterministic candidate-pair check based on normalized thesis,
  reader move and action terms. Reject obvious same-advice pairs before HITL.
- Narrow the evidence inventory flags with typed keywords and module/source
  distinctions; retain existing tests for current valid routes.
- Update the knowledge contract and Telegram/TUI renderer to show form, reader
  move, ending mode and optional action rule in plain Chinese.

## Testing Decisions

- Test externally observable routing behavior with valuation-only, acquisition-
  rumor, community-only and true cost/workflow fixtures.
- Test prompt text for removal of universal Decision requirements and presence
  of form-specific ending rules.
- Test schema acceptance of a non-action candidate without `decision_rule` and
  rejection of a same-thesis candidate pair.
- Test TUI rendering of optional decision rules and new narrative fields.
- Run the focused narrative suite, full test suite, `git diff --check`, and the
  existing CLI/UAT script before claiming completion.

## Out of Scope

- Rewriting the article drafting or evidence-sufficiency engines.
- Adding a new model provider or changing Telegram authentication.
- Automatically selecting a candidate without the existing HITL gate.
- Reintroducing unsupported claims or using KG background as event evidence.

## Further Notes

The desired Hugging Face rumor behavior is `reframe`/`watch`: explain why the
ecosystem is holding a funeral before there is a body. A dependency checklist
may appear as a secondary implication, but it must not replace the story.
