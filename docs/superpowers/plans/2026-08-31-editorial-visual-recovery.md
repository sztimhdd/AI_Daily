# Editorial Visual Recovery and LinkedIn Cover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make English visuals varied, replaceable, and resilient, then expose an AI-selected generated cover in every LinkedIn distribution kit.

**Architecture:** The visual planner produces 2–4 body images plus a separate `cover` entry. Its schema rejects repeated body treatments; the generation layer converts failed deterministic diagrams to a fact-bounded Gemini illustration. Assembly treats the visual cover as the package cover, while the LinkedIn kit reads only a successfully generated manifest entry and emits its GitHub raw URL.

**Tech Stack:** Python standard library, unittest, Vertex AI Gemini image lane, Markdown, GitHub raw assets.

**Spec:** `docs/superpowers/specs/2026-08-20-gemini-illustration-design.md`

## Global Constraints

- Do not send the whole article or external research to the image API.
- Visual prompts and diagram fallbacks may use only facts already in the article.
- A missing image or cover never blocks article assembly or LinkedIn copy.
- Never commit credentials, raw model traces, or unrelated worktree files.

---

### Task 1: Prevent stale or homogeneous article visuals

**Files:**
- Modify: `src/ai_daily/visuals.py`
- Test: `tests/test_visuals.py`

- [x] Write failing tests for rejecting three equal body styles and for removing an old package image block before a forced embed.
- [x] Run the two tests and confirm they fail against the old behavior.
- [x] Add `visual_mode` normalization plus the body diversity gate.
- [x] Add a raw-package-prefix image-block cleanup before deterministic embedding.
- [x] Run the two tests and confirm they pass.

### Task 2: Preserve the illustration when a diagram renderer fails

**Files:**
- Modify: `src/ai_daily/visuals.py`
- Test: `tests/test_visuals.py`

- [x] Write a failing test with a diagram generator error and an injected Gemini image response.
- [x] Run it and confirm one image is missing under the old behavior.
- [x] Keep a factual `fallback_image_prompt` in normalized diagram entries and use it only after a diagram failure.
- [x] Record `kind=image` and `fallback_from=diagram` in the manifest.
- [x] Run the test and confirm both assets generate.

### Task 3: Restore natural English editorial rhythm

**Files:**
- Modify: `src/ai_daily/draft_en.py`
- Modify: `knowledge/en-author-style.md`
- Test: `tests/test_draft_en.py`

- [x] Write prompt-contract assertions for 18–24 varied paragraphs, a dominant image, and no more than two consecutive standalone punch lines.
- [x] Confirm the old prompt fails the contract.
- [x] Replace the rigid 30-short-paragraph and 20-word rules with the new rhythm contract.
- [x] Mirror the contract in the author-style source of truth.
- [x] Run the test and confirm it passes.

### Task 4: Generate and deliver a LinkedIn cover

**Files:**
- Modify: `src/ai_daily/visuals.py`
- Modify: `src/ai_daily/linkedin.py`
- Modify: `src/ai_daily/assemble_en.py`
- Test: `tests/test_visuals.py`, `tests/test_linkedin.py`, `tests/test_assemble_en.py`

- [x] Write failing tests for a LinkedIn cover brief, Kit cover link, and package-cover metadata.
- [x] Confirm the old code fails all three contracts.
- [x] Require the planner to request one AI-selected cover and preserve it outside article embeds.
- [x] Read only a successful cover manifest plus existing file in the Kit; emit a raw GitHub URL and caption.
- [x] Promote the visual cover into package metadata.
- [x] Run the focused suite and confirm it passes.

### Task 5: Verification and release

**Files:**
- Modify: `docs/superpowers/specs/2026-08-20-gemini-illustration-design.md`
- Create: this plan

- [x] Run full unittest discovery with the repository-local topic-survey fixture available.
- [x] Run `git diff --check` and `scripts/uat_cli.sh`.
- [x] Review the staged diff, commit only the listed code, tests, and documentation, then push after fast-forward verification.
