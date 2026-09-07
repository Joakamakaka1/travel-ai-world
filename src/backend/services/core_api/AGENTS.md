# AGENTS.md — core_api

Read [`backend/AGENTS.md`](../../AGENTS.md) first. `core_api` owns authentication, users and trip data.

## Request lifecycle (N-tier, dependencies point inward)

```text
api/v1/endpoints/*.py   HTTP only: parse, inject, call the service, return a schema
      ↓
services/*.py           business rules; raise travel_common.exceptions.*; never import FastAPI
      ↓
repositories/*.py       SQLAlchemy only; never import Pydantic schemas
      ↓
models/*.py             tables (DeclarativeBase, SQLAlchemy 2 style)
```

- `api/deps.py`: `get_current_user` (JWT **plus** a DB check that the account is active) returns a
  `Principal`; `provide(Service, Repository)` wires services — do not write per-entity factories.
- `repositories/base.py` and `services/base.py` are generic. A new entity is:
  `models/x.py` → register in `models/__init__.py` → `schemas/x.py` → `repositories/x_repository.py`
  (`model = X`, only custom queries) → `services/x_service.py` (only custom rules) →
  `api/v1/endpoints/xs.py` → include in `api/v1/api_router.py` → `just migration "add x"`.
- Ownership: anything a user owns goes through `Service.get_owned(id, principal)` (see `TripService`).
  Known gap: nested entities (activities, meals, ...) are not yet ownership-checked (tracked in ADR 0001).
- Aggregates the API returns whole must eager-load children (`lazy="selectin"`); async serializers
  cannot lazy-load.

## Commands

```bash
uv run uvicorn core_api.main:app --reload --port 8000
uv run pytest                      # PostgreSQL: creates <DB_NAME>_test and empties it between tests
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "message"   # review the file before committing
uv run alembic check               # models and migrations agree (CI runs this)
```

Env: `.env.example`. Never add `NVIDIA_*` here — that is `ai_api`'s.
