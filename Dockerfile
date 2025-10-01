FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# deps de SO que ajudam nos logs/healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Python deps (cache só do pip, não do projeto)
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -r /app/requirements.txt

# código + start
COPY backend /app/backend
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8080
CMD ["/app/start.sh"]
