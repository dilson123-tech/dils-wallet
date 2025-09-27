FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN pip install --upgrade pip

# deps
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# app
COPY . /app

# expõe porta e adiciona HEALTHCHECK interno (garante readiness do app)
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
  CMD wget -qO- http://127.0.0.1:$\{PORT:-8080\}/api/v1/health || exit 1

# inicia uvicorn com PORT expandido em runtime e log verboso
CMD /bin/sh -c "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level debug"
