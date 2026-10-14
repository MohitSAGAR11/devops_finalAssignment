# ---- Stage 1: build the static React bundle with Node ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# ---- Stage 2: serve it with an unprivileged Nginx (runs as uid 101, port 8080) ----
FROM nginxinc/nginx-unprivileged:1.30-alpine
# Pull in Alpine security fixes released after the base image was built (keeps Trivy green).
USER root
RUN apk upgrade --no-cache
ENV BACKEND_URL=http://backend:8000
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
USER 101
EXPOSE 8080
