FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# deps de sistema úteis (inclui curl para qualquer healthcheck interno)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# deps Python
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -r /app/requirements.txt

# código
COPY backend /app/backend

# script de start
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# porta interna fixa 8080 (Railway faz proxy $PORT -> 8080)
EXPOSE 8080

# inicia a API
CMD ["/app/start.sh"]
