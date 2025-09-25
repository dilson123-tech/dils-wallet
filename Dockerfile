FROM cgr.dev/chainguard/python:latest-dev

WORKDIR /app

# deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# código (copia o conteúdo de backend/ para /app)
COPY backend /app

# meta e fallback
EXPOSE 8080
CMD ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","${PORT:-8080}"]
