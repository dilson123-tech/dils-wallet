FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Vamos trabalhar dentro de /app/backend
WORKDIR /app/backend

# Instala deps primeiro (cache)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copia o código
COPY backend /app/backend

EXPOSE 8686
ENV SENTRY_ENV=dev

# Importa como você usa localmente (sem pacote 'backend')
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8686"]
