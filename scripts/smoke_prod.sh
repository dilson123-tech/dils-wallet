#!/usr/bin/env bash
set -Eeuo pipefail
send_tg(){
  local MSG="$1"
  ARTDIR="${GITHUB_WORKSPACE:-.}/artifacts/tg/smoke_prod"
  mkdir -p "$ARTDIR"
  HTTP=$(curl -s -o "$ARTDIR/tg.txt" -w "%{http_code}" \
    -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
    -d chat_id="${TG_CHAT_ID}" \
    --data-urlencode text="$MSG") || true
  echo "HTTP=$HTTP" | tee "$ARTDIR/tg.http"
}
say() { printf "\n\033[1;36m▶ %s\033[0m\n" "$*"; }
ok()  { printf "\033[1;32m✔ %s\033[0m\n" "$*"; }
warn(){ printf "\033[1;33m⚠ %s\033[0m\n" "$*"; }
fail(){ printf "\033[1;31m✘ %s\033[0m\n" "$*"; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || { echo "ERRO: comando \"$1\" não encontrado"; exit 1; }; }


echo "FORCE_FAIL_SMOKE_PROD=${FORCE_FAIL_SMOKE_PROD:-unset}"
[ "${FORCE_FAIL_SMOKE_PROD:-0}" = "1" ] && { echo "[TEST] Forçando falha (FORCE_FAIL_SMOKE_PROD=1)"; false; }

need curl
need jq

# === Modo estrito para CI (falha em avisos críticos) ===
STRICT="${STRICT:-false}"

# === Handler de erro (sem aspas simples; à prova de unicode) ===
run="${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-}/actions/runs/${GITHUB_RUN_ID:-}"
on_err() {
  echo
  msg="Último passo falhou. Verifique logs acima. Run: ${run}"
  if declare -F warn >/dev/null 2>&1; then warn "$msg"; else echo "$msg"; fi
  if declare -F send_tg >/dev/null 2>&1; then
    send_tg "$(printf "%s\nRun: %s" "❌ Smoke Prod falhou em ${GITHUB_REPOSITORY:-?}" "${run}")"
  fi
}
trap on_err ERR
# =========================================================

die_or_warn() {  # se STRICT=true, falha; senão, apenas avisa
  if [[ "$STRICT" == "true" ]]; then
    fail "$*"
  else
    warn "$*"
  fi
}


# === Base URL (workflow usa SMOKE_BASE) ===
BASE="${BASE:-${SMOKE_BASE:-}}"
[[ -n "${BASE:-}" ]] || fail "FALTA SMOKE_BASE (base URL do backend)"
BASE="${BASE%/}"
if [[ "$BASE" == */api/v1 ]]; then BASE="${BASE%/api/v1}"; fi
ORIGIN="$BASE"
for suf in "/api/v1" "/api" "/v1"; do
  [[ "$ORIGIN" == *"$suf" ]] && ORIGIN="${ORIGIN%$suf}"
done
API_BASE="${ORIGIN}/api/v1"
EMAIL="${EMAIL:-smoke+${GITHUB_RUN_ID:-local}@dils-wallet.dev}"
PASS="${PASS:-123456}"
AMOUNT="${AMOUNT:-37.50}"
DESC="${DESC:-smoke-test $(date -u +%Y-%m-%dT%H:%M:%SZ)}"
WITHDRAW="${WITHDRAW:-5.00}"
say "Ping health"
H_AUTH=()
if [[ -n "${HEALTH_TOKEN:-}" ]]; then
  H_AUTH=(-H "Authorization: Bearer $HEALTH_TOKEN")
fi

health_call(){
  local url="$1" method="${2:-GET}"
  if [[ "$method" == "POST" ]]; then
    curl -sS -o /tmp/health.json -w "%{http_code}" -X POST "${H_AUTH[@]}" "$url" || true
  else
    curl -sS -o /tmp/health.json -w "%{http_code}" "${H_AUTH[@]}" "$url" || true
  fi
}

HEALTH_OK=0
for ep in "$BASE/health" "$API_BASE/health" "$BASE/healthz" "$API_BASE/healthz"; do
  H_CODE=$(health_call "$ep" GET)
  if [[ "$H_CODE" == "200" ]]; then
    (jq . /tmp/health.json >/dev/null 2>&1 && jq . /tmp/health.json) || cat /tmp/health.json
    ok "Health OK (GET ${ep})"
    HEALTH_OK=1
    break
  fi
  if [[ "$H_CODE" == "405" ]]; then
    H2_CODE=$(health_call "$ep" POST)
    if [[ "$H2_CODE" == "200" ]]; then
      (jq . /tmp/health.json >/dev/null 2>&1 && jq . /tmp/health.json) || cat /tmp/health.json
      ok "Health OK (POST ${ep})"
      HEALTH_OK=1
      break
    fi
  fi
done

if [[ "$HEALTH_OK" != "1" ]]; then
  fail "Health falhou em todos endpoints testados (ultimo HTTP ${H_CODE:-?})"
fi


# === PIX_ONLY_MODE_AUTODETECT =====================================
# Se o OpenAPI não expõe /api/v1/auth/login, este deploy é PIX-only.
OPENAPI_FILE="${OPENAPI_FILE:-/tmp/openapi.json}"
API_BASE="${API_BASE:-${BASE%/}/api/v1}"
POST_CODE="${POST_CODE:-SKIPPED}"
WD_CODE="${WD_CODE:-SKIPPED}"

# garante openapi local pra inspeção
if [[ ! -s "$OPENAPI_FILE" ]]; then
  curl -sS -o "$OPENAPI_FILE" "${BASE%/}/openapi.json" || true
fi

HAS_AUTH=$(jq -r ".paths | has(\"/api/v1/auth/login\")" "$OPENAPI_FILE" 2>/dev/null || echo false)
PIX_ONLY="${PIX_ONLY:-0}"
if [[ "$HAS_AUTH" != "true" ]]; then
  PIX_ONLY=1
  warn "OpenAPI sem /api/v1/auth/login → modo PIX-only (pula register/login/transactions)"

  pix_get(){
    local url="$1" out="$2" code
    code=$(curl -sS -o "$out" -w "%{http_code}" "$url" || true)
    [[ "$code" == "200" ]] && { echo "$code"; return 0; }
    if [[ -n "${HEALTH_TOKEN:-}" ]]; then
      code=$(curl -sS -o "$out" -w "%{http_code}" -H "Authorization: Bearer $HEALTH_TOKEN" "$url" || true)
      [[ "$code" == "200" ]] && { echo "$code"; return 0; }
      code=$(curl -sS -o "$out" -w "%{http_code}" -H "X-Health-Token: $HEALTH_TOKEN" "$url" || true)
      [[ "$code" == "200" ]] && { echo "$code"; return 0; }
    fi
    echo "$code"; return 1
  }

  say "PIX: list"
  PIX_LIST_CODE=$(pix_get "$API_BASE/pix/list" /tmp/pix_list.json) || {
    fail "PIX list falhou (HTTP $PIX_LIST_CODE): $(cat /tmp/pix_list.json 2>/dev/null || true)"
  }
  ok "PIX list OK (HTTP $PIX_LIST_CODE)"

  say "PIX: balance (tenta /balance e /saldo)"
  PIX_BAL_CODE=$(pix_get "$API_BASE/pix/balance" /tmp/pix_balance.json) || true
  if [[ "$PIX_BAL_CODE" != "200" ]]; then
    PIX_BAL_CODE=$(pix_get "$API_BASE/pix/saldo" /tmp/pix_balance.json) || {
      fail "PIX balance/saldo falhou (último HTTP $PIX_BAL_CODE): $(cat /tmp/pix_balance.json 2>/dev/null || true)"
    }
  fi
  ok "PIX balance/saldo OK (HTTP $PIX_BAL_CODE)"
fi
# ===================================================================

if [[ "${PIX_ONLY:-0}" != "1" ]]; then

# === PIX-ONLY fastpath (OpenAPI sem /auth) ===
# PROD atual (Railway) pode expor só PIX + health. Se não houver /auth no OpenAPI, não tenta login.
OPENAPI_URL="${OPENAPI_URL:-${ORIGIN:-$BASE}/openapi.json}"
OPENAPI="/tmp/openapi.json"
O_CODE=$(curl -sS -o "$OPENAPI" -w "%{http_code}" "$OPENAPI_URL" || true)

AUTH_PRESENT=0
if [[ "$O_CODE" == "200" ]] && jq -e '.paths|keys|map(test("/api/v1/auth/|/auth/|/token$|/login$"))|any' "$OPENAPI" >/dev/null 2>&1; then
  AUTH_PRESENT=1
fi

try_get_json() {
  local url="$1" out="$2" code
  code=$(curl -sS -o "$out" -w "%{http_code}" "$url" || true)
  if [[ "$code" == "200" ]]; then return 0; fi

  # Se exigir token, tenta HEALTH_TOKEN em headers comuns
  if [[ ("$code" == "401" || "$code" == "403") && -n "${HEALTH_TOKEN:-}" ]]; then
    code=$(curl -sS -o "$out" -w "%{http_code}" -H "X-Health-Token: $HEALTH_TOKEN" "$url" || true)
    if [[ "$code" == "200" ]]; then return 0; fi
    code=$(curl -sS -o "$out" -w "%{http_code}" -H "Authorization: Bearer $HEALTH_TOKEN" "$url" || true)
    if [[ "$code" == "200" ]]; then return 0; fi
  fi

  echo "HTTP=$code url=$url" >&2
  (head -c 400 "$out" 2>/dev/null || true) >&2
  return 1
}

if [[ "$AUTH_PRESENT" != "1" ]]; then
  warn "OpenAPI sem AUTH (PIX-only). Smoke vai validar apenas health + PIX endpoints."
  ORIGIN="${ORIGIN:-$BASE}"; ORIGIN="${ORIGIN%/}"
  API_BASE="${API_BASE:-$ORIGIN/api/v1}"

  # escolhe balance/saldo existente no OpenAPI
  BAL_PATH="/api/v1/pix/balance"
  SAL_PATH="/api/v1/pix/saldo"
  LIST_PATH="/api/v1/pix/list"

  if jq -e --arg p "$BAL_PATH" '.paths[$p]!=null' "$OPENAPI" >/dev/null 2>&1; then
    say "PIX: balance"
    try_get_json "$API_BASE/pix/balance" /tmp/pix_balance.json || fail "PIX balance falhou"
    (jq . /tmp/pix_balance.json >/dev/null 2>&1 && jq . /tmp/pix_balance.json) || cat /tmp/pix_balance.json
    ok "PIX balance OK"
  elif jq -e --arg p "$SAL_PATH" '.paths[$p]!=null' "$OPENAPI" >/dev/null 2>&1; then
    say "PIX: saldo"
    try_get_json "$API_BASE/pix/saldo" /tmp/pix_saldo.json || fail "PIX saldo falhou"
    (jq . /tmp/pix_saldo.json >/dev/null 2>&1 && jq . /tmp/pix_saldo.json) || cat /tmp/pix_saldo.json
    ok "PIX saldo OK"
  else
    fail "OpenAPI não tem /pix/balance nem /pix/saldo — não dá pra validar PIX"
  fi

  if jq -e --arg p "$LIST_PATH" '.paths[$p]!=null' "$OPENAPI" >/dev/null 2>&1; then
    say "PIX: list"
    try_get_json "$API_BASE/pix/list" /tmp/pix_list.json || fail "PIX list falhou"
    ok "PIX list OK"
  else
    warn "OpenAPI sem /pix/list — pulando"
  fi

  ok "PIX-only smoke OK ✅"
  exit 0
fi
# === END PIX-ONLY fastpath ===

say "Registrar usuário (idempotente)"
REG_CODE=$(curl -s -o /tmp/reg.json -w "%{http_code}" \
  -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")

say "Login (autodetect via OpenAPI)"
OPENAPI_FILE="/tmp/openapi.json"
OPENAPI_OK="0"
OPENAPI_URL=""
for u in "$ORIGIN/openapi.json" "$API_BASE/openapi.json" "$ORIGIN/api/openapi.json" "$ORIGIN/api/v1/openapi.json" "$BASE/openapi.json"; do
  code=$(curl -sS -o "$OPENAPI_FILE" -w "%{http_code}" "$u" || true)
  if [[ "$code" == "200" ]]; then OPENAPI_OK="1"; OPENAPI_URL="$u"; break; fi
done

echo "DEBUG base=$BASE"
echo "DEBUG origin=$ORIGIN"
echo "DEBUG api_base=$API_BASE"
echo "DEBUG openapi_ok=$OPENAPI_OK openapi_url=${OPENAPI_URL:-unset}"

# === API_BASE auto (from openapi) ===
# Se o OpenAPI tiver paths começando com /api/v1, usamos prefixo. Senão, API_BASE=ORIGIN puro.
OPENAPI_PATH="${OPENAPI_PATH:-/tmp/openapi.json}"
if [[ "${openapi_ok:-0}" = "1" ]] && [[ -s "${OPENAPI_PATH}" ]]; then
  if jq -e '.paths | keys[] | select(startswith("/api/v1/"))' "${OPENAPI_PATH}" >/dev/null 2>&1; then
    API_BASE="${ORIGIN%/}/api/v1"
  else
    API_BASE="${ORIGIN%/}"
  fi
  echo "DEBUG api_base_auto=${API_BASE}"
  echo "DEBUG openapi_auth_paths:"
  jq -r '.paths | to_entries[] | select(.key|test("auth|token|login";"i")) | "\(.key) methods=\(.value|keys|join(","))"' \
    "${OPENAPI_PATH}" | head -n 40 || true
fi
# ================================
CAND_URLS=""
if [[ "$OPENAPI_OK" == "1" ]]; then
  # pega paths que tenham POST e pareçam auth/login/token
  paths=$(jq -r ".paths | to_entries[] | select(.value.post != null) | .key | select(test(\"auth\";\"i\") and test(\"(login|token)\";\"i\"))" "$OPENAPI_FILE" 2>/dev/null || true)
  for path in $paths; do
    CAND_URLS="$CAND_URLS $ORIGIN$path"
  done
fi

# fallback (se OpenAPI estiver off)
if [[ -z "${CAND_URLS// }" ]]; then
  CAND_URLS="$API_BASE/auth/login $API_BASE/auth/token $API_BASE/token $BASE/auth/login $BASE/auth/token $BASE/token"
fi

LOGIN_OK="0"
LOGIN_USED_URL=""
LOGIN_USED_MODE=""
LAST_CODE=""
LAST_BODY=""
LAST_ALLOW=""

JSON_EMAIL=$(jq -nc --arg email "$EMAIL" --arg password "$PASS" "{email:\$email,password:\$password}")
JSON_USER=$(jq -nc --arg username "$EMAIL" --arg password "$PASS" "{username:\$username,password:\$password}")

for URL in $CAND_URLS; do
  # form
  CODE=$(curl -sS -o /tmp/login.json -w "%{http_code}" -X POST "$URL" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "username=$EMAIL" --data-urlencode "password=$PASS" || true)
  if [[ "$CODE" == "200" || "$CODE" == "201" ]]; then
    ACCESS=$(jq -r ".access_token // .access // .token // empty" /tmp/login.json 2>/dev/null || true)
    REFRESH=$(jq -r ".refresh_token // .refresh // empty" /tmp/login.json 2>/dev/null || true)
    if [[ -n "${ACCESS:-}" ]]; then LOGIN_OK="1"; LOGIN_USED_URL="$URL"; LOGIN_USED_MODE="form"; break; fi
  fi
  if [[ "$CODE" == "405" ]]; then
    LAST_ALLOW=$(curl -sSI -X OPTIONS "$URL" | tr -d "\r" | awk -F": " 'tolower($1)=="allow"{print $2}' || true)
  fi
  LAST_CODE="$CODE"; LAST_BODY="$(head -c 300 /tmp/login.json 2>/dev/null || true)"

  # json (email)
  CODE=$(curl -sS -o /tmp/login.json -w "%{http_code}" -X POST "$URL" \
    -H "Content-Type: application/json" \
    --data "$JSON_EMAIL" || true)
  if [[ "$CODE" == "200" || "$CODE" == "201" ]]; then
    ACCESS=$(jq -r ".access_token // .access // .token // empty" /tmp/login.json 2>/dev/null || true)
    REFRESH=$(jq -r ".refresh_token // .refresh // empty" /tmp/login.json 2>/dev/null || true)
    if [[ -n "${ACCESS:-}" ]]; then LOGIN_OK="1"; LOGIN_USED_URL="$URL"; LOGIN_USED_MODE="json_email"; break; fi
  fi
  if [[ "$CODE" == "405" ]]; then
    LAST_ALLOW=$(curl -sSI -X OPTIONS "$URL" | tr -d "\r" | awk -F": " 'tolower($1)=="allow"{print $2}' || true)
  fi
  LAST_CODE="$CODE"; LAST_BODY="$(head -c 300 /tmp/login.json 2>/dev/null || true)"

  # json (username)
  CODE=$(curl -sS -o /tmp/login.json -w "%{http_code}" -X POST "$URL" \
    -H "Content-Type: application/json" \
    --data "$JSON_USER" || true)
  if [[ "$CODE" == "200" || "$CODE" == "201" ]]; then
    ACCESS=$(jq -r ".access_token // .access // .token // empty" /tmp/login.json 2>/dev/null || true)
    REFRESH=$(jq -r ".refresh_token // .refresh // empty" /tmp/login.json 2>/dev/null || true)
    if [[ -n "${ACCESS:-}" ]]; then LOGIN_OK="1"; LOGIN_USED_URL="$URL"; LOGIN_USED_MODE="json_user"; break; fi
  fi
  if [[ "$CODE" == "405" ]]; then
    LAST_ALLOW=$(curl -sSI -X OPTIONS "$URL" | tr -d "\r" | awk -F": " 'tolower($1)=="allow"{print $2}' || true)
  fi
  LAST_CODE="$CODE"; LAST_BODY="$(head -c 300 /tmp/login.json 2>/dev/null || true)"
done

if [[ "$LOGIN_OK" != "1" ]]; then
  fail "Login falhou. Último HTTP=${LAST_CODE} allow=${LAST_ALLOW:-?} body=${LAST_BODY}"
fi
LEN_A=${#ACCESS}
LEN_R=0; [[ -n "${REFRESH:-}" ]] && LEN_R=${#REFRESH}
ok "Login OK via ${LOGIN_USED_URL} (${LOGIN_USED_MODE}) (access: ${LEN_A} chars, refresh: ${LEN_R} chars)"

AUTH=(-H "Authorization: Bearer $ACCESS")

say "Sanity: /users/me (se existir)"
ME_CODE=$(curl -s -o /tmp/me.json -w "%{http_code}" "$API_BASE/users/me" "${AUTH[@]}" || true)
if [[ "$ME_CODE" == "200" ]]; then
  ME_IDENT=$(jq -r ".email // .username // \"unknown\"" /tmp/me.json 2>/dev/null || echo unknown)
  ok "users/me OK: ${ME_IDENT}"
else
  die_or_warn "users/me -> $ME_CODE"
fi

say "DB: /users/test-db (verifica conexão/persistência)"
TDB_CODE=$(curl -s -o /tmp/tdb.json -w "%{http_code}" "$API_BASE/users/test-db" "${AUTH[@]}" || true)

say "Listar transações (baseline antes do insert)"
LIST1_CODE=$(curl -s -o /tmp/tx_list1.json -w "%{http_code}" "$API_BASE/transactions" "${AUTH[@]}" || true)

say "Criar transação (POST /transactions) — depósito fictício"
POST_CODE=$(curl -s -o /tmp/tx_post.json -w "%{http_code}" \
  -X POST "$API_BASE/transactions" "${AUTH[@]}" \
  -H "Content-Type: application/json" \
  -d "{\"tipo\":\"deposito\",\"valor\":$AMOUNT,\"descricao\":\"$DESC\",\"type\":\"deposit\",\"amount\":$AMOUNT,\"description\":\"$DESC\"}" || true)

if [[ "$POST_CODE" != "200" && "$POST_CODE" != "201" ]]; then
  echo "— Corpo de erro do POST /transactions (HTTP $POST_CODE):"
  cat /tmp/tx_post.json; echo
else
  echo "— Sucesso no POST /transactions (HTTP $POST_CODE):"
  cat /tmp/tx_post.json | jq -c . || cat /tmp/tx_post.json
fi

# === Validação de persistência: listar e confirmar que o ID recém-criado aparece ===
TX_ID=$(jq -r ".id // empty" /tmp/tx_post.json 2>/dev/null || true)

say "Validar persistência: conferir se a transação $TX_ID aparece na listagem"
LIST2_CODE=$(curl -s -o /tmp/tx_list2.json -w "%{http_code}" "$API_BASE/transactions" "${AUTH[@]}" || true)
if [[ "$LIST2_CODE" == "200" ]]; then
  # Procura pelo ID (string-safe)
  FOUND=$(jq --arg id "$TX_ID" "[.[] | select((.id|tostring)==\$id)] | length" /tmp/tx_list2.json 2>/dev/null || echo 0)
  COUNT2=$(jq "length" /tmp/tx_list2.json 2>/dev/null || echo 0)
  echo "— Lista pós-insert: total=$COUNT2, encontrados_com_id=$FOUND"
  if [[ -n "$TX_ID" && "$FOUND" -ge 1 ]]; then
    ok "Transação $TX_ID encontrada na listagem 🎯"
  else
    warn "Transação $TX_ID não apareceu (pode ser paginação/filtros no endpoint)."
  fi
else
  warn "GET /transactions (pós-insert) -> $LIST2_CODE"
fi

### === Saldo: calcular via listagem de transações ===
WITHDRAW="${WITHDRAW:-5.00}"

saldo_from_file() {
  # Soma depósitos e subtrai saques; default 0 se lista vazia
  jq -r "[.[] | if (.tipo==\"deposito\") then (.valor) elif (.tipo==\"saque\") then (-(.valor)) else 0 end] | add // 0" "$1" 2>/dev/null
}

say "Saldo (antes do saque) — somando lista atual"
# Recarrega lista atual para saldo base (caso a anterior não exista)
curl -s -o /tmp/tx_list_bal.json "$API_BASE/transactions" "${AUTH[@]}" >/dev/null || true
SALDO_BEFORE=$(saldo_from_file /tmp/tx_list_bal.json)
printf "— SALDO_BEFORE: %s\n" "$SALDO_BEFORE"

say "Efetuar saque fictício de R$ ${WITHDRAW}"
WD_DESC="smoke-withdraw $(date -u +%Y-%m-%dT%H:%M:%SZ)"
WD_CODE=$(curl -s -o /tmp/tx_wd.json -w "%{http_code}" \
  -X POST "$API_BASE/transactions" "${AUTH[@]}" \
  -H "Content-Type: application/json" \
  -d "{\"tipo\":\"saque\",\"valor\":${WITHDRAW},\"descricao\":\"${WD_DESC}\",\"type\":\"withdraw\",\"amount\":${WITHDRAW},\"description\":\"${WD_DESC}\"}" || true)

if [[ "$WD_CODE" != "200" && "$WD_CODE" != "201" ]]; then
  echo "— Erro no POST saque (HTTP $WD_CODE):"
  cat /tmp/tx_wd.json; echo
  warn "Saque não aplicado — pode haver bloqueio de saldo insuficiente ou regra de negócio."
else
  echo "— Sucesso no POST saque (HTTP $WD_CODE):"
  cat /tmp/tx_wd.json | jq -c . || cat /tmp/tx_wd.json
fi

say "Saldo (após saque) — recomputando da listagem"
curl -s -o /tmp/tx_list_after_wd.json "$API_BASE/transactions" "${AUTH[@]}" >/dev/null || true
SALDO_AFTER=$(saldo_from_file /tmp/tx_list_after_wd.json)
printf "— SALDO_AFTER: %s\n" "$SALDO_AFTER"

# Verificação aritmética com tolerância de centavos
  DELTA=$(python3 -c "from decimal import Decimal as D; a=D(\"$SALDO_BEFORE\"); w=D(\"$WITHDRAW\"); b=D(\"$SALDO_AFTER\"); print(f\"{(a-w-b):.2f}\")")
  ABS_DELTA=$(python3 -c "from decimal import Decimal as D; d=D(\"$DELTA\"); print(f\"{abs(d):.2f}\")")
  if python3 -c "from decimal import Decimal as D; import sys; sys.exit(0 if D(\"$ABS_DELTA\") <= D(\"0.01\") else 1)"; then
  ok "Saldo validado: BEFORE - WITHDRAW ≈ AFTER (dif=$ABS_DELTA)"
else
  die_or_warn "Saldo divergente: BEFORE=$SALDO_BEFORE, WITHDRAW=$WITHDRAW, AFTER=$SALDO_AFTER (dif=$ABS_DELTA)"
fi
fi


say "Resumo final"
jq -n --arg base "$BASE" \
      --arg email "$EMAIL" \
      --arg amount "$AMOUNT" \
      --arg desc "$DESC" \
      --arg health "OK" \
      --arg tx_post_code "$POST_CODE" \
      "{base:\$base,email:\$email,amount:\$amount,desc:\$desc,tx_post_code:\$tx_post_code,health:\$health}" | jq .

ok "Smoke de produção finalizado 🎯"

# --- Notificação opcional no Slack ----------------------
if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
  TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  STATUS="OK"
  # Monta texto resumido (sem vazar token):
  MSG="[$STATUS] smoke_prod • $TS
base=$BASE
email=$EMAIL
amount=$AMOUNT
desc=$DESC
tx_post_code=${TX_POST_CODE:-${POST_CODE:-}}
withdraw=${WITHDRAW:-0}
health=${health:-OK}"

  JSON_PAYLOAD=$(jq -n --arg text "$MSG" "{text:\$text}")
  CODE=$(curl -sS -L --max-redirs 5 -o /tmp/slack_smoke.txt -w "%{http_code}" \
         -X POST -H "Content-type: application/json" \
         --data "$JSON_PAYLOAD" "$SLACK_WEBHOOK_URL" || true)
  echo "Slack notify HTTP=$CODE"
fi
# --------------------------------------------------------
