# --- Build stage ---
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
# retries e flags pra instalação estável
RUN npm ci --no-audit --fund=false
COPY . .
# injeta a base de API no build
ARG VITE_API_BASE
ENV VITE_API_BASE=${VITE_API_BASE}
RUN npm run build

# --- Runtime (Nginx) ---
FROM nginx:alpine
# SPA fallback para /index.html
RUN sed -i 's|try_files .*;|try_files $uri $uri/ /index.html;|' /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
