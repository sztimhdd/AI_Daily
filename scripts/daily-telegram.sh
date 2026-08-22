#!/usr/bin/env bash
# AI Daily workday scheduler driver.
#
# Runs every 30 minutes via launchd (see com.aidaily.daily.plist).  It
# advances the Telegram-driven pipeline one stage at a time and stops at
# human decision points: each stage is idempotent/resumable and all business
# state lives in .local/runs/<date>/state.md (the single source of truth).
#
# Workday rule: only Monday-Friday, 08:00-20:00 local.  One article per day;
# weekends and already-delivered days exit quietly.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

DATE="$(date +%Y-%m-%d)"
STATE=".local/runs/$DATE/state.md"
DELIVERY=".local/runs/$DATE/delivery-en.json"
LOGDIR=".local/logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/daily-$DATE.log"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

# Workday + daytime window only (Mon=1 .. Fri=5).
if [ "$(date +%u)" -ge 6 ]; then
  exit 0
fi
hour="$(date +%H)"
if [ "$hour" -lt 8 ] || [ "$hour" -ge 20 ]; then
  exit 0
fi

# Already delivered today: nothing to do.
if [ -f "$DELIVERY" ] && grep -q '"status": "delivered"' "$DELIVERY"; then
  exit 0
fi

# A failed run (e.g. an unsupported audit) needs a human; stop retrying.
if [ -f "$STATE" ] && grep -q '^- status: failed' "$STATE"; then
  log "run blocked (state failed); needs human"
  exit 0
fi

run() {
  if ! PYTHONPATH="$ROOT/src" python3 -m ai_daily.cli "$@" \
      --root . --date "$DATE" >>"$LOG" 2>&1; then
    log "stage '$1' exited non-zero"
  fi
}

run collect
run telegram
if [ ! -f "$STATE" ] || ! grep -q '^- topic_choice: ' "$STATE"; then
  log "awaiting topic choice"
  exit 0
fi

run research
run narrative
run telegram
if ! grep -q '^- narrative_choice: ' "$STATE"; then
  log "awaiting narrative choice"
  exit 0
fi

run audit
if grep -q '^- status: failed' "$STATE"; then
  log "audit blocked; needs human"
  exit 0
fi

run run-en --repo-dir ".local/publish/$DATE" \
  --remote-url "https://github.com/sztimhdd/AI_Daily.git" --branch main
log "daily run finished"
