#!/usr/bin/env sh
set -eux

echo "== START.SH HIT =="
echo "PWD=$(pwd)"
echo "PORT=${PORT:-unset}"
id || true
uname -a || true
python3 -V || true
ls -la /app || true
echo "----- /app/start.sh (self) -----"
sed -n '1,120p' /app/start.sh || true
echo "-------------------------------"

# Sobe a API (usa PORT do Railway se existir; senão 8080)
exec python3 -m uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8080}" \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --access-log \
  --log-level info
