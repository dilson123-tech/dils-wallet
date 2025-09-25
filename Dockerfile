FROM cgr.dev/chainguard/python:latest-dev
WORKDIR /app

# deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# código
COPY backend /app

# apenas documenta; o Railway injeta $PORT
EXPOSE 8080

# MUITO IMPORTANTE: usar sh -c para $PORT ser expandido em runtime
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"
