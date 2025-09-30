#!/usr/bin/env sh
set -ex

echo "== preflight: importing modules =="
python3 - <<'PY'
import importlib, traceback
mods = [
    # núcleo
    "backend.app.database",
    "backend.app.models",
    "backend.app.models.user",
    "backend.app.models.transaction",
    "backend.app.schemas",

    # rotas + helpers
    "backend.app.api.v1.routes.security",
    "backend.app.api.v1.routes.auth",
    "backend.app.api.v1.routes.users",
    "backend.app.api.v1.routes.transactions",
    "backend.app.api.v1.routes.refresh",
]
ok = True
for m in mods:
    try:
        importlib.import_module(m)
        print("IMPORTED:", m)
    except Exception as e:
        print("IMPORT_FAIL:", m, "->", repr(e))
        traceback.print_exc()
        ok = False
if not ok:
    raise SystemExit(1)
PY

# sobe o servidor com log verboso
exec python3 -m uvicorn backend.app.main:app \
  --host 0.0.0.0 --port 8080 \
  --proxy-headers --forwarded-allow-ips="*" \
  --log-level debug
