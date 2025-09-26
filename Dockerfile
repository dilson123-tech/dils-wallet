FROM cgr.dev/chainguard/python:latest-dev
WORKDIR /app

# Instala dependências
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia código
COPY backend /app

# Porta fixa para o serviço web
ENV PORT=8080
EXPOSE 8080

# Healthcheck interno (sem curl), usando o Python já presente na imagem
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=6 \
  CMD python - <<'PY'
import os, sys, urllib.request
port = os.getenv("PORT", "8080")
url = f"http://127.0.0.1:{port}/api/v1/health"
try:
    with urllib.request.urlopen(url, timeout=3) as r:
        sys.exit(0 if 200 <= r.status < 300 else 1)
except Exception:
    sys.exit(1)
PY

# Start explícito com python -m (robusto)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
