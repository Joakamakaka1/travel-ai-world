# core_api

Google OAuth sign-in, users and trip data (trips, destinations, itinerary days, activities, meals,
accommodations, transportations) on PostgreSQL. Issues the JWTs every service trusts.

## Run

```bash
cp .env.example .env       # SECRET_KEY, GOOGLE_*, DB_*
uv run alembic upgrade head
uv run uvicorn core_api.main:app --reload --port 8000    # http://localhost:8000/docs
```

## Endpoints (`/api/v1`)

| Method | Path | Auth | Notes |
|---|---|---|---|
| `POST` | `/auth/google` | — | Google ID token → our JWT + profile |
| `GET` | `/users/me` | Bearer | Own profile |
| `GET` | `/users/` | Admin | List users |
| `GET/PUT/DELETE` | `/users/{id}` | Bearer | Read any; update/delete only your own |
| `PATCH` | `/users/{id}/role` | Admin | |
| `GET/POST` | `/trips/` | Bearer | Only the caller's trips |
| `GET/PUT/DELETE` | `/trips/{id}` | Bearer (owner) | 403 for another user's trip |
| CRUD | `/destinations/`, `/itinerary-days/`, `/activities/`, `/meals/`, `/accommodations/`, `/transportations/` | Bearer | Parent id as query param on create |
| `GET` | `/health/`, `/health/db` | — | |

Full contract: [`docs/api/core-api.openapi.json`](../../../../docs/api/core-api.openapi.json).

Errors: `{"detail": {"message": "...", "error_code": "NOT_FOUND" | "FORBIDDEN" | "UNAUTHORIZED" | ...}}`.

## Layout

```text
core_api/
├── main.py            create_app(settings, [api_router])
├── config.py          CoreSettings(CommonSettings): DB_*, GOOGLE_*
├── api/deps.py        get_current_user (JWT + DB check) → Principal; provide() wiring
├── api/v1/endpoints/  thin controllers
├── auth/google.py     Google tokeninfo verification
├── services/          base.py (generic) + one file per entity with its rules
├── repositories/      base.py (generic) + one file per entity with its queries
├── models/            SQLAlchemy tables (Base in base.py; register new ones in __init__.py)
├── schemas/           Pydantic request/response models
└── db/session.py      async engine + get_db
```

## Tests and migrations

```bash
uv run pytest                                          # creates <DB_NAME>_test, empties it per test
uv run alembic revision --autogenerate -m "message"    # after changing models; review the file
uv run alembic check                                   # models == migrations (CI runs it)
```

For agents: [`AGENTS.md`](AGENTS.md).
