# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y gcc curl wget && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
# Railway injeta PORT; não fixa em 8080
EXPOSE 8000

# 🔎 Healthcheck: considera o container healthy quando /health responde 200
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -qO- "http://127.0.0.1:${PORT:-8000}/health" >/dev/null || exit 1

# 🔊 Uvicorn escutando na porta dinâmica do Railway
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
