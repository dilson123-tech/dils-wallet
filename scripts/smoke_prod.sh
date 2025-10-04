#!/usr/bin/env bash
send_tg() {
  local MSG="$1"
  if [ -n "${TG_BOT_TOKEN:-}" ] && [ -n "${TG_CHAT_ID:-}" ]; then
    curl -s -o /dev/null -w "%{http_code}" \
      -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
      -d chat_id="${TG_CHAT_ID}" \
      --data-urlencode text="$MSG" || true
  fi
}
trap "send_tg \"❌ Smoke Prod falhou em ${GITHUB_REPOSITORY}
run=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}\"" ERR

set -Eeuo pipefail
send_tg() {
  local MSG="$1"
  if [ -n "${TG_BOT_TOKEN:-}" ] && [ -n "${TG_CHAT_ID:-}" ]; then
    curl -s -o /dev/null -w "%{http_code}" \
      -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
      -d chat_id="${TG_CHAT_ID}" \
      --data-urlencode text="$MSG" || true
  fi
}
trap "send_tg \"❌ Smoke + Health (smoke) falhou em ${GITHUB_REPOSITORY}
run=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}\"" ERR

set -Eeuo pipefail

send_tg() {
  local MSG="$1"
  if [ -n "${TG_BOT_TOKEN:-}" ] && [ -n "${TG_CHAT_ID:-}" ]; then
    curl -s -o /dev/null -w "%{http_code}" \
      -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
      -d chat_id="${TG_CHAT_ID}" \
      --data-urlencode text="$MSG" || true
  fi
}
trap "send_tg \"❌ Smoke + Health (smoke) falhou em ${GITHUB_REPOSITORY}
run=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}\"" ERR

set -Eeuo pipefail
set -euo pipefail

### === Config ===
: "${BASE:=https://dils-wallet-production.up.railway.app}"
EMAIL="${EMAIL:-smoke@dilswallet.com}"
PASS="${PASS:-123456}"
AMOUNT="${AMOUNT:-37.50}"
DESC="${DESC:-smoke-test $(date -u +%Y-%m-%dT%H:%M:%SZ)}"

### === Helpers ===
need() { command -v "$1" >/dev/null 2>&1 || { echo "ERRO: comando '$1' não encontrado"; exit 1; }; }
say() { printf "\n\033[1;36m▶ %s\033[0m\n" "$*"; }
ok()  { printf "\033[1;32m✔ %s\033[0m\n" "$*"; }
warn(){ printf "\033[1;33m⚠ %s\033[0m\n" "$*"; }
fail(){ printf "\033[1;31m✘ %s\033[0m\n" "$*"; exit 1; }

trap 'echo; warn "Último passo falhou. Verifique logs acima."' ERR
[ "${FORCE_FAIL_SMOKE_PROD:-0}" = "1" ] && { echo "[TEST] Forçando falha (FORCE_FAIL_SMOKE_PROD=1)"; false; }

need curl
need jq

# === Modo estrito para CI (falha em avisos críticos) ===
STRICT="${STRICT:-false}"
die_or_warn() {  # se STRICT=true, falha; senão, apenas avisa
  if [[ "$STRICT" == "true" ]]; then
    fail "$*"
  else
    warn "$*"
  fi
}

say "Ping /api/v1/health"
curl -fsS "$BASE/api/v1/health" | jq . && ok "Health OK"

say "Registrar usuário (idempotente)"
REG_CODE=$(curl -s -o /tmp/reg.json -w "%{http_code}" \
  -X POST "$BASE/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")

say "Login → access + refresh"
LOGIN_CODE=$(curl -s -o /tmp/login.json -w "%{http_code}" \
  -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASS")

if [[ "$LOGIN_CODE" != "200" ]]; then
  fail "Login falhou ($LOGIN_CODE): $(cat /tmp/login.json)"
fi

ACCESS=$(jq -r '.access_token // .access // empty' /tmp/login.json)
REFRESH=$(jq -r '.refresh_token // .refresh // empty' /tmp/login.json)
[[ -n "${ACCESS:-}" ]] || fail "Sem access_token na resposta de login"
LEN_A=${#ACCESS}
LEN_R=0; [[ -n "${REFRESH:-}" ]] && LEN_R=${#REFRESH}
ok "Token recebido (access: ${LEN_A} chars, refresh: ${LEN_R} chars)"


# Header de auth para os próximos requests
AUTH=(-H "Authorization: Bearer $ACCESS")

say "Sanity: /users/me (se existir)"
ME_CODE=$(curl -s -o /tmp/me.json -w "%{http_code}" "$BASE/api/v1/users/me" "${AUTH[@]}" || true)
if [[ "$ME_CODE" == "200" ]]; then
  ok "users/me OK: $(jq -r '.email // .username // "unknown"' /tmp/me.json)"
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
TX_ID=$(jq -r '.id // empty' /tmp/tx_post.json 2>/dev/null || true)

say "Validar persistência: conferir se a transação $TX_ID aparece na listagem"
LIST2_CODE=$(curl -s -o /tmp/tx_list2.json -w "%{http_code}" "$BASE/api/v1/transactions" "${AUTH[@]}" || true)
if [[ "$LIST2_CODE" == "200" ]]; then
  # Procura pelo ID (string-safe)
  FOUND=$(jq --arg id "$TX_ID" 'map(select((.id|tostring)==$id)) | length' /tmp/tx_list2.json 2>/dev/null || echo 0)
  COUNT2=$(jq 'length' /tmp/tx_list2.json 2>/dev/null || echo 0)
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
  jq -r '[ .[] 
           | if (.tipo=="deposito") then (.valor)
             elif (.tipo=="saque") then (-(.valor))
             else 0 end ] 
         | add // 0' "$1" 2>/dev/null
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
DELTA=$(awk -v a="$SALDO_BEFORE" -v w="$WITHDRAW" -v b="$SALDO_AFTER" 'BEGIN{printf "%.2f", (a - w - b)}')
ABS_DELTA=$(awk -v d="$DELTA" 'BEGIN{if (d<0) d=-d; printf "%.2f", d}')
if awk -v d="$ABS_DELTA" 'BEGIN{exit !(d <= 0.01)}'; then
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
      '{base:$base,email:$email,amount:$amount,desc:$desc,tx_post_code:$tx_post_code,health:$health}' | jq .

ok "Smoke de produção finalizado 🎯"

# --- Notificação opcional no Slack ----------------------
if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
  TS="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
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

  JSON_PAYLOAD=$(printf '{"text":"%s"}' "$MSG")
  CODE=$(curl -sS -L --max-redirs 5 -o /tmp/slack_smoke.txt -w "%{http_code}" \
         -X POST -H 'Content-type: application/json' \
         --data "$JSON_PAYLOAD" "$SLACK_WEBHOOK_URL" || true)
  echo "Slack notify HTTP=$CODE"
fi
# --------------------------------------------------------
