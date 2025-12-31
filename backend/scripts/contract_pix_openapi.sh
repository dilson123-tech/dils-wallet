#!/usr/bin/env bash
set -euo pipefail

BASE="${1:-http://127.0.0.1:8000}"

echo "Checking PIX OpenAPI contract @ $BASE"

must_have_keys_get() {
  local path="$1"
  local keys
  keys="$(curl -sS "$BASE/openapi.json" | jq -r --arg p "$path" '.paths[$p].get.responses | keys | join(",")')"
  case "$keys" in
    *200*401*422*500*|*200*401*500*422*|*200*422*401*500*|*200*422*500*401*|*200*500*401*422*|*200*500*422*401*)
      echo "OK: GET $path exposes 200/401/422/500"
      ;;
    *)
      echo "FAIL: GET $path responses keys = $keys (expected 200,401,422,500)"
      exit 1
      ;;
  esac
}

must_have_keys_post() {
  local path="$1"
  local keys
  keys="$(curl -sS "$BASE/openapi.json" | jq -r --arg p "$path" '.paths[$p].post.responses | keys | join(",")')"
  case "$keys" in
    *200*401*422*500*|*200*401*500*422*|*200*422*401*500*|*200*422*500*401*|*200*500*401*422*|*200*500*422*401*)
      echo "OK: POST $path exposes 200/401/422/500"
      ;;
    *)
      echo "FAIL: POST $path responses keys = $keys (expected 200,401,422,500)"
      exit 1
      ;;
  esac
}

# forecast -> PixForecastResponse
ref_forecast="$(curl -sS "$BASE/openapi.json" | jq -r '.paths["/api/v1/pix/forecast"].get.responses["200"].content["application/json"].schema["$ref"]')"
test "$ref_forecast" = "#/components/schemas/PixForecastResponse" \
  && echo "OK: forecast -> PixForecastResponse" \
  || { echo "FAIL: forecast schema ref = $ref_forecast"; exit 1; }

# balance -> PixBalanceResponse
ref_balance="$(curl -sS "$BASE/openapi.json" | jq -r '.paths["/api/v1/pix/balance"].get.responses["200"].content["application/json"].schema["$ref"]')"
test "$ref_balance" = "#/components/schemas/PixBalanceResponse" \
  && echo "OK: balance  -> PixBalanceResponse" \
  || { echo "FAIL: balance schema ref = $ref_balance"; exit 1; }

# history -> PixHistoryResponse
ref_history="$(curl -sS "$BASE/openapi.json" | jq -r '.paths["/api/v1/pix/history"].get.responses["200"].content["application/json"].schema["$ref"]')"
test "$ref_history" = "#/components/schemas/PixHistoryResponse" \
  && echo "OK: history  -> PixHistoryResponse" \
  || { echo "FAIL: history schema ref = $ref_history"; exit 1; }

# list (GET) -> PixListItem[]
ref_list_type="$(curl -sS "$BASE/openapi.json" | jq -r '.paths["/api/v1/pix/list"].get.responses["200"].content["application/json"].schema.type')"
ref_list_items="$(curl -sS "$BASE/openapi.json" | jq -r '.paths["/api/v1/pix/list"].get.responses["200"].content["application/json"].schema.items["$ref"]')"
test "$ref_list_type" = "array" && test "$ref_list_items" = "#/components/schemas/PixListItem" \
  && echo "OK: list     -> PixListItem[]" \
  || { echo "FAIL: list schema type=$ref_list_type items_ref=$ref_list_items"; exit 1; }

# 7d (GET) -> Pix7dResponse
ref_7d="$(curl -sS "$BASE/openapi.json" | jq -r '.paths["/api/v1/pix/7d"].get.responses["200"].content["application/json"].schema["$ref"]')"
test "$ref_7d" = "#/components/schemas/Pix7dResponse" \
  && echo "OK: 7d       -> Pix7dResponse" \
  || { echo "FAIL: 7d schema ref = $ref_7d"; exit 1; }


# send (POST) -> PixSendResponse
ref_send="$(curl -sS "$BASE/openapi.json" | jq -r '.paths["/api/v1/pix/send"].post.responses["200"].content["application/json"].schema["$ref"]')"
test "$ref_send" = "#/components/schemas/PixSendResponse" \
  && echo "OK: send     -> PixSendResponse" \
  || { echo "FAIL: send schema ref = $ref_send"; exit 1; }

must_have_keys_get "/api/v1/pix/balance"
must_have_keys_get "/api/v1/pix/history"
must_have_keys_get "/api/v1/pix/list"
must_have_keys_get "/api/v1/pix/7d"
must_have_keys_post "/api/v1/pix/send"
