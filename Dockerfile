FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# deps
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# código
COPY . /app

EXPOSE 8000
# usa $PORT do Railway; se não existir, cai pra 8000
CMD ["sh","-c","python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=*"]
