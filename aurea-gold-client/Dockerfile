# syntax=docker/dockerfile:1
## ---------- Builder ----------
FROM node:20-alpine AS builder
WORKDIR /workspace
ENV NODE_ENV=development \
    NPM_CONFIG_PRODUCTION=false \
    npm_config_production=false \
    NPM_CONFIG_CACHE=/tmp/.npm \
    CI=false
RUN apk add --no-cache libc6-compat bash
COPY package*.json ./
RUN npm ci --include=dev --no-audit --no-fund
COPY . .
# fallback se vite não vier por algum motivo
RUN node -e "try{require('vite');process.exit(0)}catch(e){process.exit(1)}" || npm i -D vite
RUN npm rebuild esbuild || true
# Vite grava VITE_* no bundle em tempo de build; o Railway só repassa variáveis declaradas via ARG.
# Não declarar ARGs de dev (VITE_DEV_TOKEN etc.): iriam para o bundle público.
ARG VITE_API_BASE
RUN test -n "$VITE_API_BASE" || { echo "ERRO: VITE_API_BASE ausente no build" >&2; exit 1; }
# NODE_ENV=development acima existe só para instalar devDeps; o bundle precisa ser de produção.
RUN NODE_ENV=production npm run build

## ---------- Runtime (Node + serve) ----------
FROM node:20-alpine AS runtime
WORKDIR /app
# servidor estático
RUN npm i -g serve@14
COPY --from=builder /workspace/dist ./dist
ENV PORT=8080
EXPOSE 8080
# bind na porta que o Railway injeta
CMD ["sh", "-c", "serve -s dist -l $PORT"]
