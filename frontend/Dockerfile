# =========================
# Stage 1: Build React app
# =========================
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

RUN npm run build


# =========================
# Stage 2: Nginx runtime
# =========================
FROM nginx:alpine

ENV API_UPSTREAM=http://127.0.0.1:9000

COPY nginx/default.conf.template \
    /etc/nginx/templates/default.conf.template

COPY --from=build \
    /app/dist \
    /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK \
    --interval=15s \
    --timeout=5s \
    --start-period=5s \
    --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/healthz || exit 1
