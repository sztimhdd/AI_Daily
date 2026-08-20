# AI_Daily V1 pipeline — live integrations UAT (2026-08-12)

Tracked summary of the live-integration user-acceptance run executed on
2026-08-12 against the V1 pipeline (`src/ai_daily/`). All raw evidence
lives under `.local/uat/20260812-181421/` as local raw logs (untracked,
not published); this document summarizes that session. Counts and
messages below are quoted from `00-RESULT.md` in that directory.

## Result

RESULT: PASS — all acceptance checks passed; 4 minor observations, no
blocking defects.

## Environment

- Repo: `/Users/hai/Projects/Desktop/AI_study/AI_Daily`
- Python: `Python 3.14.5`, stdlib-only pipeline
- Date: 2026-08-12 (America/Halifax); run id `AI-Daily/2026-08-12`
- Offline baseline earlier the same day: 202 unit tests OK; baseline
  jq/lint checks OK (see `.local/uat/20260812-181309/`, summarized in
  `2026-08-12-codex-exec-uat.md`)

## Case 1 — live AIHOT collection (anonymous API)

- API ground truth: `GET /api/v1/items?mode=selected&window=24h&limit=20`
  → HTTP 200, ETag `W/"v1-items-c14bd5bb493959a7"`, 14 items (stable
  across 2 fetches).
- `cli collect --mode live --date 2026-08-12 --force` → exit 0,
  `collect: collected (aihot=14 rss=439)`, wall time 55s
  (18:16:36 → 18:17:31).
- `state.md` marks the live source: note
  `collect: aihot 14 items (live); rss kept 439, failed feeds 18 (nonblocking)`;
  stage `topic_choice`; `collect_runs=1`; `last_error` empty.
- Evidence `aihot-items.json`: 14 items; IDs exact match in API order;
  0 link mismatches vs ground truth; all `origin=aihot`.

## Case 2 — candidates trace to returned IDs/links

- `cli candidates` → exit 0, exactly 3 candidates.
- 8/8 source URLs traced: 3 aihot sources → evidence item IDs → IDs
  present in API ground-truth response; 5 rss sources present in
  `rss-items.json`.
- Candidate 3 clusters 1 AIHOT + 5 RSS sources on one event (merge
  works live).

## Case 3 — AIHOT failure semantics (injected fetchers, real pipeline path)

- HTTP 503: `state.status=failed`,
  `last_error="collect: AIHOT unavailable: AIHOT API HTTP 503: Service Unavailable"`,
  `collect_runs=0`, no evidence files, `stage_log` FAILED.
- Network timeout: same semantics
  (`"AIHOT API request failed: operation timed out after 30.0s"`).
- `cli candidates` on both failed runs → exit 1,
  `error: no collected evidence; run the collect stage first`, zero
  candidates.

## Case 4 — full real RSS catalog collection (bounded timeouts)

- Catalog rebuild deterministic, byte-identical to
  `knowledge/rss-catalog.json`.
- Summary: 93 legacy entries = 91 source occurrences + 2 auxiliary
  services; 73 unique extractable (marker), 76 unique fetchable,
  15 dual-pool.
- Provenance: all 91 occurrences verified against their `(file, node)`
  in the local core-IP JSONs, 0 violations (raw sources remain
  local-only; the published catalog is `knowledge/rss-catalog.json`).
- Live fetch: `feeds_requested=76`, `feeds_ok=58`, `feeds_failed=18`
  (partial failure, pipeline exit 0 = nonblocking); per-feed errors
  listed in `rss-pool.md` 失败记录.
- `items_seen=3381` = kept 439 + duplicates 4 + out_of_window 2938
  (identity holds); undated kept=60 (matches stats);
  `sum(by_feed)=439=items_kept`; 37 feeds contributed.
- Compressed pool: 37 source sections, all within the 3-item cap;
  `window_hours=96`; 0 dated items beyond window in evidence.
- Timeouts bounded: aihot 30s; rss 15s/feed; observed total 55s vs
  worst case ~1170s.

## Observations (non-blocking)

1. `rss-stats.json` holds failure counts but the per-feed failure LIST
   only exists in `rss-pool.md` (markdown);
   `docs/verification/README.md` implies `rss-stats.json`/failures.
   The machine-readable failure list was not persisted in this run.
2. Multi-source candidates still print `缺少独立的第二来源验证` in
   `evidence_gaps` (candidate 3, n=6) — template wording contradicts
   n>1.
3. Data quirks passed through by design: one samaltman item titled
   `-`; one feed (becominghuman.ai) carries near-future timestamps;
   simonwillison link includes a `#atom-everything` fragment from the
   feed itself.
4. Dead/moved legacy feeds surfaced as recorded failures:
   openai.com/blog/rss/ (404), anthropic.com/news/rss (404),
   stability.ai (404), zhihu hot-list API (401), all 7 rsshub.app
   routes (403). Expected per catalog doc ("marker heuristic, not
   runtime verification").

## Side effects

- Writes confined to `.local/` (gitignored): `.local/runs/2026-08-12/`
  (live run state, stage `topic_choice`) and the UAT directory; no
  tracked files modified; `outputs/` and `articles/` untouched;
  nothing published.

## Evidence index (local raw logs, `.local/uat/20260812-181421/`)

- `00-RESULT.md` (session result this document summarizes)
- `02-collect-live.log`, `03-aihot-failure-cases.json`,
  `04-candidates-after-fail-503.log`, `04-candidates-after-fail-timeout.log`
- `05-catalog-provenance.json`, `06-live-evidence-checks.json`,
  `07-candidates-live.md`, `08-candidate-traceability.json`,
  `09-pool-window-checks.json`, `10-status-final.txt`
- `aihot-api-groundtruth.json`, `aihot-api-groundtruth-2.json`,
  `aihot-api-headers.txt`, `aihot-api-headers-2.txt` (API ground truth)
- `sandbox-fail-503/`, `sandbox-fail-timeout/` (failure-case run states)

These evidence paths are local raw logs in the operator workspace and
are not part of this repository.
