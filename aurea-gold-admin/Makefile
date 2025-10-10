.RECIPEPREFIX := >
.PHONY: up stop logs health
PORT ?= 5178
HOST ?= 127.0.0.1
BASE := http://$(HOST):$(PORT)

up:
> pkill -f "vite" || true
> nohup npm run dev -- --host $(HOST) --port $(PORT) --strictPort > .vite.dev.log 2>&1 & echo $$! > .vite.pid
> for i in $$(seq 1 40); do code=$$(curl -s -o /dev/null -w '%{http_code}' "$(BASE)/"); [ "$$code" = "200" ] && echo "OK $(BASE)" && break; sleep 0.5; done
> bash scripts/health_spa.sh "$(BASE)"
> echo "✅ Dev pronto em $(BASE) (PID $$(cat .vite.pid))"

stop:
> [ -f .vite.pid ] && kill -9 $$(cat .vite.pid) || pkill -f "vite" || true
> rm -f .vite.pid

logs:
> tail -f .vite.dev.log

health:
> bash scripts/health_spa.sh "$(BASE)"
