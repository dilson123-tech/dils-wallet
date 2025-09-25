FROM cgr.dev/chainguard/python:latest-dev

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app
# Sem EXPOSE e sem CMD — o Railway usará o Custom Start Command
