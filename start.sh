#!/usr/bin/env sh
set -eux

PORT="${PORT:-8080}"
APP="backend.app.main:app"

echo "== runtime info =="
date || true; echo "PWD=$(pwd)"; id || true; uname -a || true

echo "== env (top 60) =="; env | sort | sed -n '1,60p' || true

# --- SMOKE MODE: servidor mínimo só pra validar PORT/healthcheck ---
if [ "${SMOKE:-0}" = "1" ]; then
  echo "== SMOKE MODE ON (porta $PORT) =="
  python3 - <<PY
import http.server, socketserver, os, json
PORT = int(os.environ.get("PORT", "8080"))
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/openapi.json", "/api/v1/health"):
            b = json.dumps({"ok": True, "path": self.path}).encode()
            self.send_response(200); self.send_header("content-type","application/json")
            self.send_header("content-length", str(len(b))); self.end_headers(); self.wfile.write(b)
        else:
            super().do_GET()
with socketserver.TCPServer(("", PORT), H) as httpd:
    print("SMOKE server on", PORT, flush=True)
    httpd.serve_forever()
PY
  exit 0
fi
# --- fim SMOKE ---

echo "== preflight imports =="
python3 - <<'PY' || true
import importlib, traceback
mods = ["backend.app.main","backend.app.database","backend.app.models","backend.app.api.v1.routes.auth"]
ok=True
for m in mods:
    try:
        importlib.import_module(m); print("OK:", m)
    except Exception as e:
        print("FAIL:", m, "->", repr(e)); traceback.print_exc(); ok=False
print("preflight_ok=", ok)
PY

# watcher pros logs (ver quando fica pronto)
(
  i=0
  while [ "$i" -lt 300 ]; do
    i=$((i+1)); echo "[watch] try $i -> http://127.0.0.1:${PORT}/openapi.json"
    if curl -fsS "http://127.0.0.1:${PORT}/openapi.json" >/dev/null 2>&1; then
      echo "[watch] OK: openapi respondeu"; break
    fi; sleep 1
  done
) &

echo "== start uvicorn on PORT=${PORT} =="
exec python3 -m uvicorn "${APP}" \
  --host 0.0.0.0 --port "${PORT}" \
  --proxy-headers --forwarded-allow-ips="*" \
  --access-log --log-level info
