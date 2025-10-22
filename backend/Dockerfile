# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

WORKDIR /app

# dependências básicas
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# instala dependências do projeto
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia código do backend
COPY . .

# define variáveis padrão (Railway injeta DATABASE_URL, etc)
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

EXPOSE 8080

# executa FastAPI com uvicorn ouvindo na porta $PORT
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
