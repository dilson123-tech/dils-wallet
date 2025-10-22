# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
# Railway injeta automaticamente o PORT (não fixar 8080)
EXPOSE 8000

# 🔥 bind dinâmico com fallback: usa $PORT se existir, senão 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
