FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN pip install --upgrade pip

# instala deps
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# copia o resto do projeto
COPY . .

# expõe a porta usada pelo Railway
EXPOSE 8080

# inicia o servidor FastAPI
CMD /bin/sh -c "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT"
