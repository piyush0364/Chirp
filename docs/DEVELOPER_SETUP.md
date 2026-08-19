# Developer Setup Guide

### 1. Prerequisites
- **Node.js** >= 20.19.0 & **pnpm** >= 9.15.0 (`npm i -g pnpm`)
- **Python** >= 3.12 & **moon** >= 2.0 (`curl -fsSL https://moonrepo.dev/install/moon.sh | bash`)

### 2. Quick Install
```bash
# Install JS monorepo dependencies & configure git hooks
pnpm install

# Set up Python API virtual environment & dependencies
cd apps/api && python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]" && cd ../..

# Generate protocol buffer types, route trees & seed database
moon run proto:generate
pnpm run generate:routes
moon run api:db-seed
```

### 3. Local Development Services
```bash
moon run api:dev          # Python gRPC API (localhost:50051, health: :3001)
moon run client-user:dev  # User Web App (http://localhost:3000)
moon run client-admin:dev # Admin Dashboard (http://localhost:3002)
```

### 4. Code Quality & Testing Commands
```bash
moon run :lint            # Fast linting across all packages (Biome & Ruff)
pnpm format               # Format JS/TS codebase with Biome
moon run :typecheck       # Type check all TypeScript & Python code
moon run :test            # Run all unit tests across the monorepo
moon run :build           # Production build across all packages
```

### 5. Git Pre-Commit Hook
Pre-commit validation is auto-configured on `pnpm install` via `.githooks/pre-commit`.
Validate staged files manually at any time with `pnpm precommit`.
