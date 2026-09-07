# Runbook — local development

## Prerequisites

- Node.js ≥ 20 (CI uses 24), Python 3.12, [uv](https://github.com/astral-sh/uv), [just](https://just.systems)
- PostgreSQL 16 (local, Docker, or the devcontainer's)
- A Google OAuth client ID; an NVIDIA API key for the chat

## First run

```bash
just setup
```

Then edit the three env files it created:

| File | Must set |
|---|---|
| `backend/services/core_api/.env` | `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `DB_*` |
| `backend/services/ai_api/.env` | `SECRET_KEY` (**same value**), `NVIDIA_API_KEY` |
| `frontend/.env.local` | `NEXT_PUBLIC_GOOGLE_CLIENT_ID`, `NEXT_PUBLIC_API_URL=http://localhost:8000`, `NEXT_PUBLIC_AI_API_URL=http://localhost:8001` |

Generate a key: `python -c "import secrets; print(secrets.token_hex(32))"`.

## Run

Three terminals (or the devcontainer, which starts them all):

```bash
just migrate       # once, and after pulling new migrations
just dev-core      # http://localhost:8000/docs
just dev-ai        # http://localhost:8001/docs
just dev-frontend  # http://localhost:3000
```

## Before pushing

```bash
just lint
just test            # test-core needs PostgreSQL; it creates <DB_NAME>_test
just contracts       # only if you changed a schema or a route
just docs-check
```

## Devcontainer

Open the repo in VS Code → "Reopen in Container". `.devcontainer/docker-compose.yml` starts
PostgreSQL (`:5433` on the host), `core_api` (`:8000`), `ai_api` (`:8001`) and the frontend
(`:3000`), all with hot reload from the mounted source. Backend `.env` files are still required.
