# Workspace Cleanup Design

## Goal

Create one Git-rooted workspace that matches the latest GitHub state, separates historical artifacts from active development, and gives future Codex-generated articles a deterministic package layout.

## Structure

Active development uses `src/`, `tests/`, `docs/`, and `workflows/reference/`. Approved deliverables use `outputs/YYYY/MM/DD/<article-slug>/`. Existing remote articles, images, n8n assets, old workflows, retired infrastructure, and old tools are retained under typed `archive/legacy-*` directories. Runtime-only state uses ignored `.local/` paths.

## Migration

Build a clean clone from `origin/main`, move existing assets into archive paths, copy the user-designated workflow into `workflows/reference/`, redact embedded credentials, repair moved article image URLs, and verify counts, JSON syntax, hashes, ignore behavior, and Git ancestry. Promote the verified clone to the original outer path only after renaming the old workspace to a recoverable sibling backup.

## Safety

Do not merge into the stale nested checkout, rewrite Git history, push automatically, or place credentials in the repository. Delete only the two explicitly expired credential files and reproducible `node_modules/`. Preserve the old workspace backup until the promoted repository passes final verification.
