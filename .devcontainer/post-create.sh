#!/usr/bin/env bash
# Runs once, after the devcontainer is created (see devcontainer.json).
set -euo pipefail
cd /workspace

# Named volumes are created root-owned; hand them to the workspace user.
sudo chown -R "$(id -u):$(id -g)" backend/.venv frontend/node_modules frontend/.next

# .env files from templates, uv sync (into the venv volume), npm install (into the node_modules volume).
just setup

# Schema of the devcontainer's PostgreSQL (DB_* come from docker-compose.yml).
just migrate

# Chromium for `just test-e2e` (system deps need sudo, which the base image grants).
(cd frontend && npx playwright install --with-deps chromium)

echo
echo "Devcontainer ready. Fill in SECRET_KEY (same in both backend .env files), GOOGLE_* and NVIDIA_API_KEY, then:"
echo "  just dev-core   # :8000"
echo "  just dev-ai     # :8001"
echo "  just dev-frontend  # :3000"
