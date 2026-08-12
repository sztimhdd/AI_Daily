# AI_Daily V1 — final acceptance audit (2026-08-12)

Fresh remote-first acceptance audit of the V1 daily editorial pipeline,
executed 2026-08-12 (America/Halifax) from a temporary git worktree
rooted exactly at `origin/main` (`6127110`). The local operator
workspace was not modified. This audit re-checks previously recorded
evidence against the live remote and re-runs the deterministic suites;
it claims nothing beyond V1.

## Scope

V1 as defined by `docs/superpowers/plans/2026-08-12-daily-editorial-run.md`
and `docs/superpowers/specs/2026-08-12-daily-editorial-run-design.md`:
AIHOT topic candidates, one mandatory human topic gate, research →
outline → draft, optional cover, assembly, and GitHub Markdown
publication. No V1.5 scope is claimed: the separate narrative gate,
normalized evidence map, full RSS hardening/reporting, article-driven
illustration planning, the legacy visual library, multi-image
generation/publication/insertion, Automation, and email/WeChat adapters
remain deferred.

## Fresh evidence (re-run or re-read on 2026-08-12)

| # | Check | Result |
|---|-------|--------|
| 1 | Source-workspace suite `python3 -m unittest discover tests` | `Ran 208 tests` — OK (208/208) |
| 2 | Published-tree suite (temp worktree @ `origin/main`) | `Ran 195 tests` — OK (skipped=4) |
| 3 | Fixture UAT `scripts/uat_cli.sh` in temp worktree | 17/17 PASS |
| 4 | Fixture UAT in source workspace (recorded) | 17/17 PASS |
| 5 | Live AIHOT collection | 14 items; IDs/links exact-match API ground truth |
| 6 | Full real RSS catalog collection | 76 feeds requested, 58 ok, 18 failed (nonblocking), 439 items kept |
| 7 | Remote commits on GitHub `main` | `9b65a16` + `6127110` both present |
| 8 | Remote reread hash equality | 10/10 files byte-identical |
| 9 | Core V1 acceptance items | all PASS |

Details:

- Check 1 ran in the source workspace with bytecode writing disabled
  (`PYTHONDONTWRITEBYTECODE=1`); integrity snapshots before and after
  are identical (see Source workspace integrity below). The 208-test
  suite includes the 15 raw core-IP rebuild tests that can only run
  where the local-only JSONs exist.
- Check 2: 193 passed + 2 individual skips; 2 class-level skip markers
  cover the remaining 13 raw-rebuild tests (15 raw-rebuild skips
  total, 0 failures). The raw core-IP JSONs are local-only; the
  published tree tests use `knowledge/rss-catalog.json`.
- Checks 5–6 are the live-integrations UAT
  (`results/2026-08-12-live-integrations-uat.md`, cases 1 and 4):
  AIHOT 14 items stable across two ground-truth fetches; the RSS
  identity holds (`items_seen 3381 = kept 439 + duplicates 4 +
  out_of_window 2938`); per-feed failures are recorded and
  nonblocking (pipeline exit 0).
- Checks 7–8: `gh api` confirms commits
  `9b65a1664fbab811a0b46aee3e3e7ae803cf320e` (2026-08-12T22:37:50Z)
  and `6127110cdcb8b1111247de03d0d92ebbb7b0c594`
  (2026-08-12T22:39:58Z) on remote `main`; the diff between them is
  exactly `docs/verification/results/2026-08-12-github-publication.md`.
  A fresh reread of the 10 files tabulated in
  `results/2026-08-12-github-publication.md` (GitHub raw at
  `ref=main`) matches both the `origin/main` worktree copies and the
  SHA-256 values recorded in that report: `READBACK_ALL_EQUAL`, 10/10.
- Check 9 core V1 items, per `results/2026-08-12-codex-exec-uat.md`,
  `results/2026-08-12-fixture-uat.md`, and
  `results/2026-08-12-live-integrations-uat.md`: mandatory topic-gate
  refusal, fixture chain to `completed`, outline-edit regeneration
  without re-collect, deterministic redraft, two-date isolation, cover
  adoption (fixture) and cover-skip semantics, fail-fast collect with
  durable `last_error`, honest downstream refusals, all-RSS-fail
  nonblocking, `publish-mode: local-only` fallback, and publish
  verification against a real bare git remote (`tests/test_publish.py`:
  success records `publish-mode: remote`, `publish-verified:
  remote-reread`, `publish-sha256`).

## Documentation changes in this audit

- `docs/verification/README.md`: external UAT items 1 (live AIHOT),
  2 (GitHub publish + remote reread hash), and 3 (real RSS catalog)
  marked COMPLETE with links to their reports; items 4 (real ChatGPT
  cover export) and 5 (human topic gate in real chat) remain pending.
  Item 2's state-field wording corrected to the actual fields recorded
  by `src/ai_daily/publish.py` and asserted by `tests/test_publish.py`:
  `publish-mode: remote` and `publish-verified: remote-reread` (plus
  `publish-sha256`). Results index added.

## Pending items (not complete, not claimed)

- Optional — real ChatGPT cover export adoption: cover is optional in
  V1; fixture cover adoption is proven, but no real ChatGPT-exported
  image has been run through `cli cover` yet.
- Required — human topic gate in a real desktop chat: `cli candidates`
  → human choice → `cli choose-topic --choice N --direction ...` in a
  live desktop session. This has not been executed; desktop completion
  is not claimed. V1 acceptance is not final until this gate passes.

## Disclosures (local-only operator issues)

These are operator-workspace matters; they do not change the remote
evidence above and are disclosed without secret values.

1. Local source branch divergence: local `main`
   (`7ffe4da9d6bb5fb651223ef2114e4a01681022a3`, "chore: establish clean
   Codex project baseline") is ahead 1 / behind 2 of `origin/main`.
   Behind = exactly the two publication commits audited here; ahead =
   a local-only baseline commit that was never published. The operator
   workspace additionally carries staged-but-uncommitted V1 files and
   untracked local directories. Reconciling local `main` with
   `origin/main` is an operator decision outside this audit.
2. Credential disposition: the published tree contains no credentials
   (publication secret scan clean; `.gitignore` excludes `.local/`,
   `.env`, `.env.*`). AIHOT access is anonymous (no key); RSS fetches
   use public HTTP; GitHub authentication is the operator's
   keyring-managed credential, never printed or committed. Raw API
   headers and raw model responses remain under `.local/` (untracked).
   No secret value appears in this document.

## Source workspace integrity (this audit)

Snapshots taken before any audit work and re-taken after the
source-workspace suite run — identical:

- Local branch/HEAD: `main` @ `7ffe4da9d6bb5fb651223ef2114e4a01681022a3` (unchanged)
- `.git/index` SHA-256: `a47553bdede24bd4e1816e98c9f7e446842e2a1f7a728f6f418472dea6c912ac` (unchanged)
- Index entries (`git ls-files -s`) SHA-256: `660780f23caad69531f45c9812cd0327bf11d2b64b97fef43c0243a6133afe0d` (unchanged)
- `git status --porcelain` SHA-256: `4e5ddeb9b72a74ab5b50484d8c78f06ff61e9e839df920795363a31131779a01` (unchanged)

All audit writes were confined to the temporary worktree
`/tmp/ai-daily-docs-audit.1K218C/wt`; this docs-only commit is pushed
fast-forward onto `main` on top of `6127110`.
