# `.devcontainer` — Development Container

A reproducible VS Code environment for the whole monorepo: Node 24, Python 3.12, `uv`, `just`,
PostgreSQL client, plus the running stack.

## What starts

`docker-compose.yml` brings up:

| Service | Port (host) | Notes |
|---|---|---|
| `db` | 5433 | PostgreSQL 16, `travel`/`travel`, database `travel_ai_world` |
| `core_api` | 8000 | `uvicorn --reload` from the mounted source |
| `ai_api` | 8001 | `uvicorn --reload` from the mounted source |
| `frontend` | 3000 | `npm run dev` with both `NEXT_PUBLIC_*_URL` pointing at the services |
| `devcontainer` | — | your terminal; the repo is mounted at `/workspace` |

The backend services share one virtualenv in a named volume (`backend_venv`), so the host's
`backend/.venv` is never touched. `SECRET_KEY`, `GOOGLE_*` and `NVIDIA_API_KEY` are read from
`backend/services/core_api/.env` and `backend/services/ai_api/.env`: create them from the
`.env.example` files before opening the container (`just setup` does it).

## Use

1. VS Code → "Dev Containers: Reopen in Container".
2. Wait for the stack; open <http://localhost:3000>.
3. In the container terminal, the usual commands work: `just lint`, `just test`, `just migrate`, ...

To stop everything: `docker compose -f .devcontainer/docker-compose.yml down` on the host.
