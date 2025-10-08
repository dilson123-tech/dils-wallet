
.PHONY: export-pix-csv
export-pix-csv:
	@BASE_PROD="https://dils-wallet-production.up.railway.app"; \
	curl -s "$$BASE_PROD/api/v1/pix/history?limit=200" | jq -r \
	  "([\"id\",\"from_account_id\",\"to_account_id\",\"amount\",\"created_at\"]|@csv),
	   (.[]|[.id,.from_account_id,.to_account_id,.amount,.created_at]|@csv)" > pix_history.csv; \
	stat -c \"OK -> %n (%s bytes)\" pix_history.csv

.PHONY: export-pix-csv
export-pix-csv:
	@BASE_PROD="https://dils-wallet-production.up.railway.app"; \
	curl -s "$$BASE_PROD/api/v1/pix/history?limit=200" \
	| jq -r '(["id","from_account_id","to_account_id","amount","created_at"] | @csv), (.[] | [.id,.from_account_id,.to_account_id,.amount,.created_at] | @csv)' \
	> pix_history.csv; \
	stat -c "OK -> %n (%s bytes)" pix_history.csv

.PHONY: backup-db restore-db-latest
backup-db:
	@./scripts/backup_db.sh

# restaura o arquivo mais recente em um DB apontado por RESTORE_DATABASE_URL
restore-db-latest:
	@LATEST=$$(ls -1t backups/db_*.sql.gz | head -n 1); \
	: $${RESTORE_DATABASE_URL:?Defina RESTORE_DATABASE_URL}; \
	echo "[restore] usando $$LATEST -> $$RESTORE_DATABASE_URL"; \
	gunzip -c "$$LATEST" | psql "$$RESTORE_DATABASE_URL"

.PHONY: health-once watch-health notify-test
health-once:
	@set -a; . ./.env.local; set +a; \
	code=$$(curl -s -o /dev/null -w "%{http_code}" "$$HEALTH_URL"); \
	echo "HEALTH $$HEALTH_URL -> HTTP=$$code"

watch-health:
	@./scripts/health_watch.sh

notify-test:
	@set -a; . ./.env.local; set +a; \
	curl -s -X POST "https://api.telegram.org/bot$$TG_BOT_TOKEN/sendMessage" \
	-d "chat_id=$$TG_CHAT_ID" \
	--data-urlencode "text=🚀 Teste de notificação do Dils Wallet" >/dev/null && \
	echo "Enviado."

.PHONY: watch-health-bg stop-health status-health tail-health
watch-health-bg:
	@nohup ./scripts/health_watch.sh >> health.log 2>&1 & echo $$! > .health_watch.pid; \
	echo "watch-health iniciado em background (PID=$$(cat .health_watch.pid)). Logs: health.log"

stop-health:
	@PID=$$(cat .health_watch.pid 2>/dev/null || true); \
	if [ -n "$$PID" ] && ps -p $$PID >/dev/null 2>&1; then \
		kill $$PID && echo "Parado (PID=$$PID)"; \
	else \
		echo "Nenhum watcher rodando."; \
	fi; \
	rm -f .health_watch.pid || true

status-health:
	@PID=$$(cat .health_watch.pid 2>/dev/null || true); \
	if [ -n "$$PID" ] && ps -p $$PID >/dev/null 2>&1; then \
		echo "watch-health rodando (PID=$$PID)"; \
	else \
		echo "watch-health NÃO está rodando"; \
	fi

tail-health:
	@tail -n 100 -f health.log

.PHONY: watch-health-bg stop-health status-health tail-health health-doctor
watch-health-bg:
	@nohup ./scripts/health_watch.sh >> health.log 2>&1 & echo $$! > .health_watch.pid; \
	sleep 1; \
	if [ -s .health_watch.pid ] && ps -p $$(cat .health_watch.pid) >/dev/null 2>&1; then \
		echo "watch-health iniciado (PID=$$(cat .health_watch.pid)). Logs: health.log"; \
	else \
		echo "FALHOU ao iniciar watch-health."; \
		rm -f .health_watch.pid; \
		tail -n 80 health.log || true; \
		exit 1; \
	fi

stop-health:
	@PID=$$(cat .health_watch.pid 2>/dev/null || true); \
	if [ -n "$$PID" ] && ps -p $$PID >/dev/null 2>&1; then \
		kill $$PID && echo "Parado (PID=$$PID)"; \
	else \
		echo "Nenhum watcher rodando."; \
	fi; \
	rm -f .health_watch.pid || true

status-health:
	@PID=$$(cat .health_watch.pid 2>/dev/null || true); \
	if [ -n "$$PID" ] && ps -p $$PID >/dev/null 2>&1; then \
		echo "watch-health rodando (PID=$$PID)"; \
	else \
		echo "watch-health NÃO está rodando"; \
	fi

tail-health:
	@tail -n 100 -f health.log

health-doctor:
	@echo "[env]"; grep -E '^(HEALTH_URL|TG_BOT_TOKEN|TG_CHAT_ID)=' .env.local || echo "vars não encontradas"; \
	echo "[script perms]"; ls -l scripts/health_watch.sh || true; \
	echo "[last log]"; tail -n 80 health.log || true
