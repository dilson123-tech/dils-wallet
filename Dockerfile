FROM cgr.dev/chainguard/python:latest-dev
WORKDIR /app

# deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# código
COPY backend /app

# opcional (só documentação)
EXPOSE 8080

# usa a porta que o Railway injeta (fallback 8080 local)
CMD sh -c "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"
