# 04 — Run narrative v2 through Telegram and the article pipeline

**What to build:** A fresh run generates the new candidate pair, sends it through
Telegram, accepts the editor's choice, and continues into the existing full-text
stages with the chosen narrative identity intact.

**Blocked by:** 03 — Expose the new narrative contract to HITL.

**Status:** completed

- [x] Focused and full tests pass: 727 tests; `scripts/uat_cli.sh` 17/17 PASS.
- [x] Telegram receives a “narrative v2 ready” status receipt without exposing
  credentials.
- [x] A fresh run proves selected narrative title/form survives into the
  evidence package and draft input.
- [x] Any failure reports the exact stage and does not silently choose a
  different narrative.
