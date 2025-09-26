FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=${PORT:-8080}

WORKDIR /app

# Como o build context é canary_app/, copiamos arquivos locais
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8080
CMD python -m uvicorn main:app --host 0.0.0.0 --port ${PORT}
