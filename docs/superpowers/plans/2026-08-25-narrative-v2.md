# Narrative v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make 04 generate genuinely different, human-sounding narrative candidates for different news types without weakening evidence boundaries.

**Architecture:** Keep the existing evidence inventory and artifact format seam, but make narrative form, reader move and ending mode explicit fields. Route typed evidence to eligible forms, compile a form-specific prompt, and validate candidate-pair distinctness before persisting the HITL artifact. Existing consumers read old fields unchanged; new fields are additive.

**Tech Stack:** Python 3 standard library, unittest, Markdown local tracker, existing Telegram adapter and CLI.

**Spec:** `docs/superpowers/specs/2026-08-25-narrative-v2-design.md`

## Global Constraints

- Unsupported claims never enter a candidate or article body.
- `decision_rule` is required only for action-oriented forms.
- Do not touch unrelated Stripe/WIP files.
- KG background remains secondary context and never event evidence.
- Network-shaped tests remain injectable; real Telegram is only the final acceptance probe.

---

### Task 1: Typed contract and evidence routing

**Files:**
- Modify: `src/ai_daily/narrative.py`
- Modify: `knowledge/narrative-contract.md`
- Test: `tests/test_narrative.py`

**Interfaces:**
- Produces additive candidate fields `narrative_form`, `reader_move`, `ending_mode`.
- Keeps `evidence_inventory()`, `route_archetypes()`, `require_narrative()` and old artifact fields callable by existing consumers.

- [x] Write failing tests for valuation-only, acquisition-rumor and optional decision rule behavior.
- [x] Run the focused tests and confirm they fail for the intended missing behavior.
- [x] Implement typed routing and conditional schema validation.
- [x] Run the focused tests and confirm they pass.
- [x] Update the contract documentation.

### Task 2: Form-specific prompt and candidate-pair quality gate

**Files:**
- Modify: `src/ai_daily/narrative.py`
- Test: `tests/test_narrative.py`

**Interfaces:**
- Adds a deterministic pair validator used by `run()` before artifact persistence.
- Prompt output remains one JSON object with exactly two candidates.

- [x] Write failing tests for the absence of universal Decision rules and same-advice rejection.
- [x] Run the focused tests and confirm the failures are expected.
- [x] Implement form-specific prompt sections, optional endings and pair validation.
- [x] Run focused narrative tests.

### Task 3: HITL display and documentation contract

**Files:**
- Modify: `src/ai_daily/tui.py`
- Modify: `knowledge/narrative-contract.md`
- Test: `tests/test_tui.py`

**Interfaces:**
- Existing `render_narrative_candidates(candidates, color=False)` remains callable.
- Output includes readable form/move/ending fields and omits absent decision rules.

- [x] Write a failing rendering test.
- [x] Run it red.
- [x] Implement the smallest display change.
- [x] Run TUI tests green.

### Task 4: Integrated acceptance

**Files:**
- Modify only if required by the red/green findings.
- Test: existing narrative, pipeline, Telegram and CLI suites.

- [x] Run all focused tests.
- [x] Run the full test suite.
- [x] Run `git diff --check` and `scripts/uat_cli.sh`.
- [x] Run a fresh narrative artifact through Telegram status receipt and the next full-text stage.
- [x] Request independent code review and resolve important findings.
- [ ] Commit the final verified change.
