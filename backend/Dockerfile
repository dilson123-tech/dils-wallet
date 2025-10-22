# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# deps básicas + wget p/ healthcheck
RUN apt-get update && apt-get install -y gcc curl wget && rm -rf /var/lib/apt/lists/*

# deps Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# código
COPY . .

ENV PYTHONUNBUFFERED=1

# Healthcheck interno: considera healthy quando /healthz responder 200
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
  CMD wget -qO- "http://127.0.0.1:${PORT:-8000}/healthz" >/dev/null || exit 1

# loga a porta e sobe o uvicorn ouvindo exatamente no $PORT do Railway
CMD sh -c 'echo "[BOOT] PORT=${PORT:-8000}"; uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}'
