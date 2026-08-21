# 03 — English fixture E2E and CLI

**What to build:** A maintainer can run one offline fixture command that validates the daily English delivery loop and demonstrates normal, degraded, and resumed outcomes without paid APIs or a remote repository.

**Blocked by:** 01 — English delivery summary and orchestrator; 02 — English package publisher.

**Status:** ready-for-agent

- [ ] The CLI exposes `run-en` and prints the delivery summary location and per-stage statuses.
- [ ] Fixture UAT verifies article, sources, metadata, kit, final English article, and explicit degraded-image behavior.
- [ ] Fixture UAT verifies local-only publication and rerun resume semantics.
