FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN pip install --upgrade pip

# instala deps
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# copia app
COPY . /app

# Railway injeta PORT; define default pra rodar local se precisar
ENV PORT=8080

# >>> Shell form (expande ${PORT})
CMD sh -c 'python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}'
