# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y gcc curl wget && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 PORT=8000

# Healthcheck tolerante (não bloqueia deploy)
COPY healthcheck.sh /usr/local/bin/healthcheck.sh
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=6 \
  CMD /usr/local/bin/healthcheck.sh

# Loga a porta real e inicia uvicorn exatamente nela
CMD sh -c 'echo "[AUREA START] PORT=${PORT}"; exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}'
