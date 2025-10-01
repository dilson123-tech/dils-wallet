#!/usr/bin/env sh
set -eux

echo "== START.SH =="
echo "PWD=$(pwd)"
echo "PORT=${PORT:-unset}"
python3 -V || true
ls -la /app || true

exec python3 -m uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8080}" \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --access-log \
  --log-level info
