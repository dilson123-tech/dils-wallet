#!/usr/bin/env sh
set -euo pipefail

export PYTHONUNBUFFERED=1
export PORT="${PORT:-8080}"
export APP="backend.app.main:app"
# ajuda as imports (não faz mal se já estiver correto)
export PYTHONPATH="/app/backend:${PYTHONPATH:-}"

echo "===== BOOT DIAG ====="
echo "PWD=$PWD"; id; uname -a; python3 -V
echo "-- ls -la /app"
ls -la /app || true
echo "-- ls -la /app/backend"
ls -la /app/backend || true
python3 - <<'PY'
import sys, os
print("sys.path =", sys.path)
print("cwd      =", os.getcwd())
PY
echo "====================="

echo "== SMOKE: ligando servidor de saúde em :$PORT =="
python3 - <<'PY' &
import os, http.server, socketserver, json
PORT=int(os.environ.get("PORT","8080"))
class H(http.server.BaseHTTPRequestHandler):
    def _ok(self, body=b"{}"):
        self.send_response(200)
        self.send_header("content-type","application/json")
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if self.path in ("/", "/health", "/api/v1/health"):
            self._ok(b"{}")
        elif self.path == "/openapi.json":
            self._ok(json.dumps({"openapi":"3.1.0","info":{"title":"booting"}}).encode())
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *a, **k): pass
with socketserver.TCPServer(("0.0.0.0", PORT), H) as httpd:
    httpd.serve_forever()
PY
SMOKE_PID=$!
echo "SMOKE_PID=$SMOKE_PID"

echo "== Preflight: importando módulos-base =="
PRE_OK=1
python3 - <<'PY' || PRE_OK=0
import importlib, traceback
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
        print("IMPORT_FAIL", m, "->", repr(e))
        traceback.print_exc()
        ok=False
if not ok:
    raise SystemExit(1)
PY

if [ "$PRE_OK" -ne 1 ]; then
  echo "!! Preflight FALHOU. Mantendo SMOKE em pé para passar healthcheck e facilitar diagnóstico."
  echo "   Veja os logs acima (IMPORT_FAIL)."
  wait "$SMOKE_PID"   # nunca sai; mantém o container vivo
  exit 0
fi

echo "== Preflight OK: trocando SMOKE -> Uvicorn =="
kill -TERM "$SMOKE_PID" 2>/dev/null || true
wait "$SMOKE_PID" 2>/dev/null || true

exec python3 -m uvicorn "$APP" \
  --host 0.0.0.0 \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --log-level info
