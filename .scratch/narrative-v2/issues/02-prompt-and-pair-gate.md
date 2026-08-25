# 02 — Make narrative prompts form-specific and reject same-advice pairs

**What to build:** Codex receives a prompt that can produce reporting,
reframing, mechanism, strategic outlook or action narratives with an appropriate
ending, and the pipeline rejects two candidates that are merely cosmetic variants.

**Blocked by:** 01 — Restore typed narrative forms and evidence routing.

**Status:** completed

- [x] Prompt no longer imposes universal `Observable → Conflict → Decision` or
  mandatory `decision_rule`.
- [x] Prompt preserves evidence-boundary rules and original author-scene,
  first-person, metaphor and anti-consultant requirements.
- [x] Same-thesis/same-action candidate pairs fail deterministically.
- [x] Two candidates with different central questions pass.
