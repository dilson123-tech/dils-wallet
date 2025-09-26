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

# Start explícito com python -m (robusto)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
