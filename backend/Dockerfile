FROM python:3.10-slim

# Variáveis padrão (Railway injeta PORT em runtime)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Sistema básico
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependências primeiro (para cache eficiente)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install uvicorn

# Código
COPY . /app

# Healthcheck leve (ajusta rota se precisar)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:${PORT:-8000}/healthz || exit 1

# Start usando variável PORT do Railway
CMD python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
