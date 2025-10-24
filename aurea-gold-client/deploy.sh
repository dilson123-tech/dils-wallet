#!/bin/bash
set -e

inicio=$(date +%s)
msg="${1:-deploy rápido cliente}"

echo -e "\033[1;34m────────────────────────────────────────────\033[0m"
echo -e "\033[1;33m🚀 Deploy Aurea Gold Client:\033[0m"
echo -e "\033[1;37mMensagem: '$msg'\033[0m"
echo -e "\033[1;34m────────────────────────────────────────────\033[0m"

echo -e "\033[1;36m🛠️  Build (Vite)...\033[0m"
npm ci
npm run build

git add -A
git commit -m "$msg" || echo "Nenhuma mudança para commitar"
git push origin main

echo -e "\033[1;36m📦 Subindo para Railway (aurea-gold-client)...\033[0m"
railway up --service aurea-gold-client

fim=$(date +%s)
duracao=$((fim - inicio))
min=$((duracao / 60)); seg=$((duracao % 60))

echo -e "\033[1;34m────────────────────────────────────────────\033[0m"
echo -e "\033[1;32m✅ Cliente no ar!\033[0m"
echo -e "\033[1;37m⏱️ Tempo total: ${min}m ${seg}s\033[0m"
echo -e "\033[1;34m────────────────────────────────────────────\033[0m"

# 🔁 keep: ensure commit for client

