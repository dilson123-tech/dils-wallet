# base sem Docker Hub (Chainguard Python 3.11)
FROM cgr.dev/chainguard/python:3.11-dev

WORKDIR /app

# copie e instale deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copie o código
COPY backend /app

# porta do Railway
ENV PORT=8000
EXPOSE 8000

# start
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
