# Anti-slop: reduce repeated Deep judgments

## Problem Statement

The saved Chinese Deep draft from execution 871 restates the same distinction between paying for AI and receiving measurable returns in multiple sections. Two prior Light Editor attempts did not remove the repetition. The saved package identifies its original prompt version as unknown, so it demonstrates the writing problem but does not prove which historical instruction caused it.

## Solution

Test one sentence in the current Deep Writer system message. The earliest explicit current instruction that could invite repeated thesis restatement is “Make the central judgment easy to grasp. Explain how the examples support or complicate it”. Replace only that sentence with:

> State the central judgment where it first helps orient the reader; let later examples add distinct facts or consequences instead of restating it. Keep your interpretation distinct from what a source states.

This is a hypothesis to test, not a proven root cause. Keep the News Writer, Story Mode Editor, Light Editor, model node, and other prompt text fixed.

## Deep Writer system-message context

These are the other current sentences most related to judgment, repetition, endings, and voice:

1. “Open with a concrete, source-backed action, choice, or tension.”
2. “Make the reader question clear, then follow the approved story path rather than a report or feature list.”
3. “Keep passages that add a turn, example, consequence, or useful counterpoint.”
4. “Cut repeated explanations.”
5. “Write natural, varied Chinese for Zhihu or English for LinkedIn.”
6. “Use vivid phrasing only when it preserves the material's meaning and certainty.”
7. “Finish when the substance is complete.”
8. “You do not need to return to the opening, craft a memorable final line, or repeat the main point.”

The candidate wording agrees with 3–4 and 7–8: it tells examples to add distinct information and keeps one ending sufficient. It does not conflict with making the reader question clear or preserving voice. The remaining risk is that “state the central judgment where it first helps orient the reader” could pull a question-led Deep story toward an early thesis; the replay must show that this does not flatten the article.

## Replay surface

Current n8n tool metadata does not support running one node or a partial graph without adding a route. `n8n_execute_workflow` accepts `workflowId`, `executionMode`, optional trigger `inputs`, and optional `triggerNodeName`; it starts a workflow from a trigger. `n8n_test_workflow` accepts `workflowId`, `pinData`, optional `triggerNodeName`, and `timeout`; it tests a workflow and pins selected node outputs, but has no node-name or start-node argument. `n8n_get_workflow_execution` accepts `workflowId`, `executionId`, `includeData`, `nodeNames`, and `truncateData`; node filtering applies only when reading an existing execution.

Therefore ticket 01 uses two Codex CLI **Responses text experiments** before changing the n8n draft. Keep the saved input, model, CLI-supported effort, and all other configurable CLI parameters identical; change only the one candidate sentence in the Deep Writer system message. This is not an n8n node execution: it does not verify n8n parameters, ChatCompletions protocol, temperature, wiring, or runtime behavior. Record the CLI protocol and every parameter the CLI can expose; if a setting is unsupported, omit it in both calls and state that limitation. After a favorable read, update only the current n8n draft's Deep Writer system-message field. Do not publish or execute the workflow. No CLI call is part of this planning revision.

## User Stories

1. As an AI-curious reader, I want each section to add something new to the article’s central idea, so that the same point does not keep being restated.

## Implementation Decisions

- Change only the Deep Writer system-message sentence identified above, and only if a same-input replay improves the actual article on reading.
- Reuse the saved execution-871 Chinese Writer input. Keep the same input, model, CLI-supported effort, and other supported CLI settings before/after; this is a Responses text experiment, not preservation or validation of the n8n model payload. The current n8n model node exposes no effort setting; do not add one or switch providers.
- Retain the change only after reading the complete output. Otherwise restore the original sentence and report the result.
- If the Chinese model call fails, record the protocol/provider failure separately and stop that replay; do not change provider.

## Testing Decisions

- Compare one Deep Writer system-message sentence before/after in Codex CLI with identical saved Writer input, model, effort, and supported CLI settings. Record the source article hash `b0162b65a9abdec4de956de9db4860abe37b04c47b7b644a9e1983798a828b80` separately from the serialized Writer input hash `76ea9431d8423c844b5f9776583a211486f79166af0095628c4efdecb9ebc56a`. Label the calls as Responses text experiments, not n8n executions or payload validation. Read both complete outputs and judge whether repetition changed without flattening detail or voice.
- Label any CLI output as a prompt comparison. Do not call it an n8n execution or infer node wiring from it. Native n8n tools have no single-node/partial-execution parameter. The earlier executions 893/894 used a temporary route, but the operation payload is not saved; do not reconstruct or add that route in this ticket.
- No article score, automated slop detector, or broader workflow test is needed.

## Out of Scope

Changing Story Mode, News Writer, Light Editor, image captions, LinkedIn kit, adding a node/dependency, running an n8n workflow, or changing production behavior. The 871 package is a historical development sample, not an independent validation article.

## Further Notes

Current live facts and the selected prompt excerpt are stored in the ignored local fresh-read snapshot. The workflow draft and active version differ; execution 871 metadata is historical and its node data was not fetched.

## 2026-10-11 progress

Two matching Codex CLI Responses text experiments using `deepseek/deepseek-flash` at `low` effort returned complete before/after articles. The outputs are awaiting a human read; no quality conclusion or prompt-retention decision has been made. No n8n workflow was changed, published, or executed. The source article and serialized Writer input are separate artifacts with separate hashes; private request and CLI receipts remain local.
