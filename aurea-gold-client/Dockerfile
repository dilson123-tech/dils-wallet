# syntax=docker/dockerfile:1
## ---------- Builder ----------
FROM node:20-alpine AS builder
WORKDIR /workspace
ENV NODE_ENV=development
ENV NPM_CONFIG_CACHE=/tmp/.npm
RUN apk add --no-cache libc6-compat
COPY package*.json ./
RUN npm ci --include=dev --no-audit --no-fund
COPY . .
# esbuild em Alpine
RUN npm rebuild esbuild || true
RUN npm run build

## ---------- Runtime (Nginx) ----------
FROM nginx:1.25-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /workspace/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
