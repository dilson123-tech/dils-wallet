#!/usr/bin/env bash
set -euo pipefail

: "${BASE:=http://127.0.0.1:8787}"
: "${TOKEN:?exporte TOKEN do remetente antes}"
: "${ALVO_TOKEN:?exporte ALVO_TOKEN do destinatário antes}"

tmp_rem=$(mktemp)
tmp_dst=$(mktemp)

# Baixa transações dos dois usuários
curl -s "$BASE/api/v1/transactions?limit=1000" -H "Authorization: Bearer $TOKEN" | jq '.[] | . + {"owner_email":"teste@dilswallet.com"}' > "$tmp_rem"
curl -s "$BASE/api/v1/transactions?limit=1000" -H "Authorization: Bearer $ALVO_TOKEN" | jq '.[] | . + {"owner_email":"alvo@teste.com"}' > "$tmp_dst"

# Consolida, ordena por criado_em e exporta CSV com header
jq -s '
  add
  | sort_by(.criado_em)
  | (["id","criado_em","tipo","valor","referencia","user_id","owner_email"] | @csv),
    ( .[] | [ .id, .criado_em, .tipo, .valor, (.referencia // ""), .user_id, .owner_email ] | @csv )
' "$tmp_rem" "$tmp_dst" > auditoria.csv

rm -f "$tmp_rem" "$tmp_dst"
echo "OK: auditoria.csv gerado"
