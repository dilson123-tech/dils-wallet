FROM python:3.11-slim

# Evita pty interativo
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala deps do sistema mínimas (psycopg2-binary dispensa build, então leve)
RUN pip install --upgrade pip

# Copia requirements da RAIZ (que referencia o do backend)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do projeto
COPY . .

# Porta padrão do Railway vem em $PORT
ENV PORT=8080
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "${PORT}"]
