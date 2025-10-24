#!/bin/bash
set -e

inicio=$(date +%s)
msg="${1:-deploy rápido}"

echo -e "\033[1;34m────────────────────────────────────────────\033[0m"
echo -e "\033[1;33m🚀 Iniciando deploy Aurea Bank IA 2.0:\033[0m"
echo -e "\033[1;37mMensagem: '$msg'\033[0m"
echo -e "\033[1;34m────────────────────────────────────────────\033[0m"

git add -A
git commit -m "$msg" || echo "Nenhuma mudança para commitar"
git push origin main

echo -e "\033[1;36m📦 Subindo para Railway...\033[0m"
railway up --service dils-wallet2

fim=$(date +%s)
duracao=$((fim - inicio))
min=$((duracao / 60))
seg=$((duracao % 60))

echo -e "\033[1;34m────────────────────────────────────────────\033[0m"
echo -e "\033[1;32m✅ Deploy concluído com sucesso!\033[0m"
echo -e "\033[1;37m⏱️ Tempo total: ${min}m ${seg}s\033[0m"
echo -e "\033[1;34m────────────────────────────────────────────\033[0m"
