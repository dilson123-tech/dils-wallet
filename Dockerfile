FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN pip install --upgrade pip

# Copia só o requirements do backend primeiro (garante que o arquivo exista no contexto)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Agora copia o resto do projeto
COPY . /app

# Railway injeta $PORT
ENV PORT=8080
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "${PORT}"]
