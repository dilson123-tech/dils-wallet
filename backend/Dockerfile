# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y gcc curl wget && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
# Railway injeta $PORT; não fixe 8080
EXPOSE 8000

# Container só fica "healthy" quando responde 200 em /healthz (ou /)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=5 \
  CMD wget -qO- "http://127.0.0.1:${PORT:-8000}/healthz" >/dev/null || wget -qO- "http://127.0.0.1:${PORT:-8000}/" >/dev/null || exit 1

# Uvicorn ouvindo na porta dinâmica do Railway
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
