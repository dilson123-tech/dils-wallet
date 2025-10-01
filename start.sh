#!/usr/bin/env sh
set -eux

echo "PWD=$(pwd)"
id
uname -a
python3 -V || true
ls -la /app

echo "----- /app/start.sh (self) -----"
sed -n '1,200p' /app/start.sh || true
echo "-------------------------------"

# sobe a API (usa PORT do Railway se existir; senão 8080)
exec python3 -m uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8080}" \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --log-level info
