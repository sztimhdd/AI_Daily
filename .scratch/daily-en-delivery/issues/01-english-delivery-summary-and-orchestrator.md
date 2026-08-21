# 01 — English delivery summary and orchestrator

**What to build:** An editor can invoke one English delivery operation that drives the existing draft, review, illustration, kit, and assembly stages, then leaves a durable per-stage summary and a usable package when optional enrichment fails.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Offline test proves a generated draft, unavailable image and kit, and completed assembly yield a durable package plus a degraded delivery summary.
- [ ] Offline test proves a malformed or absent English draft stops before assembly and identifies the hard failure.
- [ ] Offline test proves a second invocation resumes completed work rather than regenerating it.
