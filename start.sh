#!/usr/bin/env sh
set -euxo pipefail

echo "=== env/diag ==="
echo "PWD=$(pwd)"
id
uname -a
python3 -V
echo "PORT=${PORT:-unset}"

echo "=== pip list (topo) ==="
pip list | head -n 50 || true

echo "=== ls /app ==="
ls -la /app || true
echo "=== ls /app/backend ==="
ls -la /app/backend || true

echo "=== import preflight ==="
python3 - <<'PY'
import importlib, traceback
mods = [
    "backend.app.main",
    "backend.app.database",
    "backend.app.models",
    "backend.app.api.v1.routes.auth",
]
ok = True
for m in mods:
    try:
        importlib.import_module(m)
        print("IMPORT_OK", m)
    except Exception as e:
        print("IMPORT_FAIL", m, "->", repr(e))
        traceback.print_exc()
        ok = False
if not ok:
    raise SystemExit(1)
PY

echo "=== starting uvicorn ==="
# --lifespan off evita travar se existir evento de startup que dependa de DB
exec python3 -m uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8080}" \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --log-level debug \
  --lifespan off
