FROM cgr.dev/chainguard/python:latest-dev

WORKDIR /app

# deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# código
COPY backend /app

# porta padrão usada pelo Railway
ENV PORT=8000
EXPOSE 8000

# start
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
