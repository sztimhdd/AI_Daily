# AI Daily

AI Daily is being rebuilt as a Codex-operated pipeline for producing daily, deeply researched Chinese AI articles with publication-ready illustrations.

## Repository map

- `workflows/reference/` — the single authoritative n8n workflow used to understand legacy behavior.
- `src/` — future Codex pipeline implementation.
- `tests/` — automated checks for the new implementation.
- `outputs/` — approved article packages, grouped by publication date and article slug.
- `docs/` — architecture, operating instructions, decisions, and migration notes.
- `archive/` — read-only historical content, n8n assets, workflows, and retired tools.
- `.local/` — ignored runtime logs, caches, temporary files, candidate media, and credentials.

## Output package

Each future article belongs in `outputs/YYYY/MM/DD/<article-slug>/` and should contain `article.md`, `metadata.json`, `sources.md`, and an `images/` directory. Only final or intentionally versioned deliverables belong in Git; raw model responses and transient execution data belong in `.local/`.

## Current status

The new runtime has not been implemented. Until migration requirements are captured, treat `workflows/reference/公众号选题写稿配图一体化工作流.json` as reference evidence—not as a production runtime or a file to import blindly.
