# English Draft + Quality Gate + Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the English full draft from the evidence package (not translation), gate it through the bilingual editing quality layer, and package it to `outputs/YYYY/MM/DD/<slug>/` + `articles/<date>-<slug>-en.md`, coexisting with the Chinese path.

**Architecture:** English-first additive path alongside the existing deterministic Chinese draft/assembly. Codex (injectable `codex_runner`) writes the English draft from the 06 evidence package + chosen narrative; Python runs the deterministic quality gate (deslop EN + evidence-boundary + rhythm checks). `draft_en`/`assemble_en` mirror `draft`/`assemble`.

**Tech Stack:** Python 3 stdlib only (`unittest`, `argparse`, `re`, `json`, `pathlib`). No new runtime dependencies.

**Spec:** `docs/superpowers/specs/2026-08-14-bilingual-editing-quality-layer.md` (quality layer); `docs/superpowers/specs/2026-08-14-v2-orchestration-and-delivery.md` (§5 English-first loop); tickets `.scratch/v2-mvp/issues/07-*.md`, `08-*.md`.

## Global Constraints

- English edition is **never a translation** of Chinese; it is organized from the evidence package.
- Input gate: sufficiency audit verdict must be `sufficient` (or a conservative downgrade the user accepts) before drafting; unaudited claims never enter the body.
- EN length 800–1200 words; ≤3 sentences per paragraph; cold kicker (no uplift ending).
- Facts / inference / opinion must stay distinguishable; every sourced claim carries inline `[title](URL)`; walled sources (zhihu/mp.weixin) are downgraded by fetch status, never asserted as certain.
- Quality gate only checks and rejects; it never silently rewrites.
- Package filenames are language-suffixed for English (`-en`) so the Chinese package (`article.md`/`sources.md`/`metadata.json`) coexists without conflict.

## File Structure

- Create `knowledge/en-author-style.md` — EN voice + rhythm contract (Lead Tech Editor, News Peg/Nut Graf/Smart Brevity/Kicker, 3-Sentence Rule, 1–2 cold parenthetical `(*...*)`, Markdown Purity).
- Modify `src/ai_daily/deslop.py` — add English blacklists + `check_text_en` (8 categories mirrored).
- Create `src/ai_daily/quality.py` — deterministic English quality gate (verdicts `pass`/`pass_with_notes`/`revise`/`evidence_recovery`).
- Create `src/ai_daily/draft_en.py` — English draft stage (prompt + codex runner + validation + gate).
- Create `src/ai_daily/assemble_en.py` — English packaging (article-en.md + sources-en.md + metadata-en.json + `articles/<date>-<slug>-en.md`).
- Modify `src/ai_daily/paths.py` — `final_article_en_path`.
- Modify `src/ai_daily/pipeline.py` — `run_draft_en` / `run_assemble_en`.
- Modify `src/ai_daily/cli.py` — `draft-en`, `assemble-en` subcommands.
- Modify `src/ai_daily/topics.py` — stop-word expansion + URL-aware `same_event` (BISC fix).
- Tests mirror `src/` in `tests/`.

## Tasks

### Task 1: English de-AI check (deslop EN mode)

**Files:** Modify `src/ai_daily/deslop.py`; Test `tests/test_deslop.py`.

- [ ] Write failing test `test_check_text_en_detects_leverage` + one clean case.
- [ ] Implement `check_text_en` (8 EN categories) reusing existing scanners.

### Task 2: Deterministic English quality gate

**Files:** Create `src/ai_daily/quality.py`; Test `tests/test_quality.py`.

- [ ] Verdict types, word count 800–1200, ≤3 sentences/paragraph, link presence, walled downgrade marker, AI-trace tag, placeholder, bold spacing.
- [ ] `pass` / `pass_with_notes` / `revise` / `evidence_recovery` semantics.

### Task 3: English draft stage

**Files:** Create `src/ai_daily/draft_en.py`; Test `tests/test_draft_en.py`.

- [ ] Input gate (sufficiency sufficient), prompt build, codex runner injection, output validation (H1 + links), write `article-en.md`, gate on `quality.check_en`.

### Task 4: English package

**Files:** Create `src/ai_daily/assemble_en.py`; Modify `src/ai_daily/paths.py`, `pipeline.py`, `cli.py`; Tests `tests/test_assemble_en.py`, `tests/test_paths.py`, `tests/test_cli.py`.

- [ ] Package `article-en.md`/`sources-en.md`/`metadata-en.json` + `articles/<date>-<slug>-en.md`; `-en` path coexists with `-zh`.

### Task 5: Clustering false-merge fix (BISC)

**Files:** Modify `src/ai_daily/topics.py`; Test `tests/test_topics.py`.

- [ ] Expand `_STOP_TOKENS` with English function words; regression test reproducing the BISC false merge; URL-aware tightening on the weak 2-token path.

## Testing

```bash
python3 -m unittest discover -s tests -q
git diff --check
bash scripts/uat_cli.sh
```
