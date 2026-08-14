#!/usr/bin/env bash
# Deterministic fixture UAT for the AI_Daily V1 CLI.
#
# Runs the full daily editorial chain end-to-end against bundled
# fixtures (no network, no credentials, no git remotes):
#   init -> collect(fixture) -> candidates -> choose-topic(fixture)
#        -> research -> outline -> draft -> cover(skipped)
#        -> assemble -> publish(local-only) -> status
# plus an outline-edit regeneration check.
#
# Usage:
#   scripts/uat_cli.sh            # prints PASS/FAIL summary, exit 0/1
#   scripts/uat_cli.sh out.md     # also saves the summary to out.md
#
# Exit codes: 0 = all UAT checks passed, 1 = a check or command failed.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DATE="${UAT_DATE:-2026-08-12}"
SLUG="ai-search-budget-research-cost"
AIHOT_FIXTURE="tests/fixtures/aihot_items.json"
TOPIC_FIXTURE="tests/fixtures/topic_fixture.json"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

LOG=""
pass=0
fail=0

say() { LOG+="$1"$'\n'; echo "$1"; }

cli() {
  # Run one CLI command against the UAT sandbox; abort UAT on failure.
  say "\$ ai_daily $* --root <sandbox> --date $DATE"
  local rc=0 out=""
  out="$(PYTHONPATH=src python3 -m ai_daily.cli "$@" --root "$WORK" --date "$DATE" 2>&1)" || rc=$?
  while IFS= read -r line; do
    LOG+="    $line"$'\n'
    echo "    $line"
  done <<< "$out"
  if [ "$rc" -ne 0 ]; then
    say "ABORT: ai_daily $* exited with code $rc"
    say ""
    say "RESULT: FAIL (command error)"
    [ -n "${1_OUT:-}" ] || true
    if [ -n "${SUMMARY_OUT:-}" ]; then printf '%s\n' "$LOG" > "$SUMMARY_OUT"; fi
    exit 1
  fi
}

check() {
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    say "PASS: $desc"
    pass=$((pass + 1))
  else
    say "FAIL: $desc"
    fail=$((fail + 1))
  fi
}

SUMMARY_OUT="${1:-}"

say "# AI_Daily fixture UAT — $DATE"
say ""
say "repo: $REPO_ROOT"
say "python: $(python3 --version 2>&1)"
say "sandbox: $WORK (temp, removed on exit)"
say ""

cli init
cli collect --mode fixture --aihot-fixture "$AIHOT_FIXTURE"
cli candidates
cli choose-topic --fixture "$TOPIC_FIXTURE"
cli research
cli outline
cli draft
cli cover
cli assemble
cli publish --repo-dir "$WORK/.local/publish/$DATE"
cli status

say ""
say "## checks"

STATE="$WORK/.local/runs/$DATE/state.md"
PKG="$WORK/outputs/2026/08/12/$SLUG"
FINAL="$WORK/articles/$DATE-$SLUG-zh.md"

check "state.md exists" test -f "$STATE"
check "stage completed" grep -q -- "- stage: completed" "$STATE"
check "publish recorded local-only" grep -q "publish-mode: local-only" "$STATE"
check "collect_runs incremented exactly once" grep -q "collect_runs: 1" "$STATE"
check "no pending error" grep -q -- "- last_error:$" "$STATE"
check "package article.md" test -f "$PKG/article.md"
check "package metadata.json" test -f "$PKG/metadata.json"
check "package sources.md" test -f "$PKG/sources.md"
check "final article at articles/<date>-<slug>-zh.md" test -f "$FINAL"
check "final article identical to package copy" cmp -s "$PKG/article.md" "$FINAL"
check "draft has H1" grep -q "^# " "$PKG/article.md"
check "draft carries source links" grep -q "https://" "$PKG/article.md"
check "no unresolved image placeholders" bash -c "! grep -q '{\[IMG' '$PKG/article.md'"
check "no n8n leftovers" bash -c "! grep -qi 'n8n' '$PKG/article.md'"

# Outline-edit regeneration: edited outline changes draft without re-collect.
OUTLINE="$WORK/.local/runs/$DATE/article-outline.md"
DRAFT="$WORK/.local/runs/$DATE/article.md"
cp "$DRAFT" "$WORK/draft-before.md"
python3 - "$OUTLINE" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
text = p.read_text(encoding="utf-8")
marker = "- 风险冷评：给读者的具体警告"
assert marker in text, "outline section marker missing"
p.write_text(text.replace(marker, "- UAT 附加章节：验收自检\n" + marker), encoding="utf-8")
PY
cli regenerate-outline
check "outline edit changed the draft" bash -c "! cmp -s '$DRAFT' '$WORK/draft-before.md'"
check "new section heading present in draft" grep -q "UAT 附加章节：验收自检" "$DRAFT"
check "collect_runs unchanged after outline edit" grep -q "collect_runs: 1" "$STATE"

say ""
say "## summary"
say "passed: $pass"
say "failed: $fail"
if [ "$fail" -eq 0 ]; then
  say "RESULT: PASS"
else
  say "RESULT: FAIL"
fi

if [ -n "$SUMMARY_OUT" ]; then
  printf '%s\n' "$LOG" > "$SUMMARY_OUT"
  echo "summary saved to: $SUMMARY_OUT"
fi

[ "$fail" -eq 0 ]
