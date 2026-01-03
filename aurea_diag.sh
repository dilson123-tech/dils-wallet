#!/usr/bin/env bash
set -euo pipefail

# === Ajuste se seus domínios mudarem ===
BACK="https://dils-wallet-production.up.railway.app"
CLIENT="https://aurea-gold-client-production.up.railway.app"
USER_EMAIL="user@example.com"

echo "===== RAILWAY STATUS ====="
railway status || true

echo -e "\n===== VARS (dils-wallet) ====="
railway variables --service dils-wallet | egrep -i 'DATABASE|CORS|ORIGIN|ENVIRONMENT|PROJECT_NAME' || true

echo -e "\n===== HEALTH ====="
echo "# back /healthz"
curl -sS "$BACK/healthz" | jq . || true

echo -e "\n# openapi pix paths"
curl -sS "$BACK/openapi.json" | jq -r '.paths | keys[] | select(test("/pix"))' | sort || true

echo -e "\n===== PIX LIST (com header de usuário) ====="
curl -sS "$BACK/api/v1/pix/list" -H "X-User-Email: $USER_EMAIL" | jq . || true

echo -e "\n===== CORS PROBE (OPTIONS do client->back) ====="
ORIG="$CLIENT"
curl -sS -i -X OPTIONS "$BACK/api/v1/pix/list" \
  -H "Origin: $ORIG" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" | sed -n '1,30p' || true

echo -e "\n===== LOGS RECENTES (dils-wallet) ====="
railway logs --service dils-wallet --lines 160 || true

echo -e "\n===== RESUMO ====="
echo "BACK:  $BACK"
echo "CLIENT:$CLIENT"
