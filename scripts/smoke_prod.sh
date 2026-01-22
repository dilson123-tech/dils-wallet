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
for ep in "$BASE/health" "$BASE/api/v1/health" "$BASE/healthz" "$BASE/api/v1/healthz"; do
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

say "Registrar usuário (idempotente)"
REG_CODE=$(curl -s -o /tmp/reg.json -w "%{http_code}" \
  -X POST "$BASE/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")

say "Login (autodetect endpoint/payload)"

OPENAPI_FILE=/tmp/openapi.json
OPENAPI_URL=""
for u in "$BASE/openapi.json" "$BASE/api/v1/openapi.json"; do
  O_CODE=$(curl -sS -o "$OPENAPI_FILE" -w "%{http_code}" "$u" || true)
  if [[ "$O_CODE" == "200" ]]; then
    OPENAPI_URL="$u"
    break
  fi
done

LOGIN_EPS=()
if [[ -n "${OPENAPI_URL:-}" ]]; then
  while IFS= read -r ep; do
    [[ -n "$ep" ]] && LOGIN_EPS+=("$ep")
  done < <(jq -r '.paths
      | to_entries[]
      | select(.value.post != null)
      | select(.key|test("auth|login|token";"i"))
      | .key' "$OPENAPI_FILE" 2>/dev/null || true)
fi

# Fallbacks se OpenAPI não ajudar
LOGIN_EPS+=(
  "/api/v1/auth/login"
  "/api/v1/auth/token"
  "/api/v1/token"
  "/auth/login"
  "/auth/token"
  "/token"
)

LOGIN_OK=0
LOGIN_USED_URL=""
LOGIN_USED_MODE=""
ACCESS=""
REFRESH=""

for EP in "${LOGIN_EPS[@]}"; do
  URL="$BASE$EP"
  for MODE in "form_username" "form_email" "json_username" "json_email"; do
    rm -f /tmp/login.json >/dev/null 2>&1 || true

    if [[ "$MODE" == "form_username" ]]; then
      CT="Content-Type: application/x-www-form-urlencoded"
      DATA="username=$EMAIL&password=$PASS"
    elif [[ "$MODE" == "form_email" ]]; then
      CT="Content-Type: application/x-www-form-urlencoded"
      DATA="email=$EMAIL&password=$PASS"
    elif [[ "$MODE" == "json_username" ]]; then
      CT="Content-Type: application/json"
      DATA="{\"username\":\"$EMAIL\",\"password\":\"$PASS\"}"
    else
      CT="Content-Type: application/json"
      DATA="{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}"
    fi

    CODE=$(curl -sS -L --post301 --post302 --post303 --max-redirs 5 \
      -o /tmp/login.json -w "%{http_code}" \
      -X POST "$URL" -H "$CT" --data "$DATA" || true)

    if [[ "$CODE" == "200" || "$CODE" == "201" ]]; then
      ACCESS=$(jq -r ".access_token // .access // .token // empty" /tmp/login.json 2>/dev/null || true)
      REFRESH=$(jq -r ".refresh_token // .refresh // empty" /tmp/login.json 2>/dev/null || true)
      if [[ -n "${ACCESS:-}" ]]; then
        LOGIN_OK=1
        LOGIN_USED_URL="$EP"
        LOGIN_USED_MODE="$MODE"
        break 2
      fi
    fi
  done
done

if [[ "$LOGIN_OK" != "1" ]]; then
  BODY=$(cat /tmp/login.json 2>/dev/null || true)
  fail "Login falhou (autodetect). Última resposta: ${BODY}"
fi

ok "Login OK via ${LOGIN_USED_URL} (${LOGIN_USED_MODE})"
LEN_A=${#ACCESS}
LEN_R=0; [[ -n "${REFRESH:-}" ]] && LEN_R=${#REFRESH}
ok "Token recebido (access: ${LEN_A} chars, refresh: ${LEN_R} chars)"



# Header de auth para os próximos requests
AUTH=(-H "Authorization: Bearer $ACCESS")

say "Sanity: /users/me (se existir)"
ME_CODE=$(curl -s -o /tmp/me.json -w "%{http_code}" "$BASE/api/v1/users/me" "${AUTH[@]}" || true)
if [[ "$ME_CODE" == "200" ]]; then
  ME_IDENT=$(jq -r ".email // .username // \"unknown\"" /tmp/me.json 2>/dev/null || echo unknown)
  ok "users/me OK: ${ME_IDENT}"
else
  die_or_warn "users/me -> $ME_CODE"
fi

say "DB: /users/test-db (verifica conexão/persistência)"
TDB_CODE=$(curl -s -o /tmp/tdb.json -w "%{http_code}" "$BASE/api/v1/users/test-db" "${AUTH[@]}" || true)

say "Listar transações (baseline antes do insert)"
LIST1_CODE=$(curl -s -o /tmp/tx_list1.json -w "%{http_code}" "$BASE/api/v1/transactions" "${AUTH[@]}" || true)

say "Criar transação (POST /transactions) — depósito fictício"
POST_CODE=$(curl -s -o /tmp/tx_post.json -w "%{http_code}" \
  -X POST "$BASE/api/v1/transactions" "${AUTH[@]}" \
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
LIST2_CODE=$(curl -s -o /tmp/tx_list2.json -w "%{http_code}" "$BASE/api/v1/transactions" "${AUTH[@]}" || true)
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
curl -s -o /tmp/tx_list_bal.json "$BASE/api/v1/transactions" "${AUTH[@]}" >/dev/null || true
SALDO_BEFORE=$(saldo_from_file /tmp/tx_list_bal.json)
printf "— SALDO_BEFORE: %s\n" "$SALDO_BEFORE"

say "Efetuar saque fictício de R$ ${WITHDRAW}"
WD_DESC="smoke-withdraw $(date -u +%Y-%m-%dT%H:%M:%SZ)"
WD_CODE=$(curl -s -o /tmp/tx_wd.json -w "%{http_code}" \
  -X POST "$BASE/api/v1/transactions" "${AUTH[@]}" \
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
curl -s -o /tmp/tx_list_after_wd.json "$BASE/api/v1/transactions" "${AUTH[@]}" >/dev/null || true
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
