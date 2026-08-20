# Repository Guidelines

## Project Structure

`workflows/reference/公众号选题写稿配图一体化工作流.json` is the sole authoritative description of the legacy workflow. New implementation belongs in `src/`, with matching tests in `tests/`. Final article packages belong in `outputs/YYYY/MM/DD/<article-slug>/`. Documentation belongs in `docs/`. Everything under `archive/` is read-only historical evidence and must not drive implementation unless a migration decision cites it explicitly.

## Development and Validation

No new runtime or test framework has been selected yet. Until one is introduced, validate the reference workflow with:

```bash
jq empty workflows/reference/公众号选题写稿配图一体化工作流.json
git diff --check
```

When adding a runtime, document install, test, lint, and run commands in `README.md` in the same change. Do not revive the archived n8n Docker image as the default environment.

## Output Conventions

Keep each article and its final media together. Use lowercase kebab-case article slugs. The article file is named by its title slug (`<slug>.md`, in the edition's own language — never the generic `article.md`); each edition's package also carries `metadata.json`, `sources.md`, and optional `images/cover.webp` plus numbered body images such as `images/01.webp`. Use PNG only when transparency or lossless fidelity is required. Store drafts, candidate images, raw responses, caches, logs, and temporary downloads under `.local/`, never in Git.

## Code and Tests

Follow the formatter and linter selected by the future runtime. Prefer small modules with explicit inputs and outputs. Name tests after observable behavior and mirror the `src/` structure. Every workflow stage must cover its successful path and at least one failure path before it becomes production-capable.

## Commits and Pull Requests

Use imperative, scoped commit subjects, for example `archive legacy n8n assets` or `add article package validator`. Pull requests must state the behavior changed, affected pipeline stages, validation performed, configuration changes, and any migration impact. Include rendered article or image previews when output changes.

## Security

Never commit tokens, credentials, private payloads, or unredacted model traces. Use environment variables or ignored files under `.local/`. Treat values found in Git history as exposed and rotate them; moving a file into `archive/` does not remove it from history.

## Agent skills

### Issue tracker

Issues and specs are local Markdown files under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the repository's five canonical triage role strings. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository using root `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.
