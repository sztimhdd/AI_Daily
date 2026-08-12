# Workspace cleanup baseline

Date: 2026-08-12

This repository was rebuilt from the latest `origin/main` to make `/Users/hai/Projects/Desktop/AI_study/AI_Daily` the sole Git root. The previous nested checkout was 575 commits behind the remote and was not merged in place.

## Decisions

- Existing GitHub articles and images are historical published content and live under `archive/legacy-content/`.
- The latest supplied n8n export is the sole authoritative legacy behavior reference and lives under `workflows/reference/`.
- Other workflows, n8n infrastructure, old documentation, generated media, and prompt datasets are archived and read-only.
- The retired Express publisher is archived with hard-coded tokens replaced by environment-variable references.
- Future approved articles keep their body, metadata, sources, and final images in one dated package under `outputs/`.
- Runtime logs, caches, raw model responses, candidate media, temporary downloads, and credentials live under ignored `.local/` paths.
- Expired Google credential files and reproducible `node_modules/` dependencies were intentionally excluded from the rebuilt workspace.

## Reference integrity

The user-supplied source workflow had SHA-256 `28e3ca0de66b92d600a17f2d74e73de52204b552a5682c5308079db5b7173c30`. The committed reference preserves its workflow structure but replaces two occurrences of an embedded Apify token with `${APIFY_API_TOKEN}`. The original source file remains outside this repository and must not be committed.

## Git synchronization

The cleanup starts from remote commit `15527dced5440845892e93ca49759c5a6a3b473a`. No force push, history rewrite, or automatic push is part of this cleanup. Git history retains the original paths and content.
