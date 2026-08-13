# Desktop human topic gate UAT (2026-08-12)

External UAT item 5: the mandatory human topic gate executed in a real
desktop chat against the live run `AI-Daily/2026-08-12`, then the run
resumed to `completed` and the article was published to GitHub with
remote reread hash verification.

## Conversation record

- The three candidates for 2026-08-12 (generated from the live pool:
  AIHOT 14 items + RSS 439 items kept, `collect_runs: 1`) were
  presented in the real desktop conversation.
- The user replied: 选择3 (choose candidate 3, no direction given).
- Candidate 3: `Meta 开源 Muse Glimmer 登陆 OpenRouter` — the first
  open-weights model from Meta AI's Superintelligence Labs, listed on
  OpenRouter; the only candidate with multi-source coverage (6
  sources: 1 AIHOT + 5 RSS).

## CLI record (source workspace; every command exited 0)

| Step | Command | Result |
|---|---|---|
| Verify | `PYTHONPATH=src python3 -m ai_daily.cli candidates --date 2026-08-12` | exit 0; index 3 confirmed = Meta Muse Glimmer event |
| Choose | `PYTHONPATH=src python3 -m ai_daily.cli choose-topic --date 2026-08-12 --choice 3` | exit 0; state: `topic_choice: human`, `slug: meta-muse-glimmer-openrouter`, `topic_title` kept verbatim, `direction` empty |
| Research | `cli research --date 2026-08-12` | exit 0, generated |
| Outline | `cli outline --date 2026-08-12` | exit 0, generated |
| Draft | `cli draft --date 2026-08-12` | exit 0, generated (remove-ai-slop contract clean) |
| Cover | `cli cover --date 2026-08-12` (no `--source-dir`) | exit 0, skipped / not generated — no logged-in ChatGPT Web session exists; no ChatGPT export was located, adopted, or fabricated |
| Assemble | `cli assemble --date 2026-08-12` | exit 0, `assembled`, stage `completed` |

## Resume without re-collect

`stage_log` proves resume: after the original collect entries
(18:14–18:17 ADT) the log continues at 21:47:54 with `topic_choice`
(note: human, candidate 3), then research, outline, draft,
optional_cover, assembly, completed (21:48:14). No collect stage
re-entry appears after the choice; `collect_runs` stayed `1`. Final
state fields:

- stage: `completed`
- status: `completed`
- slug: `meta-muse-glimmer-openrouter`
- topic_choice: `human`
- topic_title: `Meta 开源 Muse Glimmer 登陆 OpenRouter`
- last_error: (empty)
- counters: `collect_runs: 1`

## Article and package

- Final article: `articles/2026-08-12-meta-muse-glimmer-openrouter-zh.md`,
  SHA-256 `4034a8e17d11bcbf1fb73c83b7cd9ba511e36c931a53057263462cc5d2613a1f`.
- Package: `outputs/2026/08/12/meta-muse-glimmer-openrouter/` with
  `state.md`, `topic-candidates.md`, `research.md`,
  `article-outline.md`, `article.md`, `metadata.json`, `sources.md`.
  Package `article.md` is byte-identical to the final article by
  design.
- Assembly validation: CLEAN (H1 title, no placeholders/debug
  artifacts); remove-ai-slop (deslop) check: CLEAN; 9 `https://`
  source links preserved into the publishable Markdown and listed in
  `sources.md`.
- Cover: `has_cover: false`, `cover: null` — not generated (no
  logged-in ChatGPT Web session); nonblocking by design. Legacy
  untracked files directly under `outputs/2026/08/12/` root were left
  untouched.

## Publication (isolated worktree, fast-forward only)

- Worktree: temporary branch `codex/desktop-human-gate-20260812`
  rooted exactly at `origin/main`
  `6affcc6c71149011ff63d8909823607f377f7fc1`; only the new article,
  its package, and docs updates were staged. Source workspace HEAD and
  index were never touched.
- Pre-push verification in the worktree: `python3 -m unittest discover
  tests` → `Ran 195 tests ... OK (skipped=4)`; `scripts/uat_cli.sh` →
  17/17 PASS; `compileall`, stdlib-only grep, n8n/automation
  prohibition grep, `git diff --check`, and a secret scan over the new
  files: all clean.
- Content commit: `b0070532c3297780c211c1fc20bf22420be2d505`
  (parent `6affcc6c71149011ff63d8909823607f377f7fc1`), pushed as
  `6affcc6..b007053  HEAD -> main` — fast-forward, never forced.

## Remote reread at the exact commit (gh API)

Method: `gh api repos/sztimhdd/AI_Daily/contents/<path>?ref=b0070532c3297780c211c1fc20bf22420be2d505`
with `Accept: application/vnd.github.raw+json`, saved to scratch
files, SHA-256 compared against the committed worktree copies.
Browse form: `https://github.com/sztimhdd/AI_Daily/blob/b0070532c3297780c211c1fc20bf22420be2d505/<path>`

| Path | SHA-256 (local == remote) | Result |
|---|---|---|
| `articles/2026-08-12-meta-muse-glimmer-openrouter-zh.md` | `4034a8e17d11bcbf1fb73c83b7cd9ba511e36c931a53057263462cc5d2613a1f` | EQUAL |
| `outputs/2026/08/12/meta-muse-glimmer-openrouter/article.md` | `4034a8e17d11bcbf1fb73c83b7cd9ba511e36c931a53057263462cc5d2613a1f` | EQUAL |
| `outputs/2026/08/12/meta-muse-glimmer-openrouter/state.md` | `0f4ad1c9793e58f15a8e09636108b0d2c2a3ce5bbf22d6730d605f01b0af312e` | EQUAL |
| `outputs/2026/08/12/meta-muse-glimmer-openrouter/research.md` | `6b91e79c5b770b445910da25d11f5bd77624720776e3e278803a5138df659a20` | EQUAL |
| `outputs/2026/08/12/meta-muse-glimmer-openrouter/article-outline.md` | `29afcf98dba14df3337fe76832a05a305c34cfe69d937951c61efa563665aefb` | EQUAL |
| `outputs/2026/08/12/meta-muse-glimmer-openrouter/metadata.json` | `c4b882f8b77d316a83ac2e7845af1a61a8c2bac74b5b46c7d94feb01ed6da0b7` | EQUAL |
| `outputs/2026/08/12/meta-muse-glimmer-openrouter/sources.md` | `7db21d1df259a63c8bc537269b516d1ba22103fde2849a4cd0e864c29c837303` | EQUAL |
| `outputs/2026/08/12/meta-muse-glimmer-openrouter/topic-candidates.md` | `3fff0edc026ff7e40e2f38828cd012e426c2be4f049c9394e2bcdb53faa76d70` | EQUAL |

Result: `READBACK_ALL_EQUAL` — 8/8 files byte-identical local vs
remote at the exact content commit.

This record itself is published in the follow-up docs commit on top of
`b007053`; that commit's SHA is reported in the delivery message and
its files are reread-verified at their own SHA.
