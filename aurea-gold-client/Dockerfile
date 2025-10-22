# syntax=docker/dockerfile:1
## ---------- Builder ----------
FROM node:20-alpine AS builder
WORKDIR /app
# garantir que o builder NÃO está em production
ENV NODE_ENV=development
# mover cache do npm pra fora de node_modules (evita EBUSY)
ENV NPM_CONFIG_CACHE=/tmp/.npm
# deps necessárias p/ binário do esbuild no Alpine
RUN apk add --no-cache libc6-compat
COPY package*.json ./
# força incluir dev deps mesmo que exista .npmrc com production
RUN npm ci --include=dev --no-audit --no-fund
COPY . .
# alguns ambientes precisam rebuild do esbuild
RUN npm rebuild esbuild || true
RUN npm run build

## ---------- Runtime (Nginx) ----------
FROM nginx:1.25-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
