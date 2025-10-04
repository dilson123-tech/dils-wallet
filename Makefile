.PHONY: smoke smoke-wait smoke-url smoke-pass

# Variáveis utilitárias
OWNER_REPO := $(shell gh repo view --json nameWithOwner -q .nameWithOwner)
LAST_RUN_ID = $(shell gh run list --limit 1 --json databaseId -q '.[0].databaseId' 2>/dev/null)
TG_MSG_ID_FILE := artifacts/tg/smoke_prod/tg.msg_id
TG_TXT_FILE    := artifacts/tg/smoke_prod/tg.txt
TG_HTTP_FILE   := artifacts/tg/smoke_prod/tg.http

# 1) Smoke padrão (mantém seu comportamento atual, só organiza artefatos)
smoke:
	@mkdir -p artifacts/tg/smoke_prod
	@echo "[SMOKE] Disparando teste de fumaça..."
	@echo "🔔 Smoke iniciado em $$(date -Iseconds)" | tee $(TG_TXT_FILE)
	@HTTP=$$(curl -s -o $(TG_TXT_FILE) -w "%{http_code}" \
		-X POST "https://api.telegram.org/bot$${TG_BOT_TOKEN}/sendMessage" \
		-d chat_id="$${TG_CHAT_ID}" \
		--data-urlencode text="🚀 Smoke disparado: $$(date -Iseconds)"); \
	echo "$$HTTP" | tee $(TG_HTTP_FILE)
	@echo "HTTP TG = $$(cat $(TG_HTTP_FILE))"
	@echo "RUN URL: https://github.com/$(OWNER_REPO)/actions/runs/$(LAST_RUN_ID)"

# 2) Aguarda e mostra URL do run
smoke-url:
	@[ -n "$(LAST_RUN_ID)" ] || (echo "Sem run recente. Rode 'make smoke' antes."; exit 1)
	@echo "RUN URL: https://github.com/$(OWNER_REPO)/actions/runs/$(LAST_RUN_ID)"

# 3) Fluxo feliz: bate no /health, exige 200 e envia TG com link clicável
smoke-pass:
	@mkdir -p artifacts/tg/smoke_prod
	@[ -n "$${BASE}" ] || (echo "Defina BASE (ex: export BASE=https://<dominio>.up.railway.app)"; exit 1)
	@echo "[SMOKE-PASS] GET $$BASE/api/v1/health"
	@HTTP=$$(curl -s -o artifacts/health.json -w "%{http_code}" "$${BASE}/api/v1/health" || true); \
	if [ "$$HTTP" != "200" ]; then \
		echo "FAIL: health=$$HTTP"; \
		exit 2; \
	fi; \
	echo "OK: health=$$HTTP"
	@RUN_URL="https://github.com/$(OWNER_REPO)/actions/runs/$(LAST_RUN_ID)"; \
	MSG="✅ Smoke PASS • $$(date -Iseconds)%0A%0A• Run: $$RUN_URL%0A• Health: $${BASE}/api/v1/health"; \
	HTTP=$$(curl -s -o $(TG_TXT_FILE) -w "%{http_code}" \
		-X POST "https://api.telegram.org/bot$${TG_BOT_TOKEN}/sendMessage" \
		-d chat_id="$${TG_CHAT_ID}" \
		--data-urlencode text="$$MSG"); \
	echo "$$HTTP" | tee $(TG_HTTP_FILE); \
	echo "RUN URL: $$RUN_URL"
