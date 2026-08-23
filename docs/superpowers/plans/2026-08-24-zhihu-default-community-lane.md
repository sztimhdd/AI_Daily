# Zhihu Default Community Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Zhihu CLI a default community-evidence source in the 03 live research stage (bounded, cached, labeled community-voice), without touching the real API during verification.

**Architecture:** `zhihu_lane.py` gains a `community_voice()` helper + markdown renderer. `research.run_initial` gains an injectable `zhihu_runner`; after the KG background, it runs one cached community search, writes `zhihu-community.json`/`.md`, appends items to the OSINT sources (`source_lane="zhihu-cli"`) and enriches `community_voices`. A `zhihu` CLI subcommand mirrors `kg` for manual/real runs. All tests use fake runners.

**Tech Stack:** Python stdlib, existing unittest suite, existing research stage, existing zhihu_lane.

**Spec:** ADR 0002 (evidence-level rules: community voice, not primary fact; never feeds gates; quota knob).

## Global Constraints

- Never raise on zhihu failure; return degraded/unavailable.
- Zhihu items are labeled `source_lane="zhihu-cli"` + `community=true`; never treated as primary fact.
- All verification with injectable runners; no real API calls.
- `ZHIHU_RESEARCH_BUDGET = 1` per research run (single knob for later raise).

---

### Task 1: `zhihu_lane.community_voice` + renderer

**Files:** `src/ai_daily/zhihu_lane.py`, `tests/test_zhihu_lane.py`

- [ ] **Step 1: Failing tests** — `community_voice()` returns normalized items with a topic-derived query; a `render_community_md()` marks 二手社区证据; unavailable runner → `{"status": "unavailable"}` and never raises.
- [ ] **Step 2: Run → red.**
- [ ] **Step 3: Implement** — `community_voice(topic, runner=None, count=5)` builds `query = topic.title + first research_query`, calls `search_zhihu`, returns `{"status": "ok", "items": [...]}`; `render_community_md(data)`.
- [ ] **Step 4: Run → green.**
- [ ] **Step 5: Commit.**

### Task 2: Research-stage integration

**Files:** `src/ai_daily/research.py` (+`pipeline.py`), `tests/test_research.py`

- [ ] **Step 1: Failing tests** — with a fake zhihu runner, `run_initial` writes `zhihu-community.json`/`.md`, appends `source_lane="zhihu-cli"` items to the OSINT sources, and enriches `community_voices`; failure → degraded and research still `generated`; resume skips re-search.
- [ ] **Step 2: Run → red.**
- [ ] **Step 3: Implement** — `run_initial(..., zhihu_runner=None)`; after KG, call `zhihu_lane.community_voice(topic, runner)` (skip if `zhihu-community.json` exists for the topic), write artifacts, append to `data["sources"]` + a `community_voices` note. Add `ZHIHU_RESEARCH_BUDGET = 1` and a run-level guard.
- [ ] **Step 4: Run → green.**
- [ ] **Step 5: Commit.**

### Task 3: CLI `zhihu` subcommand

**Files:** `src/ai_daily/cli.py`, `tests/test_cli.py`

- [ ] **Step 1: Failing test** — `zhihu` prints status and reuses `pipeline.run_zhihu_community` (mocked).
- [ ] **Step 2: Run → red.**
- [ ] **Step 3: Implement** — `pipeline.run_zhihu_community(run_paths, runner=None, force=False)` (persist + resume); `cmd_zhihu`; register parser + `COMMANDS`.
- [ ] **Step 4: Run → green.**
- [ ] **Step 5: Commit.**

### Task 4: Closeout

- [ ] Full suite + `git diff --check` + `bash scripts/uat_cli.sh`.
- [ ] Self code-review (no subagent tool in this session); fix Critical/Important.
- [ ] Push; report design/plan/code done, real-API regression deferred to quota.
