#!/usr/bin/env sh
set -eu

export PYTHONUNBUFFERED=1

PORT="${PORT:-8080}"
APP="backend.app.main:app"

echo "== preflight (non-fatal) importing modules =="
python3 - <<'PY' || true
import importlib
mods = [
    "backend.app.main",
    "backend.app.api.v1.routes.auth",
    "backend.app.api.v1.routes.users",
    "backend.app.api.v1.routes.transactions",
]
for m in mods:
    try:
        importlib.import_module(m)
        print("IMPORTED:", m)
    except Exception as e:
        print("IMPORT_FAIL:", m, "->", repr(e))
PY

echo "== starting uvicorn on :${PORT} =="
exec python3 -m uvicorn "$APP" \
  --host 0.0.0.0 \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --log-level info
