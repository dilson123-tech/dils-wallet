FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências de sistema (curl para o HEALTHCHECK)
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
 && rm -rf /var/lib/apt/lists/*

# Instala Python deps
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copia o app
COPY . /app

EXPOSE 8000

# 🔥 Healthcheck real: bate no /api/v1/health
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=24 \
  CMD curl -fsS "http://127.0.0.1:${PORT:-8000}/api/v1/health" || exit 1

# Start (usa ${PORT} do Railway)
CMD ["sh","-c","python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=*"]
