#!/usr/bin/env bash
set -euo pipefail

URL="${1:?usage: wait_http.sh <url> [timeout_seconds]}"
TIMEOUT="${2:-15}"

start="$(date +%s)"
while true; do
  if curl -sS -f --max-time 2 "$URL" >/dev/null 2>&1; then
    echo "✅ READY: $URL"
    exit 0
  fi
  now="$(date +%s)"
  if (( now - start >= TIMEOUT )); then
    echo "❌ TIMEOUT waiting for: $URL (timeout=${TIMEOUT}s)" >&2
    exit 1
  fi
  sleep 0.4
done
