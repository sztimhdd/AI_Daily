# 02 — Check the retained Deep Writer change on one holdout article

**What to build:** Evidence that a retained prompt change also improves one different Chinese Deep article, read as a complete draft rather than judged by a mechanical score.

**Blocked by:** 01 — Remove repeated Deep judgments when the replay supports it.

**Status:** not started — gated on ticket 01 editorial review and a decision to retain the change.

- [ ] Proceed only if ticket 01 retains the prompt change; if ticket 01 restores it, mark this ticket moot and report that no holdout run is needed.
- [ ] Use one independent saved article input that was not supplied as a model answer. Run two Codex CLI Responses text experiments with identical input, model, CLI-supported effort, and other supported settings; this does not preserve or validate the n8n model payload. Change only the same Deep Writer sentence.
- [ ] Label the result as a CLI prompt comparison, not an n8n node execution. Do not add a temporary n8n route. If the CLI cannot hold the saved input, model, and supported settings constant, stop and report the missing capability.
- [ ] Read both complete outputs. Keep the change only if the holdout also avoids repeated judgments while preserving its own voice and useful detail; otherwise revert the prompt change and report the regression.
- [ ] Treat any Chinese model protocol/provider failure separately and stop without switching models/providers.
