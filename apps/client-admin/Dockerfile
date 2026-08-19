FROM node:20-slim AS builder

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /app

# Copy workspace and configuration files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml biome.json tsconfig.json* ./
COPY tooling/ ./tooling/
COPY packages/ ./packages/
COPY apps/client-admin/ ./apps/client-admin/

# Install dependencies
RUN pnpm install --frozen-lockfile

# Generate TanStack Router route tree and build application
RUN pnpm --filter @chirp/client-admin run generate:routes
RUN pnpm --filter @chirp/client-admin run build

FROM node:20-slim AS runner

WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3002

# Copy necessary runtime artifacts from builder
COPY --from=builder /app /app

EXPOSE 3002

CMD ["node", "apps/client-admin/.output/server/index.mjs"]
