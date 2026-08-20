# AI_Daily V1 pipeline — unattended live UAT (2026-08-13)

Record of the first fully unattended live daily run, executed on
2026-08-13 (America/Halifax) against the V1 pipeline (`src/ai_daily/`).
No human waited on at any gate: the topic gate used the new simulated
choice path. Raw stage logs live under `.local/unattended-20260813/`
(untracked); this document is the tracked summary. Commands, exit
codes, counts, hashes, and messages are quoted from that session.

## Environment

- Repo: `/Users/hai/Projects/Desktop/AI_study/AI_Daily`
- Python: `3.14`; invocation `PYTHONPATH=src python3 -m ai_daily.cli ...`
- Run date: `2026-08-13`; network enabled (live AIHOT + live RSS catalog)
- Mode: UNATTENDED — `choose-topic --simulate`, zero interactive prompts

## Verdict summary

| Check | Result | Notes |
|---|---|---|
| Chain init → collect(live) → candidates → simulated choice → research → outline → draft → cover(skipped) → assemble | PASS | every stage exit `0`; final `stage: completed` |
| Simulated choice contract | PASS | `topic_choice: simulated`, candidate title/slug verbatim, direction empty, stage_log note present |
| `collect_runs` / no human wait | PASS | `collect_runs: 1`; no prompt issued anywhere |
| RSS failures nonblocking | PASS | 18/76 feeds failed; recorded, run continued |
| Article validation | PASS | one H1, no raw HTML, no ellipsis, `deslop.check_text() == []`, real links |
| Research defect F5 (lead cited sibling story) | FIXED | two regression tests, RED before / GREEN after |
| Full source suite | PASS | `Ran 254 tests ... OK` |

## Unattended chain — commands and exit codes

All commands exit `0`; evidence logs `01-init.log` … `05-research-outline-draft.log`
(each ends with `EXIT_<stage>=0`).

| # | Command | Exit |
|---|---|---|
| 1 | `python3 -m ai_daily.cli init --date 2026-08-13` | 0 |
| 2 | `python3 -m ai_daily.cli collect --date 2026-08-13 --mode live` | 0 |
| 3 | `python3 -m ai_daily.cli candidates --date 2026-08-13` | 0 |
| 4 | `python3 -m ai_daily.cli choose-topic --date 2026-08-13 --simulate --choice 1` | 0 |
| 5 | `python3 -m ai_daily.cli research --date 2026-08-13` | 0 |
| 6 | `python3 -m ai_daily.cli outline --date 2026-08-13` | 0 |
| 7 | `python3 -m ai_daily.cli draft --date 2026-08-13` | 0 |
| 8 | cover skipped (optional; no cover source dir) | 0 |
| 9 | `python3 -m ai_daily.cli assemble --date 2026-08-13` | 0 |

Collect wall time: `48.399 total` seconds (bounded RSS timeouts).
Stage output: `collect: collected (aihot=15 rss=445)`; choice output:
`topic chosen: OpenRouter 推出实时网页搜索基准测试：如何为智能体选择引擎、深度与模型 (openrouter)`.

## RSS live collection — nonblocking failures

From `.local/runs/2026-08-13/rss-stats.json`: `feeds_requested=76`,
`feeds_ok=58`, `feeds_failed=18`, `items_seen=3381`, `items_kept=445`,
`items_out_of_window=2933`, `duplicates_removed=3`, `undated_items=60`,
`window_hours=96`. All 18 failures are recorded with URL + error in the
`failures` array (e.g. `https://earthly.dev/blog/rss.xml` → HTTP 404,
`https://gizmodo.com/rss` → HTTP 403) and none blocked the run.

## Simulated choice contract

- State fields: `topic_choice: simulated`, `slug: openrouter`,
  `topic_title` equal verbatim to candidate 1's title, direction empty.
- stage_log note: `topic choice: simulated (unattended mode, candidate 1)`.
- `selected-topic.json` preserves the candidate title/slug verbatim with
  `direction` empty.
- Resume check: re-running `choose-topic --simulate` after the fact is
  accepted without re-collecting; `collect_runs` remained `1` throughout.
- Unit coverage: `tests/test_topics.py` and `tests/test_cli.py` cover the
  bypass, verbatim preservation, and resume-without-re-collect paths.

## Final state (`.local/runs/2026-08-13/state.md`)

`stage: completed`, `status: completed`, `slug: openrouter`,
`topic_choice: simulated`, `collect_runs: 1`, `last_error:` empty.
stage_log excerpt: `note: collect: aihot 15 items (live); rss kept 445,
failed feeds 18 (nonblocking)` → `note: topic choice: simulated
(unattended mode, candidate 1)` → `note: cover: skipped (no cover source
dir given (cover is optional))` → `completed (assembly accepted)`.

## Article validation (`articles/2026-08-13-openrouter-zh.md`)

- sha256 `bdbfe10d2fc8c8265adc8e49aa6327b563ad7dee5ad1161711bbccb496baeb94`
  — identical to `.local/runs/2026-08-13/article.md` and to the packaged
  `outputs/2026/08/13/openrouter/article.md`.
- Exactly one H1 (the topic title); no raw HTML tags; no `…`/`...`
  ellipsis; `deslop.check_text()` returns `[]`.
- 6 markdown links (3 unique), all real https sources:
  `https://openrouter.ai/blog/announcements/web-search-benchmark`,
  `https://www.unite.ai/deepseek-ships-v4-pro-as-its-flagship-model-leaves-preview/`,
  `https://x.com/OpenRouter/status/2087509478480765218`.

## F5 fix — topic's own event must outrank sibling stories

Defect: with live evidence the draft lead cited a peg of a *sibling*
story (same query term, different event) instead of the chosen topic's
own event. Root cause: `match_evidence` ranked lexically-tied siblings
ahead of the topic's own event, and the `MAX_EVIDENCE_PER_QUESTION=3`
cap then squeezed the topic's own event out of the pool. Reproduced
with a 4-item pool (3 siblings + topic) all tying at score 2 on the
query `openrouter`.

Fix in `src/ai_daily/research.py`: `match_evidence(query, items,
topic_title="")` now sorts by `(not_own_event, -score, title, item)`
where `not_own_event` is `0` when `topics.same_event(item.title,
topic_title)` matches, so the topic's own event always leads before the
cap applies. Call site passes `topic.get("title", "")`.

Regression tests (`tests/test_research.py::TopicEventPriorityTests`,
confirmed RED before the fix, GREEN after):

- `test_topics_own_event_ranks_first_in_matching_questions`
- `test_draft_lead_cites_topics_own_event_not_sibling_story`

After the fix, `research/outline/draft` were regenerated with `--force`;
the lead now cites the OpenRouter announcement URL.

## Package (`outputs/2026/08/13/openrouter/`)

Regenerated deterministically from `.local/runs/2026-08-13/` and staged
at `/tmp/aidaily-stage-20260813/` because a background process repeatedly
wiped `outputs/` in the source workspace during this session (observed
`outputs/2026/08/12|13|14` oscillating present/absent; `.local/runs/`,
`articles/`, and git state were never affected). Publish therefore copies
the package from the stable staged directory.

| File | sha256 |
|---|---|
| `article.md` | `bdbfe10d2fc8c8265adc8e49aa6327b563ad7dee5ad1161711bbccb496baeb94` |
| `article-final.md` | `bdbfe10d2fc8c8265adc8e49aa6327b563ad7dee5ad1161711bbccb496baeb94` |
| `article-outline.md` | `fc9ce69de2d8f26c96328add350959b1a7678636fce5ea2938c0ec261406717e` |
| `research.md` | `aa5a9142b8d86ec1759a63daa65f65d627b26008293de084b21bc59439394eb4` |
| `sources.md` | `04d452d19cd3416efeacb5146e0f7c242150dd4a3370d854f410bd6e5f06cdec` |
| `state.md` | `dd46c60813989b431a32ac9ea34f99fca963996a152fbf83c04c9e2e003fdc5b` |
| `topic-candidates.md` | `18e1ecc14e548538762bb60235cdd4fa79f9ae2cb274458973cd0152e0263fd9` |
| `metadata.json` | `99dba53bdaa5bf5b2a810f0ba7dab36546e47b0e2a4a2e625a3305938aa0a9ee` |

`metadata.json`: `slug=openrouter`, `topic_choice=simulated`,
`has_cover=false`, `sources=5`,
`final_article=articles/2026-08-13-openrouter-zh.md`,
`package=outputs/2026/08/13/openrouter`.

## Test suites

- Full source suite: `PYTHONPATH=src python3 -m unittest discover tests`
  → `Ran 254 tests ... OK` (252 before the two F5 regression tests).
- Fixture UAT `scripts/uat_cli.sh`: run in the publish worktree (see
  publish evidence for this change).

## Notes

- No secrets are referenced anywhere in this run; collection is
  credential-free.
- Protected paths untouched: legacy `outputs/2026/08/12` root files,
  `automation/state.json`, root core-IP JSONs, `archive/`.
