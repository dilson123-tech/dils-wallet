FROM cgr.dev/chainguard/python:latest
WORKDIR /app

# porta padrão só pra local; em produção o Railway injeta PORT
ENV PORT=8080
EXPOSE 8080

# servidor mínimo que sempre responde 200 em "/"
CMD sh -c 'echo "ok" > index.html && python -m http.server ${PORT:-8080}'
