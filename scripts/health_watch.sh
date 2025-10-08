#!/usr/bin/env bash
set -euo pipefail

# Carrega .env*
for f in .env .env.local .env.prod .env.production; do
  [ -f "$f" ] && { set -a; . "$f" || true; set +a; }
done

: "${HEALTH_URL:?HEALTH_URL não definido}"
: "${TG_BOT_TOKEN:?TG_BOT_TOKEN não definido}"
: "${TG_CHAT_ID:?TG_CHAT_ID não definido}"

STATE_FILE=".health_state"

ts_utc() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }

notify() {
  local text="$1"
  curl -s -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TG_CHAT_ID}" \
    --data-urlencode "text=${text}" >/dev/null || true
}

check_once() {
  code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")
  if [ "$code" = "200" ]; then echo "ok"; else echo "down"; fi
}

last_state="$(cat "$STATE_FILE" 2>/dev/null || echo "unknown")"

while true; do
  status="$(check_once)"
  if [ "$status" != "$last_state" ]; then
    if [ "$status" = "down" ]; then
      notify "⚠️ Dils Wallet OFFLINE\nURL: $HEALTH_URL\nTime: $(ts_utc)"
    elif [ "$status" = "ok" ] && [ "$last_state" = "down" ]; then
      notify "✅ Dils Wallet ONLINE novamente\nURL: $HEALTH_URL\nTime: $(ts_utc)"
    fi
    echo "$status" > "$STATE_FILE"
    last_state="$status"
  fi
  sleep 60
done
