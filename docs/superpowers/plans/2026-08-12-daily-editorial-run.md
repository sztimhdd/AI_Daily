# Daily Editorial Run (V1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Implement the V1 daily editorial pipeline — collect → topic_choice (human gate) → research → outline → draft → optional cover → assembly → publish — driven by `state.md`, tests-first, Python stdlib + unittest only.

**Architecture:** One module per pipeline stage under `src/ai_daily/`, orchestrated by `pipeline.py` and exposed through `cli.py`. Each dated run owns `.local/runs/<date>/` working state; durable packages land in `outputs/YYYY/MM/DD/<slug>/` with a final article at `articles/<date>-<slug>-zh.md`. Evidence never leaves the run directory; knowledge assets compiled from the immutable core-IP JSONs live in `knowledge/`.

**Tech Stack:** Python 3.14 standard library, unittest, POSIX shell (UAT), jq (baseline checks)

**Spec:** `docs/superpowers/specs/2026-08-12-daily-editorial-run-design.md`

## Global Constraints

- Stdlib only in `src/`; no new runtime/test framework.
- Never modify the five immutable core-IP JSONs or legacy 2026-08-12 artifacts.
- No Automation, email/WeChat publishing, DB/locks/event sourcing, or V1.5 features.
- RSS failures are nonblocking; AIHOT failure stops candidate generation.
- Never invent feed URLs; catalog provenance documents 93 entries = 91 source occurrences + 2 auxiliary services, 73 unique extractable URLs (marker heuristic, not runtime verification).
- No commits/pushes from implementation workers.

---

### Task 1: Run scaffolding — paths and state

**Files:** `src/ai_daily/paths.py`, `src/ai_daily/state.py`, `tests/test_paths.py`, `tests/test_state.py`

- [x] Date-validated `RunPaths` (work dir, package dir, final article path).
- [x] Stable `state.md` with stage, slug, topic_choice, last_error, stage_log, artifacts, counters; transitions, fail/clear_error, bump_counter, record_artifact.

### Task 2: Evidence collection — AIHOT + RSS

**Files:** `src/ai_daily/aihot.py`, `src/ai_daily/rss_catalog.py`, `src/ai_daily/rss_collect.py`, matching tests, `knowledge/rss-catalog.json`

- [x] AIHOT fixture and live modes; malformed payload/source-string returns controlled failure with zero items.
- [x] Provenance-aware RSS catalog preserving 93 legacy entries; deterministic regeneration (no timestamps).
- [x] RSS collect: parser, window filter incl. `dc:date`, undated items kept+counted, URL+title dedup, per-feed stats, compressed pool markdown, generator-safe inputs; failures nonblocking.

### Task 3: Topic candidates and human gate

**Files:** `src/ai_daily/topics.py`, `tests/test_topics.py`

- [x] Exactly 3 rich candidates (thesis/hook/relevance/gaps/queries/sources) from the evidence pool.
- [x] `same_event` clustering: generic-token exclusion, mixed ASCII+CJK bigram fallback, numbered-series protection.
- [x] Human gate (`require_choice`) + fixture bypass; fixture load errors wrapped in `TopicError`.

### Task 4: Knowledge compilation

**Files:** `knowledge/research-contract.md`, `knowledge/author-style.md`, `knowledge/remove-ai-slop.md`

- [x] Compiled from the immutable core-IP JSONs (read-only) into executable guidance for research/draft/deslop.

### Task 5: Research, outline, draft

**Files:** `src/ai_daily/research.py`, `outline.py`, `draft.py`, matching tests

- [x] Key-question research over the evidence pool only; linked evidence; insufficient questions marked, never fabricated; failure recorded and cleared on recovery; resume without re-collect.
- [x] Outline with the 8 spec fields; bullets map 1:1 to draft headings; thesis quoted verbatim.
- [x] Fact-backed draft: news peg, nut graf, short mobile paragraphs, source links, uncertainty, cold kicker; must pass the deslop contract.
- [x] `regenerate_outline_from_edit`: edited outline rebuilds the draft without collect; `collect_runs` unchanged.

### Task 6: Remove-AI-slop contract

**Files:** `src/ai_daily/deslop.py`, `tests/test_deslop.py`

- [x] Executable 8-category checker with positive (dirty) and clean corpus tests.

### Task 7: Cover (optional, nonblocking)

**Files:** `src/ai_daily/cover.py`, `tests/test_cover.py`

- [x] PNG/JPEG/WebP byte validation incl. dimensions; newest `ChatGPT Image*` locator + move; invalid/missing cover never blocks.

### Task 8: Assembly

**Files:** `src/ai_daily/assemble.py`, `tests/test_assemble.py`

- [x] Package `article.md`/`metadata.json`/`sources.md`(+cover), final article mapping; rejects empty/no-H1/placeholders/`{{...}}`/n8n leftovers/source-link-less drafts; succeeds without cover.

### Task 9: Publish with verified remote

**Files:** `src/ai_daily/publish.py`, `tests/test_publish.py`

- [x] `gh`-compatible git transport (injectable); push → fetch → `show FETCH_HEAD:<rel>` → SHA-256 compare of exact content; unavailable/failure → explicit `local-only`, never fake success; recovery files recorded.

### Task 10: Pipeline orchestration and CLI

**Files:** `src/ai_daily/pipeline.py`, `src/ai_daily/cli.py`, `tests/test_pipeline.py`, `tests/test_cli.py`, `tests/test_pipeline_e2e.py`

- [x] Stage gates, resume from existing artifacts, AIHOT-failure-stops, RSS nonblocking, outline-regenerate mode, unattended `run` fixture E2E.
- [x] CLI subcommands with exit codes 0/1/2; black-box E2E incl. two-date isolation, gate refusal, cover variants, failure→resume.

### Task 11: Verification scaffold and docs

**Files:** `scripts/uat_cli.sh`, `docs/verification/`, `README.md`, `src/README.md`, `tests/README.md`

- [x] Deterministic fixture UAT entrypoint with saved results.
- [x] Verification plan covering local checks and remaining external UAT.
- [x] README install/test/lint/run documentation.

## Remaining external UAT (out of scope for local implementation)

1. Live AIHOT endpoint against `https://aihot.virxact.com/api/v1/items`.
2. Real GitHub publish: push + remote reread hash against an actual remote.
3. Real RSS fetch across catalog feeds (extractability heuristic confirmation).
4. Real ChatGPT cover export adoption.
5. Human topic-gate interaction in a real editorial chat.
