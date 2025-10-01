#!/usr/bin/env sh
set -euo pipefail

PORT="${PORT:-8080}"
APP="backend.app.main:app"

echo "Starting Uvicorn on port $PORT"
exec python3 -m uvicorn "$APP" \
  --host 0.0.0.0 \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips="*"
