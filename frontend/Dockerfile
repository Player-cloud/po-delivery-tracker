# Node 20, not the Node 24 you have locally — same reasoning as the backend's
# Python 3.13 choice: an isolated, well-tested LTS release for the container,
# independent of whatever version happens to be on your Windows machine.

# ---- Stage 1: install dependencies ----
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- Stage 2: build the app ----
FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ---- Stage 3: run it ----
# This is the ONLY stage that ships. Stages 1 and 2 (and everything heavy in
# them — dev tools, the full node_modules, source files) get discarded
# entirely once their output has been copied out below.
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

# The standalone build already bundles only the node_modules it actually
# needs — copied from the BUILDER stage's output, not reinstalled here.
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]