#!/usr/bin/env bash
set -euo pipefail
BASE="http://127.0.0.1:5178"

pkill -f "vite" || true
nohup npm run dev -- --host 127.0.0.1 --port 5178 --strictPort > .vite.dev.log 2>&1 & echo $! > .vite.pid

for i in {1..40}; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/")
  [ "$code" = "200" ] && echo "OK dev na 5178 (PID $(cat .vite.pid))" && break
  sleep 0.5
done

bash scripts/health_spa.sh "$BASE"
echo "✅ Pronto em $BASE"
