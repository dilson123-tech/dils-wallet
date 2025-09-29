FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN pip install --upgrade pip

# deps
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# app + healthcheck script
COPY . /app
COPY healthcheck.py /app/healthcheck.py

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
  CMD python /app/healthcheck.py

# usa o PORT injetado pelo Railway; fallback 8080
CMD /bin/sh -c "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080}"
