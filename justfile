# Travel AI World — task runner (humans and agents use the same commands).
# Install: https://just.systems  (winget install Casey.Just / brew install just / cargo install just)
#
#   just            list recipes
#   just setup      first-time setup
#   just dev-core   run core_api with hot reload

set shell := ["bash", "-euo", "pipefail", "-c"]
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

backend := "backend"
core := "backend/services/core_api"
ai := "backend/services/ai_api"
common := "backend/libs/travel_common"
frontend := "frontend"

# List available recipes
default:
    @just --list --unsorted

# ── Setup ────────────────────────────────────────────────────────────────────

# Create .env files from templates and install every dependency
setup:
    @[ -f {{core}}/.env ] || cp {{core}}/.env.example {{core}}/.env
    @[ -f {{ai}}/.env ] || cp {{ai}}/.env.example {{ai}}/.env
    @[ -f {{frontend}}/.env.local ] || cp {{frontend}}/.env.example {{frontend}}/.env.local
    cd {{backend}} && uv sync
    cd {{frontend}} && npm install
    @echo "Setup complete. Fill in SECRET_KEY (same value in both backend .env files), GOOGLE_* and NVIDIA_API_KEY."

# ── Run ──────────────────────────────────────────────────────────────────────

# core_api with hot reload on :8000
dev-core:
    cd {{core}} && uv run uvicorn core_api.main:app --reload --host 0.0.0.0 --port 8000

# ai_api with hot reload on :8001
dev-ai:
    cd {{ai}} && uv run uvicorn ai_api.main:app --reload --host 0.0.0.0 --port 8001

# Next.js dev server on :3000
dev-frontend:
    cd {{frontend}} && npm run dev

# ── Quality ──────────────────────────────────────────────────────────────────

# Lint backend (ruff) and frontend (eslint)
lint:
    cd {{backend}} && uv run ruff check . && uv run ruff format --check .
    cd {{frontend}} && npm run lint

# Auto-format the backend
format:
    cd {{backend}} && uv run ruff format . && uv run ruff check --fix .

# All tests: backend packages + frontend unit tests
test: test-backend test-frontend

# Every backend package (needs PostgreSQL for core_api)
test-backend: test-common test-core test-ai

test-common:
    cd {{common}} && uv run pytest -q

test-core:
    cd {{core}} && uv run pytest -q

test-ai:
    cd {{ai}} && uv run pytest -q

test-frontend:
    cd {{frontend}} && npm run test:unit

# Playwright E2E smoke tests (starts the dev server)
test-e2e:
    cd {{frontend}} && npx playwright test

# ── Contracts & docs ─────────────────────────────────────────────────────────

# Export OpenAPI documents and regenerate the frontend's TypeScript types
contracts:
    cd {{backend}} && uv run python scripts/export_openapi.py
    cd {{frontend}} && npm run types:generate

# Fail if OpenAPI documents or generated types are stale (what CI runs)
contracts-check:
    cd {{backend}} && uv run python scripts/export_openapi.py --check
    cd {{frontend}} && npm run types:check

# Documentation hygiene: required files present, links resolve
docs-check:
    python3 scripts/check_docs.py

# ── Database ─────────────────────────────────────────────────────────────────

# Apply core_api migrations
migrate:
    cd {{core}} && uv run alembic upgrade head

# Autogenerate a migration after changing core_api models: just migration "add x"
migration message:
    cd {{core}} && uv run alembic revision --autogenerate -m "{{message}}"

# ── Build & Docker ───────────────────────────────────────────────────────────

# Production static export of the frontend
build:
    cd {{frontend}} && npm run build

# Build both backend images locally
docker-build:
    cd {{backend}} && docker build --build-arg SERVICE=core_api -t travel-ai-world/core-api:local .
    cd {{backend}} && docker build --build-arg SERVICE=ai_api -t travel-ai-world/ai-api:local .

# Start proxy + core_api + ai_api + PostgreSQL
docker-up:
    cd {{backend}} && docker compose up --build -d

docker-down:
    cd {{backend}} && docker compose down

# Tail logs: just docker-logs core_api | ai_api | proxy
docker-logs service="core_api":
    cd {{backend}} && docker compose logs -f {{service}}

# ── Release ──────────────────────────────────────────────────────────────────

# Bump the version in every manifest (patch|minor|major)
version bump="patch":
    pwsh -NoLogo -File scripts/new_version.ps1 -Bump {{bump}}

# Create a GitHub release from main (needs gh)
release:
    pwsh -NoLogo -File scripts/new_release.ps1

# Remove virtualenvs, node_modules and build output
clean:
    rm -rf {{backend}}/.venv {{frontend}}/node_modules {{frontend}}/.next {{frontend}}/out
