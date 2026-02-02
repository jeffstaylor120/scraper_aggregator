# frontend/Dockerfile — Vite dev server for hot reload in Docker.
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# VITE_API_PROXY_TARGET set in compose so /api proxies to api:8000
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
