# ---------- build stage ----------
FROM node:20-alpine AS build
WORKDIR /app

# Dependências primeiro (cache eficiente)
COPY package*.json ./
RUN npm ci --omit=dev --no-audit --no-fund

# Código
COPY . .

# Garante binário do esbuild correto p/ ambiente
RUN npm rebuild esbuild

# Build Vite
RUN npm run build

# ---------- runtime stage ----------
FROM node:20-alpine
WORKDIR /app

# Evita EBUSY de cache
ENV NODE_ENV=production
ENV NPM_CONFIG_CACHE=/tmp/npm-cache

# Copia tudo que o server precisa
COPY --from=build /app ./

# Railway usa PORT; expõe 8080 por padrão
EXPOSE 8080

# Sobe o server que já existe no projeto
CMD ["node", "server.cjs"]
