#!/usr/bin/env sh
set -Eeuo pipefail

PORT="${PORT:-8080}"
APP="backend.app.main:app"

echo "== SAFE MODE: SMOKE -> troca para Uvicorn =="

# 1) Sobe um servidor SMOKE que responde /api/v1/health e /openapi.json no PORT
python3 - <<'PY' &
import os, http.server, socketserver
PORT=int(os.environ.get("PORT","8080"))

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health", "/api/v1/health"):
            self.send_response(200)
            self.send_header("content-type","application/json")
            self.end_headers()
            self.wfile.write(b'{}')
        elif self.path == "/openapi.json":
            self.send_response(200)
            self.send_header("content-type","application/json")
            self.end_headers()
            self.wfile.write(b'{"openapi":"3.1.0","info":{"title":"booting"}}')
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *a, **k): pass

with socketserver.TCPServer(("0.0.0.0", PORT), H) as httpd:
    httpd.serve_forever()
PY
SMOKE_PID=$!
trap 'kill -TERM $SMOKE_PID 2>/dev/null || true' EXIT
echo "SMOKE_PID=$SMOKE_PID"

# 2) Preflight rápido: garante que os módulos críticos importam
python3 - <<'PY'
import importlib
mods = [
    "backend.app.database",
    "backend.app.models",
    "backend.app.schemas",
    "backend.app.api.v1.routes.auth",
]
ok=True
for m in mods:
    try:
        importlib.import_module(m)
        print("IMPORT_OK", m)
    except Exception as e:
        print("IMPORT_FAIL", m, "->", repr(e)); ok=False
if not ok:
    raise SystemExit(1)
PY

# 3) Troca: derruba o SMOKE e sobe o Uvicorn na MESMA porta
kill -TERM "$SMOKE_PID" || true
wait "$SMOKE_PID" 2>/dev/null || true

exec python3 -m uvicorn "$APP" \
  --host 0.0.0.0 \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --log-level info
