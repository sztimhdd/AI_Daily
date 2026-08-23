# KG Lane Query & Relevance Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the KG lane's observed root cause — queries aim at the news event instead of the mechanism — via a mechanism query derived from the OSINT tech summary, a free fts probe that skips wasteful syntheses, a relevance gate on the report, and a persistent query cache.

**Architecture:** `knowledge.py` gains `_mechanism_concept()`, `_relevance()`, and refactored `fetch_background(topic, client, query, tech_summary, cache_dir, max_polls)`: concept = explicit query or mechanism concept (tech_engineering summary) or first research query or title; fts probe decides whether to spend the 1–4 min synthesis; the report is gated for "no data" signals; results are cached by query hash under `.local/knowledge-cache/`. `research.run_initial` passes the tech_engineering module summary + cache dir; `persist_background` passes the cache dir.

**Tech Stack:** Python stdlib, existing unittest suite, existing knowledge.py / research.py.

**Spec:** Observed failures: 08-24 auto-query "across claude claude.ai code cowork errors" → fts `[no-results]` yet kg_search synthesized off-target Claude-Code content; 08-21 event-title query → "do not have enough information". Manual mechanism query ("speculative decoding …") produced the 7.7k-char high-value synthesis.

## Global Constraints

- Never raise; degrade honestly with a `relevant` flag.
- fts probe result must not be fabricated: `[no-results]` skips the synthesis.
- Mechanism concept is derived deterministically (no LLM call).
- All verification via injectable runners + replayed real responses; no new real API calls.

---

### Task 1: mechanism concept + relevance gate + fts-probe fetch

**Files:** `src/ai_daily/knowledge.py`, `tests/test_knowledge.py`

- [ ] **Step 1: Failing tests**

```python
def test_mechanism_concept_prefers_tech_summary(self):
    topic = {"title": "Claude 宕机", "research_queries": ["q1"]}
    concept = knowledge._mechanism_concept(topic, tech_summary="依赖拓扑、根因与回滚")
    self.assertIn("依赖拓扑", concept)

def test_relevance_flags_no_data(self):
    self.assertFalse(knowledge._relevance("[no-results]", ""))
    self.assertFalse(knowledge._relevance("hit", "I do not have enough information to answer."))
    self.assertFalse(knowledge._relevance("hit", "short"))
    self.assertTrue(knowledge._relevance("hit", "## Deep\nSubstantive mechanism synthesis of useful length."))

def test_fetch_skips_synthesis_when_fts_misses(self):
    calls = {"synth": 0}
    class C:
        def fts_search(self, q, limit=5, lang="zh-CN"): return "[no-results]"
        def synthesize(self, q, max_polls=8): calls["synth"] += 1; return {"status": "completed", "report": "x"}
    result = knowledge.fetch_background({"title": "T"}, client=C())
    self.assertEqual(result["status"], "degraded")
    self.assertFalse(result["relevant"])
    self.assertEqual(calls["synth"], 0)

def test_fetch_relevant_when_report_substantive(self):
    class C:
        def fts_search(self, q, limit=5, lang="zh-CN"): return "draft model 机制"
        def synthesize(self, q, max_polls=8): return {"status": "completed", "report": "## Deep\n" + "mechanism " * 60}
    result = knowledge.fetch_background({"title": "T"}, client=C())
    self.assertEqual(result["status"], "completed")
    self.assertTrue(result["relevant"])

def test_fetch_caches_by_query(self):
    calls = {"n": 0}
    class C:
        def fts_search(self, q, limit=5, lang="zh-CN"): calls["n"] += 1; return "hit"
        def synthesize(self, q, max_polls=8): return {"status": "completed", "report": "r" * 400}
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as tmp:
        result = knowledge.fetch_background({"title": "T"}, client=C(), cache_dir=tmp)
        result2 = knowledge.fetch_background({"title": "T"}, client=C(), cache_dir=tmp)
    self.assertEqual(calls["n"], 1)
    self.assertTrue(result2.get("cached"))
```

- [ ] **Step 2: Run → red.**
- [ ] **Step 3: Implement** — `_mechanism_concept(topic, tech_summary)` (strip URLs, take first 160 chars; fallbacks); `_relevance(fts, report)`; refactor `fetch_background` with fts-probe + relevance + cache (sha256 of the concept, `cached` flag).
- [ ] **Step 4: Run → green.**
- [ ] **Step 5: Commit.**

### Task 2: wire tech_summary + cache dir through research

**Files:** `src/ai_daily/research.py`, `src/ai_daily/knowledge.py` (`persist_background`), tests

- [ ] **Step 1: Failing tests** — a fake kg client records the fts query; `run_initial` with a `tech_engineering` module summary produces a concept derived from it; `persist_background(cache_dir=...)` writes/reads the cache.
- [ ] **Step 2: Run → red.**
- [ ] **Step 3: Implement** — `run_initial` extracts the tech_engineering summary and passes `tech_summary=` + `cache_dir=.local/knowledge-cache`; `persist_background(..., cache_dir=None)` defaults to run root's cache and passes through.
- [ ] **Step 4: Run → green.**
- [ ] **Step 5: Commit.**

### Task 3: replay real cached KG responses through the relevance gate

- [ ] Unit-level replay: feed the real 08-24 report text ("Errors Across the Claude Ecosystem…") → assert `relevant` is True (substantive) and that with fts `[no-results]` the synthesis is skipped.
- [ ] Full suite + `git diff --check` + `bash scripts/uat_cli.sh`.
- [ ] Self code-review; push; report evidence (real 08-24 fts `[no-results]` would now skip the wasteful synthesis).
