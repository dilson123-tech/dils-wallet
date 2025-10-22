# ---------- BUILD STAGE ----------
FROM node:20-alpine AS build
WORKDIR /app

# deps primeiro p/ cache
COPY package*.json ./
RUN npm ci --omit=dev --no-audit --no-fund

# código
COPY . .

# garante binário correto do esbuild para o ambiente
RUN npm rebuild esbuild

# build do Vite (gera ./dist)
RUN npm run build

# ---------- RUNTIME STAGE ----------
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
ENV NPM_CONFIG_CACHE=/tmp/npm-cache

# só o que precisamos em produção:
# - bundle estático
# - servidor node (server.cjs)
# - package.json/package-lock (para instalar deps de runtime se houver)
COPY --from=build /app/dist ./dist
COPY --from=build /app/server.cjs ./server.cjs
COPY --from=build /app/package*.json ./

# instala **somente** deps de produção do server
RUN npm ci --omit=dev --no-audit --no-fund

EXPOSE 8080
CMD ["node", "server.cjs"]
