# 01 — Remove repeated Deep judgments when the replay supports it

**What to build:** A Chinese Deep draft where later sections add distinct information instead of restating the central judgment, while keeping the article’s useful detail, voice, attribution, and uncertainty.

**Blocked by:** None — can start immediately.

**Status:** awaiting editorial review — both text outputs are complete; the main controller has not read them. The earlier CLI argument parsing failure was corrected before these calls and is not the current status.

- [ ] In the current draft, change only the Deep Writer system-message sentence “Make the central judgment easy to grasp. Explain how the examples support or complicate it” to “State the central judgment where it first helps orient the reader; let later examples add distinct facts or consequences instead of restating it. Keep your interpretation distinct from what a source states.” Treat this as a hypothesis; do not modify Story Mode, News Writer, Light Editor, or other fields.
- [x] Run exactly two Codex CLI Responses text experiments with the same saved Writer input, `deepseek/deepseek-flash`, `low` effort, and matching supported CLI settings. Change only the approved Deep Writer sentence. The source article SHA-256 `b0162b65a9abdec4de956de9db4860abe37b04c47b7b644a9e1983798a828b80` and serialized Writer input SHA-256 `76ea9431d8423c844b5f9776583a211486f79166af0095628c4efdecb9ebc56a` are distinct artifacts. Both calls returned complete articles. This is not an n8n node execution and does not validate n8n parameters or runtime behavior; see the private local receipts for request and CLI evidence.
- [ ] Read both complete outputs. Retain the sentence change only if repetition improves without losing useful detail or voice; otherwise do not change the n8n draft. Label the result as a CLI prompt comparison, not an n8n node execution.
- [ ] If the comparison supports the change, update only the current n8n draft's Deep Writer `options.systemMessage` field. Record the resulting draft version. Do not publish or execute the workflow; do not alter the active version or other workflow fields.
- [ ] If the CLI cannot hold the saved input, model, and supported settings constant, stop before the second call and report the missing capability. The existing n8n tools do not support single-node or partial execution without a temporary route; do not create or run such a route in this ticket.
- [ ] If the Chinese model call fails, record it as a protocol/provider failure and stop. Do not retry through another model/provider. Report the changed field, model payload identity, output finding, and keep/revert decision.
