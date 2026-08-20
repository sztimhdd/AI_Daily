# GitHub publication verification — V1 delivery (2026-08-12)

Safe isolated publication of the self-contained V1 set to
`https://github.com/sztimhdd/AI_Daily.git` (`main`), executed from a
temporary git worktree rooted exactly at the previous `origin/main`.
The local operator workspace was not modified (HEAD, index, and status
snapshots taken before and after are identical).

## Publication facts

- Remote: `https://github.com/sztimhdd/AI_Daily.git`
- Previous `origin/main`: `15527dced5440845892e93ca49759c5a6a3b473a`
- First V1 commit (this delivery): `9b65a1664fbab811a0b46aee3e3e7ae803cf320e`
- Parent of first commit: `15527dced5440845892e93ca49759c5a6a3b473a` (fast-forward, never forced)
- Remote commit date: `2026-08-12T22:37:50Z`
- Remote tree of first commit: `3857d3f0cda39e3e371d279ec39a7a305af709a3`
- Push form: `git push origin HEAD:main` → `15527dc..9b65a16  HEAD -> main`
- Worktree: temporary branch `codex/v1-publication-20260812` under
  `/private/tmp/ai-daily-pub.N5IIt8/wt`, removed after verification.

## Staged and committed paths (63)

`.gitignore`, `CONTEXT.md`, `README.md` (modified),
`articles/2026-08-14-ai-search-budget-research-cost-zh.md`,
`docs/research/codex-automation-stateful-workflows.md`,
`docs/superpowers/plans/2026-08-12-daily-editorial-run.md`,
`docs/superpowers/specs/2026-08-12-daily-editorial-run-design.md`,
`docs/verification/README.md`,
`docs/verification/results/2026-08-12-codex-exec-uat.md`,
`docs/verification/results/2026-08-12-fixture-uat.md`,
`docs/verification/results/2026-08-12-live-integrations-uat.md`,
`knowledge/author-style.md`, `knowledge/remove-ai-slop.md`,
`knowledge/research-contract.md`, `knowledge/rss-catalog.json`,
`outputs/2026/08/14/ai-search-budget-research-cost/{article-outline.md,article.md,metadata.json,research.md,sources.md,state.md,topic-candidates.md}`,
`scripts/uat_cli.sh`, `src/README.md`,
`src/ai_daily/{__init__,aihot,assemble,cli,cover,deslop,draft,outline,paths,pipeline,publish,research,rss_catalog,rss_collect,state,topics}.py`,
`tests/README.md`, `tests/test_{aihot,assemble,cli,cover,deslop,draft,outline,paths,pipeline,pipeline_e2e,publish,research,rss_catalog,rss_collect,state,topics}.py`,
`tests/fixtures/{aihot_items.json,topic_fixture.json}`,
`tests/fixtures/feeds/{source_a.xml,source_b.xml,source_dc.xml,source_invalid.xml}`

## Explicitly excluded (never copied or staged)

- `AGENTS.md`
- `workflows/reference/**` (legacy n8n workflow reference)
- `archive/**`
- `[Atomic] Researcher_Skill.json`, `[Atomic] Topic_Survey_Skill.json`,
  `[Atomic] Universal Draft Writing.json`, `Long-Content-Writing.json`
  (raw core-IP JSONs)
- `automation/**`, `outputs/2026/08/12/**`, `.local/**`
- credentials, raw API headers, raw model responses

## Publication-scope adaptations (worktree only)

- `tests/test_rss_catalog.py` gained explicit skip guards: when the raw
  core-IP JSONs are absent (published repository), the 15 raw-rebuild
  tests are skipped with the reason `raw core-IP JSONs are local-only;
  published repo tests use knowledge/rss-catalog.json`. The local
  workspace copy is unchanged and still runs all 208 tests.
- `README.md` gained a "Publication scope" section and a baseline-check
  applicability note; `docs/verification/README.md` gained a note that
  the five `jq empty` baseline checks apply to the local workspace only.
- `.gitignore` added (absent on `origin/main`): `.local/`, env files,
  Python bytecode/caches, temp/editor files, local draft/media dirs.
- `docs/verification/results/2026-08-12-live-integrations-uat.md`
  created as a tracked summary of the existing local raw logs under
  `.local/uat/20260812-181421/` (no fabrication; evidence paths cited
  as local raw logs).

## Verification run in the temp worktree (before commit)

- `python3 -m unittest discover tests`: `Ran 195 tests ... OK (skipped=4)`
  (193 passed + 2 individual skips; 2 class-level skip markers cover the
  remaining 13 raw-rebuild tests — 15 raw-rebuild skips total, 0 failures)
- `scripts/uat_cli.sh`: `passed: 17, failed: 0, RESULT: PASS`
- `python3 -m compileall -q src tests`: OK
- stdlib-only import grep and n8n/automation prohibition greps: clean
- `git diff --check`: clean
- `jq empty` on `knowledge/rss-catalog.json` and all committed JSON
  fixtures/metadata: valid
- Secret scan (token formats, literal key assignments, private keys)
  over the worktree: clean

## Remote reread at exact commit (gh API)

Method: `gh api repos/sztimhdd/AI_Daily/contents/<path>?ref=9b65a1664fbab811a0b46aee3e3e7ae803cf320e`
with `Accept: application/vnd.github.raw+json`, saved to scratch files,
SHA-256 compared against the committed worktree copy.
Browse form: `https://github.com/sztimhdd/AI_Daily/blob/9b65a1664fbab811a0b46aee3e3e7ae803cf320e/<path>`

| Path | SHA-256 (local == remote) | Result |
|---|---|---|
| `articles/2026-08-14-ai-search-budget-research-cost-zh.md` | `e9baa23f94c40370cc0ca59aa9b793e2c974b953ce1c1abc95ac057f39826bb8` | EQUAL |
| `outputs/2026/08/14/ai-search-budget-research-cost/state.md` | `012c4ae5f5e1da6b9af2d5cdbbbff1aae9ad98e4d1703e838090b3d119d56191` | EQUAL |
| `outputs/2026/08/14/ai-search-budget-research-cost/research.md` | `05950ab9809e7ac3cf891dc9d0bb03d048edf9e425ddf5eba83760b5d4573988` | EQUAL |
| `outputs/2026/08/14/ai-search-budget-research-cost/article-outline.md` | `b724a4402d7134d2b04fbeee538a2827686a63df9c35640db114c92756875d1f` | EQUAL |
| `outputs/2026/08/14/ai-search-budget-research-cost/article.md` | `e9baa23f94c40370cc0ca59aa9b793e2c974b953ce1c1abc95ac057f39826bb8` | EQUAL |
| `src/ai_daily/pipeline.py` | `0fa8f25c6216b81b2cd1f9eb093c5148b8f1b56d3f966b0670d06ec4fc1f0a4c` | EQUAL |
| `knowledge/remove-ai-slop.md` | `f9edd4fabfda77201c6c84f528ad46e06f2d694c2b149ec204e5f42409353505` | EQUAL |
| `docs/verification/results/2026-08-12-fixture-uat.md` | `4ef619b9e60c4b643dca284f1428c378809eca409d17eff29f6ffa1b99438a96` | EQUAL |
| `docs/verification/results/2026-08-12-codex-exec-uat.md` | `a9475743076a52bdf31414145ca975277052d8fc8abbebb138d5da5c5b1d1c3e` | EQUAL |
| `docs/verification/results/2026-08-12-live-integrations-uat.md` | `bfb0508eb6a347739f38c0b0288c0d94ce51975fe01cfbab3210921b93f650bf` | EQUAL |

Result: `READBACK_ALL_EQUAL` — 10/10 files byte-identical local vs remote.

Note: package `article.md` and the final article share hash
`e9baa23f…` by design (assembly maps the package article verbatim to
`articles/`).

## Source workspace integrity

Snapshot taken before work began and re-checked after the push:

- Local branch/HEAD: `main` @ `7ffe4da9d6bb5fb651223ef2114e4a01681022a3` (unchanged)
- `.git/index` SHA-256: `a47553bdede24bd4e1816e98c9f7e446842e2a1f7a728f6f418472dea6c912ac` (unchanged after baseline capture)
- Index tree (`git write-tree`): `25ff211ce51a3791cb3ef7fa9dc6b6215d77bbb2` (unchanged)
- `git ls-files -s` SHA-256: `660780f23caad69531f45c9812cd0327bf11d2b64b97fef43c0243a6133afe0d` (unchanged)
- `git status --porcelain` SHA-256: `4e5ddeb9b72a74ab5b50484d8c78f06ff61e9e839df920795363a31131779a01` (unchanged)

All publication work happened in the temporary worktree; no add/commit,
index refresh, or file write touched the source workspace.
