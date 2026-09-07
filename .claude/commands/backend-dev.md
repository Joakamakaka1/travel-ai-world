Run a backend service locally with hot reload.

The backend is two services; pick the one you are working on:

```bash
just dev-core   # core_api → http://localhost:8000/docs
just dev-ai     # ai_api   → http://localhost:8001/docs
```

Without `just`:

```bash
cd backend/services/core_api && uv run uvicorn core_api.main:app --reload --port 8000
cd backend/services/ai_api   && uv run uvicorn ai_api.main:app --reload --port 8001
```

Notes:

- Each service reads its own `.env` (`backend/services/<service>/.env`); `SECRET_KEY` must match.
- `core_api` needs PostgreSQL and `just migrate` first.
