# 01 — Restore typed narrative forms and evidence routing

**What to build:** The narrative stage distinguishes evidence type from narrative
form and does not classify valuation rumors as cost data or acquisition rumors as
confirmed control changes.

**Blocked by:** None — can start immediately.

**Status:** completed

- [x] Candidate schema supports `narrative_form`, `reader_move`, and
  `ending_mode`; `decision_rule` is optional outside action forms.
- [x] Valuation-only and acquisition-rumor fixtures route without cost/control
  artifacts; genuine cost and mechanism fixtures retain their routes.
- [x] Existing selected-narrative readers remain compatible.
