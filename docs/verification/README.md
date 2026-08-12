# Verification scaffold

How the V1 daily editorial pipeline is verified, and what remains for
external user acceptance testing.

## Local verification (no network, no credentials)

Run from the repository root:

```bash
# 1. Full unit + integration suite (stdlib unittest, 208 tests)
python3 -m unittest discover tests

# 2. Deterministic fixture UAT through the real CLI (17 checks)
scripts/uat_cli.sh                                  # prints summary
scripts/uat_cli.sh docs/verification/results/<date>-fixture-uat.md  # saves it

# 3. Baseline structural checks
jq empty "workflows/reference/公众号选题写稿配图一体化工作流.json"
jq empty "[Atomic] Researcher_Skill.json"
jq empty "[Atomic] Topic_Survey_Skill.json"
jq empty "[Atomic] Universal Draft Writing.json"
jq empty "Long-Content-Writing.json"
git diff --check

# 4. Lint (byte-compile + static prohibition greps, see README.md "Lint")
python3 -m compileall -q src tests
```

Steps 1, 2, and 4 run identically in the published repository. Step 3
(the five `jq empty` baseline checks) applies only to the local
workspace: the raw core-IP JSONs and the legacy workflow reference
remain local-only, the published repository carries the compiled
knowledge assets under `knowledge/` (provenance retained), and the
deterministic tests use `knowledge/rss-catalog.json`.

Saved results live in `docs/verification/results/`:

- `2026-08-12-codex-exec-uat.md` — black-box UAT (sessions A/B/C/C2,
  findings F1–F4).
- `2026-08-12-fixture-uat.md` — deterministic fixture chain (17/17).
- `2026-08-12-live-integrations-uat.md` — live AIHOT + full real RSS
  catalog UAT.
- `2026-08-12-github-publication.md` — isolated publication with
  remote reread hash.
- `2026-08-12-final-acceptance-audit.md` — final acceptance audit of
  the V1 evidence.

## What the local checks prove

- Every stage's success path and at least one failure path (unit tests).
- Full fixture chain to `completed`, two-date isolation, gate refusal,
  cover/no-cover/invalid-cover, AIHOT failure → fixture resume,
  all-RSS-fail nonblocking, outline-edit regeneration without re-collect
  (`tests/test_pipeline_e2e.py`, `scripts/uat_cli.sh`).
- Publish verification logic against a real bare git remote
  (`tests/test_publish.py`) and honest `local-only` fallback.
- Immutable core-IP JSONs still parse (`jq empty` on all five).

## External UAT status (needs network / accounts / humans)

Three of five items are complete as of 2026-08-12. Remaining: the real
ChatGPT cover export (optional — cover is optional in V1) and the human
topic gate in a real desktop chat (required for V1 acceptance; desktop
completion is not claimed).

| # | Item | How to verify | Status |
|---|------|---------------|--------|
| 1 | Live AIHOT collection | `PYTHONPATH=src python3 -m ai_daily.cli collect --mode live --date <today>` | COMPLETE — [live integrations UAT](results/2026-08-12-live-integrations-uat.md), case 1 |
| 2 | Real GitHub publish + remote reread hash | `cli publish --repo-dir <clone> --remote-url <origin>` then check `publish-mode: remote`, `publish-verified: remote-reread`, and `publish-sha256` in state.md | COMPLETE — [GitHub publication](results/2026-08-12-github-publication.md) |
| 3 | Real RSS catalog fetch | `cli collect --mode live` with catalog URLs; inspect `rss-stats.json` per-feed results | COMPLETE — [live integrations UAT](results/2026-08-12-live-integrations-uat.md), case 4 |
| 4 | Real ChatGPT cover export | drop the exported `ChatGPT Image*.png` into a dir, `cli cover --source-dir <dir>` | pending |
| 5 | Human topic gate in real chat | `cli candidates`, then `cli choose-topic --choice N --direction ...` | pending |

External UAT writes only into the run's own sandbox/root; it never
modifies the five immutable JSONs or legacy artifacts.

## Failure semantics under test

- AIHOT unavailable → collect fails fast, stage `failed`, `last_error`
  set; later fixture/live resume clears the error. Failed attempts do
  not increment `collect_runs`.
- Any RSS feed failure → recorded in `rss-stats.json`/`failures`,
  pipeline continues (nonblocking).
- Invalid/missing cover → skipped with reason, assembly still completes.
- Remote unavailable/push fails/hash mismatch → `publish-mode: local-only`,
  never a fake success.
