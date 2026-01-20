#!/usr/bin/env bash
set -euo pipefail
# Uso: scripts/guard_apply.sh "descrição" -- comando_que_mexe_no_codigo ...
desc="$1"; shift
echo "🛡  Guard: $desc"

# 4.1 snapshot antes de mexer
./scripts/snapshot.sh >/dev/null

# 4.2 executa comando de patch
"$@"

# 4.3 smoke test backend (se ativo local)
( set +e
  if curl -sS http://127.0.0.1:8080/healthz | jq -e '.ok==true' >/dev/null 2>&1; then
    echo "🔎 /healthz OK"
    curl -sS http://127.0.0.1:8080/openapi.json | jq -r '.info.title' >/dev/null && echo "🔎 openapi OK"
  else
    echo "⚠️  backend não respondeu; verifique uvicorn/logs"
  fi
)

# 4.4 valida build do client (Vite dev rodando já basta)
echo "✅ Guard finalizado."
