FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=${PORT:-8080}

WORKDIR /app
COPY canary_app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY canary_app /app
EXPOSE 8080
CMD python -m uvicorn main:app --host 0.0.0.0 --port ${PORT}
