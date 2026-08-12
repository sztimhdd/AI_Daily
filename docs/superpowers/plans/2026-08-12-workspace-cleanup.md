# Workspace Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Replace the stale nested workspace with a verified repository rooted at the outer `AI_Daily` directory.

**Architecture:** Rebuild from a fresh clone of `origin/main`, classify existing assets into active, archived, output, and local-only zones, then atomically promote the verified clone. Preserve the previous workspace as a sibling backup until post-promotion checks pass.

**Tech Stack:** Git, POSIX shell, Python standard library, JSON, Markdown

## Global Constraints

- Do not push or rewrite Git history.
- Preserve all GitHub content under archive paths.
- Delete only explicitly expired credentials and reproducible dependencies.
- Keep the supplied n8n workflow as the sole legacy behavior reference.

---

### Task 1: Build the synchronized staging repository

**Files:** Create a fresh sibling clone and capture the old workspace manifest.

- [x] Fetch and clone `origin/main`; verify staged `HEAD` equals `origin/main`.
- [x] Record the pre-cleanup workspace file hashes, excluding `.git` and `node_modules`.

### Task 2: Classify historical and active material

**Files:** Move remote content into `archive/`; create `workflows/reference/`, `src/`, `tests/`, `outputs/`, and `docs/`.

- [x] Archive remote articles, images, workflows, prompt data, infrastructure, and documentation.
- [x] Copy the supplied authoritative workflow and local retired article service into their designated paths.
- [x] Preserve the local draft and exclude reproducible dependencies.

### Task 3: Establish security and repository rules

**Files:** Create `.gitignore`, `AGENTS.md`, repository documentation, and redact retired source.

- [x] Replace hard-coded publisher and Apify tokens with environment-variable references.
- [x] Document archive immutability, article-package conventions, and ignored runtime data.
- [x] Repair absolute URLs for the moved historical article illustrations.

### Task 4: Verify and promote

**Files:** Entire staged repository and final workspace path.

- [x] Validate every JSON file, reference workflow structure, known-secret absence, article links, file counts, and `git diff --check`.
- [x] Rename the old workspace to a sibling backup and promote the staged clone to the original path.
- [x] Delete the expired credentials and `node_modules` by excluding them from the promoted workspace.
- [x] Re-run validation from the final path, commit the cleanup locally, and confirm the branch is ahead of—not pushed to—`origin/main`.
