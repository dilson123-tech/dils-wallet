# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

WORKDIR /app

# Dependências básicas
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Instala requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código do backend
COPY . .

# Porta padrão (Railway substitui $PORT automaticamente)
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST=0.0.0.0

EXPOSE 8080

# Executa FastAPI ouvindo na porta $PORT (não fixa 8080)
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
