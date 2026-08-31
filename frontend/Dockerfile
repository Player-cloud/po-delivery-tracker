# The app is a static export (next.config.ts: output "export"). Build it, then
# serve ./out with nginx. Used by docker-compose for the local full-stack path;
# production deploys the same `out/` to Cloudflare Pages.

# ---- build ----
FROM node:20-slim AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# NEXT_PUBLIC_API_BASE_URL is intentionally unset here: in docker-compose the
# browser reaches the API from the host at http://localhost:8000 (the default).
RUN npm run build

# ---- serve ----
FROM nginx:1.27-alpine AS runner
COPY --from=builder /app/out /usr/share/nginx/html
RUN printf 'server {\n\
  listen 3000;\n\
  root /usr/share/nginx/html;\n\
  location / { try_files $uri $uri.html $uri/index.html =404; }\n\
  error_page 404 /404.html;\n\
}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
