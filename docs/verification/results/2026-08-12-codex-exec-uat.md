# AI_Daily V1 pipeline — Codex black-box UAT (2026-08-12)

Consolidated record of the black-box user-acceptance run executed on
2026-08-12 against the V1 pipeline (`src/ai_daily/`). All raw evidence
lives under `.local/uat/20260812-181309/` (untracked); this document is
the tracked summary. Nothing here is re-interpreted: commands, exit
codes, counts, hashes, and messages are quoted from that session.

## Environment

- Repo: `/Users/hai/Projects/Desktop/AI_study/AI_Daily`
- Python: `Python 3.14.5`
- Orchestrator: OpenAI Codex `v0.147.0-alpha.6.5`, model `gpt-5.6-sol`,
  approval `never`, sandbox `workspace-write` (per session transcript
  headers)
- UAT harness roots: `root-main` (sessions A/B), `root-rss` (sessions
  C/C2); run date `2026-08-12`
- Network: enabled for sessions C/C2 (live AIHOT + `file://` RSS fixtures)

## Verdict summary

| Workstream | Result | Notes |
|---|---|---|
| Session A — happy-path chain (13 steps) | PASS | gates, fixture collect, candidates, research→publish local-only |
| Session B — resume/regeneration/cross-date (S0–S7) | PASS | outline edit, deterministic redraft, cover adoption, date isolation |
| Session C — live AIHOT + broken RSS | FAIL | environment DNS failure blocked live AIHOT before RSS criteria could be exercised; safety behaviors observed |
| Session C2 — fixture resume + forced live collect + chain | FAIL | one defect: `rss-stats.json` lacked the machine-readable `failures` array (R2.2); all other checks PASS |
| Fixture UAT `scripts/uat_cli.sh` | PASS | 17 passed / 0 failed |
| Unit suite `python3 -m unittest discover tests` | PASS | `Ran 202 tests ... OK` |
| Baseline checks (5× `jq empty`, `git diff --check`, `compileall`) | PASS | all five core-IP JSONs parse |
| Lint prohibition greps | FAIL (false positives) | matched sanitizer source `assemble.py` and `__pycache__` bytecode |

## Session A — happy path with mandatory gates (OVERALL: PASS)

13/13 steps passed (`sessionA-report.md`), including the two
EXPECT-FAIL gate checks:

- Step 2 (research before any collect/choice): exit `1`,
  `error: topic_choice is a mandatory human gate; choose a topic (or use the fixture bypass) before research`
- Step 3: `collect: collected (aihot=14 rss=0)`
- Step 4: exactly 3 `## 候选` headings (verified by `grep -c`)
- Step 5: gate still blocks after candidates (exit `1`)
- Steps 7–12: research → outline → draft → cover skipped (optional) →
  assemble → `publish: mode=local-only`
- Final state: `- stage: completed`, `- last_error:` empty,
  `- publish-mode: local-only`, `- collect_runs: 1`

## Session B — resume, regeneration, cover, cross-date (OVERALL: PASS)

All stages S0–S7 passed with hash-level evidence (`sessionB-report.md`,
`command-output-b/`):

- S2: `regenerate-outline` rebuilt the draft from a human-edited outline;
  marker count `1`; article hash changed
  (`e9baa23f…` → `18995375…`); upstream `aihot-items.json` and
  `research.json` hashes unchanged; `collect_runs` stayed `1`.
- S4: removing `article.md` and re-running `draft` reproduced the exact
  S2 hash `18995375…` (deterministic redraft).
- S5: `research: resumed` and `collect: resumed` — no stage re-ran,
  `research.json` hash unchanged.
- S6: fixture 8×8 PNG adopted (`cover: ok … 8x8 png`), package gained
  `images/cover.png`, metadata `has_cover: true`, package article and
  final article identical (`cmp` exit 0).
- S7: second date (`2026-08-13`) ran the full chain on the same root;
  both run dirs exist, exactly two packages, `run_id: AI-Daily/2026-08-13`,
  and all four D1 hashes still match their S0/S2 values.

## Fixture UAT — `scripts/uat_cli.sh` (RESULT: PASS)

`uat-cli-sh.log` / `uat-cli-sh-summary.md`: full fixture chain to
`completed` in a temp sandbox, publish recorded `local-only` with
sha256 `e9baa23f…`, plus outline-edit regeneration checks.

```text
## summary
passed: 17
failed: 0
RESULT: PASS
```

## Baseline + suite (all PASS)

`baseline-checks.log`:

```text
jq OK: workflows/reference/公众号选题写稿配图一体化工作流.json
jq OK: [Atomic] Researcher_Skill.json
jq OK: [Atomic] Topic_Survey_Skill.json
jq OK: [Atomic] Universal Draft Writing.json
jq OK: Long-Content-Writing.json
git diff --check: clean
compileall OK
```

`unittest-full.log`: `Ran 202 tests in 1.989s — OK`.

The same log records the lint false positives that became finding F3:

```text
Binary file src/ai_daily/__pycache__/assemble.cpython-314.pyc matches
src/ai_daily/assemble.py:5:debug artifacts (``{[IMG_x]}``, ``{{ $json }}`` n8n expressions, bare
src/ai_daily/assemble.py:34:    re.compile(r"\{\{.*?\}\}", re.S),              # n8n/template expressions
```

## Session C — live AIHOT + broken RSS (OVERALL: FAIL, environment-caused)

Intended scenario: live AIHOT plus one broken and one valid RSS feed.
What happened (`sessionC-report.md`, `command-output-c/`):

- Step 2 live collect: exit `1`,
  `error: AIHOT unavailable: AIHOT API request failed: <urlopen error [Errno 8] nodename nor servname provided, or not known>` —
  DNS resolution of the AIHOT endpoint failed in this session.
- Collection aborted before RSS artifacts: `rss-stats.json` and
  `rss-items.json` were never created (steps 3–4 FAIL on missing files).
- Post-collection state: `- stage: collect`,
  `- last_error: collect: AIHOT unavailable: …` — fail-fast recorded.
- Candidates refused honestly: exit `1`, `CANDIDATES_COUNT=0`,
  `error: no collected evidence; run the collect stage first`.
- Fixture topic choice still worked (exit `0`).
- Research refused to fabricate: exit `1`,
  `error: no evidence pool; run the collect stage first (research never fabricates evidence)`;
  outline/draft/assemble skipped by the `&&` chain.

Safety behaviors proven: fail-fast collect with durable `last_error`,
honest downstream refusals, no fabricated evidence. The run could not
exercise the intended RSS acceptance criterion because the required live
AIHOT dependency failed first.

## Session C2 — fixture resume + forced live collect (OVERALL: FAIL, one defect)

Rerun of the same scenario on `root-rss`
(`sessionC2-report.md`, `command-output-c2/`):

- R1 fixture resume: PASS — exit `0`, `stage: topic_choice`,
  `last_error:` empty, `collect_runs: 1`.
- R2 forced live collect (`--mode live --force`, two `file://` RSS
  fixtures): PASS — exit `0`, `collect: collected (aihot=14 rss=2)`,
  `collect_runs: 2`, `last_error` empty; the broken feed did not block.
- R2.2 `rss-stats.json` failure entry: **FAIL** — counts were correct
  (`feeds_requested: 2`, `feeds_ok: 1`, `feeds_failed: 1`,
  `items_kept: 2`) but the file contained no `failures` key. Explicit
  check:

  ```text
  jq -e 'has("failures") and (.failures | type == "array") and
    (any(.[]; ((.url // .feed // .source // "") | contains("source_invalid.xml"))))' …/rss-stats.json
  → exit 1, output: false
  ```

  The failure was recorded only in `rss-pool.md`:
  `- file:///…/tests/fixtures/feeds/source_invalid.xml: parse failed: no element found: line 2, column 0`
- R3 chain to completion: PASS — candidates (exactly 3 headings),
  fixture topic choice, research, outline, draft, assemble all exit `0`;
  final state `stage: completed`, `collect_runs: 2`;
  `source-a.example.com` appears 3× in the final article (RSS evidence
  propagated).

## Findings and resolutions

- **F1 (C2/R2.2)** — `rss-stats.json` had no machine-readable failure
  details. Fixed: `rss_collect.collect()` now emits
  `stats["failures"]` (`[{"url", "error"}, …]`) with
  `feeds_failed == len(stats["failures"])` by construction, and the
  pipeline persists it (including the fixture-skip path); `rss-pool.md`
  keeps the human-readable record. Regressions:
  `test_stats_carry_machine_readable_failure_details`,
  `test_rss_stats_json_records_machine_readable_failure_details`, and
  the `failures` assertions in `test_all_rss_fail_is_nonblocking`
  (mirrors the UAT jq check).
- **F2 (C/step 8)** — research's empty-pool refusal raised without a
  durable failure record: the run's `stage_log` shows `-> research`
  (18:23:22) with no `FAILED at research` entry and `last_error` still
  pointing at collect. Fixed: `research.run()` calls
  `state.fail(run_paths, "research", …)` before raising. Regressions:
  `EmptyEvidencePoolStateTests` (failure recorded + recovery).
- **F3 (baseline log)** — README lint greps false-positived on the
  sanitizer source (`assemble.py` must literally name the n8n artifacts
  it strips) and on `__pycache__` bytecode. Fixed: README commands now
  use `--exclude-dir=__pycache__` (both greps) and `--exclude=assemble.py`
  (prohibition grep); verified clean on the tree and still detecting a
  planted forbidden adapter in a scratch copy.
- **F4 (fixture-UAT candidates output)** — evidence-gap wording said
  `目前只有 N 个来源报道，缺少独立的第二来源验证。` for any cluster
  size, claiming a missing second source even when N > 1. Fixed in
  `topics._build_candidate()` with context-aware wording keyed on the
  number of independent sources. Regressions:
  `test_multi_source_cluster_gap_does_not_claim_missing_second_source`,
  `test_single_source_cluster_gap_still_flags_missing_second_source`.

## Evidence index (`.local/uat/20260812-181309/`)

- Session reports: `sessionA-report.md`, `sessionB-report.md`,
  `sessionC-report.md`, `sessionC2-report.md` (+ `*-last.md`,
  `*-transcript.log`)
- Command captures: `command-output/` (A), `command-output-b/`,
  `command-output-c/`, `command-output-c2/`
- Harness + checks: `run-uat.sh`, `uat-cli-sh.log`,
  `uat-cli-sh-summary.md`, `baseline-checks.log`, `unittest-full.log`
- Run-state snapshots: `root-main/.local/runs/…`, `root-rss/.local/runs/…`
