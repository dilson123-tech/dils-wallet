# syntax=docker/dockerfile:1
## ---------- Builder ----------
FROM node:20-alpine AS builder
WORKDIR /workspace
ENV NODE_ENV=development \
    NPM_CONFIG_PRODUCTION=false \
    npm_config_production=false \
    NPM_CONFIG_CACHE=/tmp/.npm \
    CI=false
RUN apk add --no-cache libc6-compat
COPY package*.json ./
RUN npm ci --include=dev --no-audit --no-fund
COPY . .
# fallback se vite não vier por algum motivo
RUN node -e "try{require('vite');process.exit(0)}catch(e){process.exit(1)}" || npm i -D vite
RUN npm rebuild esbuild || true
RUN npm run build

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
