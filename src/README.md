# Source

V1 of the daily editorial pipeline lives in `ai_daily/`. Python standard
library only; no third-party imports are allowed (enforced by the lint
greps documented in the root README).

## Modules

| Module | Stage / responsibility |
|---|---|
| `paths.py` | Date-validated run paths (work dir, package dir, final article). |
| `state.py` | `state.md` read/write: stage, counters, artifacts, stage_log, errors. |
| `aihot.py` | AIHOT collection (fixture + live), controlled failure on bad payloads. |
| `rss_catalog.py` | Provenance-aware catalog (93 entries, 73 unique extractable URLs, deterministic). |
| `rss_collect.py` | Feed fetch/parse/filter/dedup/stats/pool; per-feed failures nonblocking, persisted as machine-readable `stats["failures"]`. |
| `topics.py` | 3 rich candidates, same-event clustering, human gate + fixture bypass. |
| `research.py` | Key-question research over the evidence pool only; no fabrication. |
| `outline.py` | Editable 8-field outline; bullets map 1:1 to draft headings. |
| `draft.py` | Fact-backed draft following outline/research/author style; passes deslop. |
| `deslop.py` | Executable 8-category remove-AI-slop contract. |
| `cover.py` | Optional cover: PNG/JPEG/WebP byte validation, ChatGPT export locator. |
| `assemble.py` | Package + final article validation and mapping. |
| `publish.py` | Git publish with remote reread hash; honest `local-only` fallback. |
| `pipeline.py` | Stage orchestration, gates, resume, fixture E2E. |
| `cli.py` | Subcommands (`init ... run`), exit codes 0/1/2. |

## Conventions

- Small modules with explicit inputs and outputs; stage functions take a
  `RunPaths` and return plain dicts/results.
- Network access only through injectable `fetch`/transport callables so
  every failure path is testable offline.
- Runtime state under `.local/` only; durable outputs under `outputs/`
  and `articles/`.
