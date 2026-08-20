# Verification scaffold

How the V1 daily editorial pipeline is verified, and what remains for
external user acceptance testing.

## Local verification (no network, no credentials)

Run from the repository root:

```bash
# 1. Full unit + integration suite (stdlib unittest, 254 tests in the
#    local source workspace; the published tree runs the same suite
#    with skips where the raw core-IP JSONs are intentionally absent)
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

Saved results live in `docs/verification/results/`.

## What the local checks prove

- Every stage's success path and at least one failure path (unit tests).
- Full fixture chain to `completed`, two-date isolation, gate refusal,
  cover/no-cover/invalid-cover, AIHOT failure → fixture resume,
  all-RSS-fail nonblocking, outline-edit regeneration without re-collect
  (`tests/test_pipeline_e2e.py`, `scripts/uat_cli.sh`).
- Publish verification logic against a real bare git remote
  (`tests/test_publish.py`) and honest `local-only` fallback.
- Immutable core-IP JSONs still parse (`jq empty` on all five).
- Unattended simulated topic choice: gate bypass, verbatim
  title/slug preservation, default-empty direction, out-of-range
  refusal, and resume without re-collect
  (`tests/test_topics.py`, `tests/test_pipeline.py`,
  `tests/test_cli.py`).

## Unattended mode

The topic gate has an unattended simulated path:
`cli choose-topic --simulate [--choice N]` records
`topic_choice: simulated`, keeps the ranked candidate's title/slug
verbatim, defaults the direction to empty, and writes the stage_log
note `topic choice: simulated (unattended mode, candidate N)`
(`--simulate` without `--choice` auto-selects candidate 1, the
top-ranked editorial candidate). `require_choice` accepts simulated
choices, and resume never re-collects. Combining `--simulate` with
`--fixture` is a usage error (exit 2). First real use: the
2026-08-13 live unattended run
([results](results/2026-08-13-unattended-uat.md)).

## External UAT status (needs network / accounts / humans)

| # | Item | How to verify | Status |
|---|------|---------------|--------|
| 1 | Live AIHOT collection | `PYTHONPATH=src python3 -m ai_daily.cli collect --mode live --date <today>` | COMPLETE — [live integrations UAT](results/2026-08-12-live-integrations-uat.md), re-exercised live by the [2026-08-13 unattended run](results/2026-08-13-unattended-uat.md) |
| 2 | Real GitHub publish + remote reread hash | `cli publish --repo-dir <clone> --remote-url <origin>` then check `publish-mode: remote`, `publish-verified: remote-reread`, and `publish-sha256` in state.md | COMPLETE — [GitHub publication](results/2026-08-12-github-publication.md) |
| 3 | Real RSS catalog fetch | `cli collect --mode live` with catalog URLs; inspect `rss-stats.json` per-feed results | COMPLETE — [live integrations UAT](results/2026-08-12-live-integrations-uat.md), re-exercised live by the [2026-08-13 unattended run](results/2026-08-13-unattended-uat.md) |
| 4 | Real ChatGPT cover export | drop the exported `ChatGPT Image*.png` into a dir, `cli cover --source-dir <dir>` | UNAVAILABLE / NONBLOCKING — [ChatGPT cover UAT](results/2026-08-12-chatgpt-cover-uat.md): no reachable logged-in ChatGPT Web session; not executed |
| 5 | Human topic gate in real chat | `cli candidates`, then `cli choose-topic --choice N --direction ...` | COMPLETE — [desktop human-gate UAT](results/2026-08-12-desktop-human-gate-uat.md): choice 3 recorded as `topic_choice: human` (empty direction); resumed without re-collect to `completed`; article published + reread-verified |

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
