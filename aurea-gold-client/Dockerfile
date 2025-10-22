## ---------- Builder: instala devDeps e roda build Vite ----------
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
# npm ci inclui devDependencies; NÃO usar --omit=dev
RUN npm ci
COPY . .
RUN npm run build

## ---------- Runtime: Nginx servindo /dist ----------
FROM nginx:1.25-alpine AS runtime
# Config SPA com fallback para /index.html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
