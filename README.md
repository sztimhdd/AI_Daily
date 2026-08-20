# AI Daily

AI Daily is a Codex-operated pipeline for producing daily, deeply researched
Chinese AI articles with publication-ready illustrations. V1 is implemented
in Python (standard library only) under `src/ai_daily/`.

## Pipeline

```
collect → topic_choice (human gate) → research → outline → draft
        → optional_cover → assembly → publish
```

The topic gate is mandatory but can be satisfied three ways: a human
choice (`--choice N`), a deterministic fixture bypass (`--fixture`), or
an unattended simulated choice (`--simulate`, records
`topic_choice: simulated`).

One run per date (`AI-Daily/YYYY-MM-DD`). Working state lives in
`.local/runs/<date>/state.md`; the durable package lands in
`outputs/YYYY/MM/DD/<article-slug>/` and the publishable article at
`articles/YYYY-MM-DD-<article-slug>-zh.md`.

Failure semantics: AIHOT collection failure stops candidate generation
(state `failed`, resumable); RSS feed failures are nonblocking and
recorded in `rss-stats.json` (machine-readable `failures` array, counts
agreeing with `feeds_failed`) plus the `rss-pool.md` failure section;
cover problems never block assembly; publish falls
back to an explicit `local-only` mode when no remote is reachable —
never a fake success.

## Repository map

- `src/ai_daily/` — V1 pipeline modules and CLI (see `src/README.md`).
- `tests/` — unittest suite mirroring `src/` (see `tests/README.md`).
- `knowledge/` — guidance compiled from the immutable core-IP JSONs
  (author style, remove-ai-slop contract, research contract, RSS catalog).
- `scripts/` — `uat_cli.sh`, the deterministic fixture UAT entrypoint.
- `workflows/reference/` — the authoritative legacy n8n workflow (read-only evidence).
- `[Atomic] Researcher_Skill.json`, `[Atomic] Topic_Survey_Skill.json`,
  `[Atomic] Universal Draft Writing.json`, `Long-Content-Writing.json`
  — the four immutable core-IP JSONs at the repo root (read-only).
- `outputs/` — approved article packages by date and slug.
- `articles/` — final publishable articles.
- `docs/` — specs, plans, verification scaffold, migration notes.
- `archive/` — read-only historical content.
- `.local/` — ignored runtime state, logs, caches, candidate media.

## Install

Requires Python 3.11+ (developed on 3.14). There are no third-party
runtime or test dependencies; nothing to install beyond a Python
interpreter and (for the publish stage) git. `jq` is used only for
baseline structural checks.

```bash
python3 --version   # 3.11+
```

## Run

All commands run from the repository root with `PYTHONPATH=src`.
The daily chain (fixture mode shown; `--mode live` uses real sources):

```bash
export PYTHONPATH=src
DATE=2026-08-13

python3 -m ai_daily.cli init --date $DATE
python3 -m ai_daily.cli collect --date $DATE --mode fixture \
  --aihot-fixture tests/fixtures/aihot_items.json
python3 -m ai_daily.cli candidates --date $DATE
python3 -m ai_daily.cli choose-topic --date $DATE \
  --fixture tests/fixtures/topic_fixture.json     # or: --choice 2 --direction "..."
python3 -m ai_daily.cli research --date $DATE
python3 -m ai_daily.cli outline --date $DATE
python3 -m ai_daily.cli draft --date $DATE
python3 -m ai_daily.cli cover --date $DATE [--source-dir <ChatGPT export dir>]
python3 -m ai_daily.cli assemble --date $DATE
python3 -m ai_daily.cli publish --date $DATE --repo-dir <publish-repo> \
  [--remote-url <origin-url>]
python3 -m ai_daily.cli status --date $DATE
```

Unattended fixture end-to-end (one command, publishes local-only):

```bash
python3 -m ai_daily.cli run --date $DATE \
  --topic-fixture tests/fixtures/topic_fixture.json \
  --aihot-fixture tests/fixtures/aihot_items.json
```

Unattended mode (no human wait): the topic gate accepts a simulated
choice. The ranked candidate is kept verbatim (title/slug/thesis), the
direction defaults to empty, and state records `topic_choice: simulated`
plus the stage_log note `topic choice: simulated (unattended mode,
candidate N)`. Resume never re-collects.

```bash
python3 -m ai_daily.cli choose-topic --date $DATE --simulate --choice 1
python3 -m ai_daily.cli choose-topic --date $DATE --simulate  # auto-selects candidate 1
```

Live unattended daily chain (AIHOT + RSS catalog with bounded
timeouts; RSS failures recorded nonblocking in `rss-stats.json`):

```bash
python3 -m ai_daily.cli init --date $DATE
python3 -m ai_daily.cli collect --date $DATE --mode live
python3 -m ai_daily.cli candidates --date $DATE
python3 -m ai_daily.cli choose-topic --date $DATE --simulate --choice 1
python3 -m ai_daily.cli research --date $DATE
python3 -m ai_daily.cli outline --date $DATE
python3 -m ai_daily.cli draft --date $DATE
python3 -m ai_daily.cli cover --date $DATE          # optional, skipped cleanly when absent
python3 -m ai_daily.cli assemble --date $DATE
```

After a human edits `.local/runs/<date>/article-outline.md`, rebuild
the draft without re-collecting:

```bash
python3 -m ai_daily.cli regenerate-outline --date $DATE
```

### Launch a visible Terminal window (TUI session)

The whole app interface is a visible macOS Terminal.app window: the
launcher opens a foreground window and runs the interactive `session`
there (pure macOS-native `osascript`, no third-party dependencies).
`session` walks collect → topic choice → research with full TUI output
(AIHOT hot topics, candidates, story matrix, fetch status, OSINT archive)
and stops at stage 03:

```bash
./scripts/open_ai_daily_terminal.sh --root /Users/hai/Projects/Desktop/AI_study/AI_Daily --date 2026-08-17
```

The window runs
`cd <root> && export PYTHONPATH=src && python3 -m ai_daily.cli session --root <root> --date <date>`
and keeps the shell prompt after the command finishes, so you can keep
running the same CLI manually to resume the chain. Allowed commands
(whitelist: `session`, `choose-topic`, `status`);
`--dry-run` prints the command without opening a window.

Exit codes: `0` success, `1` controlled domain error (message on stderr),
`2` usage error.

### Low-level fetch primitive

Any stage can fetch one URL through the unified three-lane primitive
(auto-routed HTTP/CDP) without run state:

```bash
python3 -m ai_daily.cli fetch --root <root> --date $DATE <url>
```

## Test

```bash
python3 -m unittest discover tests          # full suite (371 tests)
python3 -m unittest tests.test_pipeline_e2e # black-box E2E subset
scripts/uat_cli.sh                          # deterministic fixture UAT (17 checks)
```

Tests never touch the network or real credentials; live paths are
exercised with injected fetchers/transports.

## Lint

No external linter is configured yet. The working lint is byte
compilation plus the static prohibition greps (must print nothing):

```bash
python3 -m compileall -q src tests
grep -rnE --exclude-dir=__pycache__ 'import (requests|httpx|feedparser|yaml|bs4|lxml|sqlite3)|from (requests|httpx|feedparser|yaml|bs4|lxml)' src/ || true
grep -rniE --exclude-dir=__pycache__ --exclude=assemble.py 'n8n|automation|event.sourcing|wechat publish|email send' src/ai_daily/ || true
```

Exclusions, so the prohibition check has no false positives:

- `__pycache__` bytecode re-embeds source strings and matches as binary.
- `assemble.py` is the sanitizer: its placeholder regexes and docstring
  must literally name the n8n artifacts they strip. Forbidden adapter
  code added anywhere else in `src/ai_daily/` is still flagged.

## Baseline checks

```bash
jq empty "workflows/reference/公众号选题写稿配图一体化工作流.json"
jq empty "[Atomic] Researcher_Skill.json"
jq empty "[Atomic] Topic_Survey_Skill.json"
jq empty "[Atomic] Universal Draft Writing.json"
jq empty "Long-Content-Writing.json"
git diff --check
```

## Output package

Each article belongs in `outputs/YYYY/MM/DD/<article-slug>/` containing
`<article-slug>.md` (the article, named by its title slug), `metadata.json`,
`sources.md`, and (optionally) `images/cover.<png|jpg|webp>`. The Chinese
and English editions each get their own slug-named package directory.
Only final or intentionally versioned
deliverables belong in Git; raw responses, caches, and working state
stay in `.local/`.

## Security

Never commit tokens, credentials, private payloads, or unredacted model
traces. Publish credentials are never automated: `publish` uses whatever
git/`gh` authentication the operator already has, and records
`local-only` when none is available. Treat values found in Git history
as exposed and rotate them.
