#!/usr/bin/env bash
set -euo pipefail
RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[1;33m'; NC='\033[0m'

restore_if_changed () {
  local SRC="$1" DST="$2"
  if [ ! -f "$DST" ]; then
    echo -e "${YLW}[guard] ${DST} ausente → restaurando snapshot${NC}"
    mkdir -p "$(dirname "$DST")"
    cp "$SRC" "$DST"
    return
  fi
  local A B; A=$(sha256sum "$SRC" | awk '{print $1}'); B=$(sha256sum "$DST" | awk '{print $1}')
  if [ "$A" != "$B" ]; then
    echo -e "${YLW}[guard] divergência em ${DST} → restaurando snapshot${NC}"
    cp "$SRC" "$DST"
  fi
}

BASE="src/_locked/pix"
restore_if_changed "$BASE/RecentPixList.tsx" "src/app/customer/components/RecentPixList.tsx"
restore_if_changed "$BASE/SummaryKpis.tsx"   "src/app/customer/components/SummaryKpis.tsx"
restore_if_changed "$BASE/PixChart.tsx"      "src/app/customer/components/PixChart.tsx"
restore_if_changed "$BASE/aurea.css"         "src/styles/aurea.css"

echo -e "${GRN}[guard] PIX UI OK — protegido contra perda acidental.${NC}"
