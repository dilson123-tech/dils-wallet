#!/usr/bin/env bash
set -eu

BASE="http://127.0.0.1:8000"
EMAIL="dilsonpereira231@gmail.com"

echo
echo ">>> Pergunta FORA do escopo (piada)..."
curl -s "$BASE/api/v1/ai/chat" \
  -H "Content-Type: application/json" \
  -H "X-User-Email: $EMAIL" \
  -d '{"message": "me conta uma piada"}'
echo
echo
echo ">>> Pergunta DENTRO do escopo (saldo hoje)..."
curl -s "$BASE/api/v1/ai/chat" \
  -H "Content-Type: application/json" \
  -H "X-User-Email: $EMAIL" \
  -d '{"message": "meu saldo hoje"}'
echo
