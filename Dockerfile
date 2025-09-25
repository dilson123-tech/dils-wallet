FROM cgr.dev/chainguard/python:latest-dev
WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app
EXPOSE 8080

# use sh -c para o ${PORT} ser expandido no runtime do Railway
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"
