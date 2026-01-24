FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# dependências
COPY requirements.txt /app/requirements.txt
COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --upgrade pip && pip install -r /app/requirements.txt

# código da app
COPY backend /app/backend
COPY start.sh /app/start.sh

# porta padrão (Railway injeta PORT; aqui só documenta)
EXPOSE 8000

# start — bind 0.0.0.0 e porta da Railway

RUN chmod +x backend/start.sh

CMD ["bash","backend/start.sh"]
