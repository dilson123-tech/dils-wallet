FROM cgr.dev/chainguard/python:latest-dev
WORKDIR /app

# Instala dependências
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia código
COPY backend /app

# Apenas documentação da porta (Railway injeta PORT real)
EXPOSE 8080

# Start usando a PORT do Railway (com fallback p/ 8080 local)
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"
