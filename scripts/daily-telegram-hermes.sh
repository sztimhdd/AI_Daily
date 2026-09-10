#!/usr/bin/env bash
# AI Daily workday scheduler for Hermes (WSL2 Ubuntu, systemd timer).
#
# Same stage-advancing logic as daily-telegram.sh, adapted for Hermes:
# - PATH includes the user-local bin dirs where `codex` and `npx` live.
# - DISPLAY=:0 is injected so the ChatGPT web image bridge can open a
#   headful Chrome window through WSLg.
#
# Workday rule: only Monday-Friday, 08:00-20:00 local.  One article per day;
# weekends and already-delivered days exit quietly.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$HOME/.bun/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export DISPLAY="${DISPLAY:-:0}"

DATE="$(date +%Y-%m-%d)"
STATE=".local/runs/$DATE/state.md"
DELIVERY=".local/runs/$DATE/delivery-en.json"
LOGDIR=".local/logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/daily-$DATE.log"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

run() {
  if ! PYTHONPATH="$ROOT/src" python3 -m ai_daily.cli "$@" \
      --root . --date "$DATE" >>"$LOG" 2>&1; then
    log "stage '$1' exited non-zero"
  fi
}

# Workday + daytime window only (Mon=1 .. Fri=5).
if [ "$(date +%u)" -ge 6 ]; then
  exit 0
fi
hour="$(date +%H)"
if [ "$hour" -lt 8 ] || [ "$hour" -ge 20 ]; then
  exit 0
fi

# Already delivered today: the article is done.  The completion receipt is
# idempotent, so re-issuing it here is what retries a failed announce.
if [ -f "$DELIVERY" ] && grep -q '"status": "delivered"' "$DELIVERY"; then
  run receipt
  exit 0
fi

# Resume delivery only: do not repeat research/audit for missing assets.
if [ -f "$DELIVERY" ] && grep -q '"status": "partial"' "$DELIVERY"; then
  run run-en --repo-dir ".local/publish/$DATE" \
    --remote-url "https://github.com/sztimhdd/AI_Daily.git" --branch main
  run receipt
  log "resumed partial delivery"
  exit 0
fi

# A failed run needs a human. Poll Telegram once so its one-shot blocked
# receipt is delivered, then stop retrying expensive stages.
if [ -f "$STATE" ] && grep -q '^- status: failed' "$STATE"; then
  run telegram
  log "run blocked (state failed); needs human"
  exit 0
fi

run collect
run telegram
if [ ! -f "$STATE" ] || ! grep -q '^- topic_choice: ' "$STATE"; then
  log "awaiting topic choice"
  exit 0
fi

run research
run narrative --no-prompt
run telegram
if grep -q '^- status: failed' "$STATE"; then
  log "run blocked after narrative; failure receipt sent"
  exit 0
fi
if ! grep -q '^- narrative_choice: ' "$STATE"; then
  log "awaiting narrative choice"
  exit 0
fi

run audit
if grep -q '^- status: failed' "$STATE"; then
  run telegram
  log "audit blocked; failure receipt sent"
  exit 0
fi

run run-en --repo-dir ".local/publish/$DATE" \
  --remote-url "https://github.com/sztimhdd/AI_Daily.git" --branch main
run receipt
log "daily run finished"
