FROM node:22-slim AS deps
WORKDIR /app
COPY frontend/package.json ./
RUN npm install

FROM node:22-slim AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY frontend ./
COPY mcp_server/users.json ./mcp_server/users.json
COPY mcp_server/schema_metadata.json ./mcp_server/schema_metadata.json
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/mcp_server/users.json ./mcp_server/users.json
COPY --from=builder /app/mcp_server/schema_metadata.json ./mcp_server/schema_metadata.json
EXPOSE 3000
CMD ["node", "server.js"]
