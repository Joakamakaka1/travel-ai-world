# AGENTS.md — Travel AI World

Instructions for coding agents (Claude Code, Codex, Cursor, Gemini CLI, Copilot, Antigravity, Jules, ...).
Humans: start at [README.md](README.md). This file is the **single source of truth for agents**;
tool-specific files (`.claude/CLAUDE.md`, `.claude/commands/`) only add what their tool needs.

The nearest `AGENTS.md` to the file you are editing wins:
[`backend/AGENTS.md`](backend/AGENTS.md) · [`backend/services/core_api/AGENTS.md`](backend/services/core_api/AGENTS.md) ·
[`backend/services/ai_api/AGENTS.md`](backend/services/ai_api/AGENTS.md) · [`frontend/AGENTS.md`](frontend/AGENTS.md)

## What this is

AI-powered travel planner. Static Next.js frontend + two FastAPI services:

| Path | Role | Talks to |
|---|---|---|
| `frontend/` | Next.js 16 static export (GitHub Pages) | `core_api`, `ai_api` |
| `backend/services/core_api/` | Google auth, users, trips CRUD | PostgreSQL |
| `backend/services/ai_api/` | LLM chat streaming (NVIDIA), future RAG | `core_api` (with the caller's token) |
| `backend/libs/travel_common/` | Shared kernel: Principal, settings, errors, JWT, app factory | — |
| `infra_terraform_{gcp,aws}/` | Two-service deployment | — |
| `docs/` | Architecture, ADRs, runbooks, OpenAPI documents | — |

Why two services: [docs/architecture/adr/0001-backend-split.md](docs/architecture/adr/0001-backend-split.md).
Diagram and request flows: [docs/architecture/overview.md](docs/architecture/overview.md).

## Commands (one interface for everyone: `just`)

```bash
just                # list recipes
just setup          # .env files + uv sync + npm install
just dev-core       # core_api  :8000 (hot reload)
just dev-ai         # ai_api    :8001 (hot reload)
just dev-frontend   # Next.js   :3000
just lint           # ruff + eslint
just test           # every backend package + frontend unit tests
just test-core / test-ai / test-common / test-frontend / test-e2e
just contracts      # export OpenAPI docs + regenerate frontend types (run after changing any schema/route)
just docs-check     # documentation hygiene
just migrate / just migration "message"
just docker-up      # proxy :8080 + core_api + ai_api + PostgreSQL
```

Windows: `winget install Casey.Just`; the recipes run under PowerShell there.
`just test-core` needs PostgreSQL (see `backend/services/core_api/.env.example`).

## Non-negotiable rules

1. **Run the checks before you finish**: `just lint`, the tests of every package you touched, and
   `just contracts` whenever a Pydantic schema or route changed (CI rejects drift).
2. **Keep the service boundary**: `ai_api` never imports `core_api` or SQLAlchemy; `core_api` never
   imports `ai_api`. They talk over HTTP. Shared code goes to `travel_common` only if both need it.
3. **Errors are domain errors**: raise `travel_common.exceptions.*` from services; never
   `HTTPException`; endpoints contain no `if not x: raise 404`.
4. **Identity is `Principal`**, never an ORM row, in any endpoint or use case.
5. **No secrets in code or docs.** `.env.example` files document variables; real values live in `.env` (ignored).
6. **Frontend strings go through i18n** (`useLanguage()`); components never call `fetch` directly
   (only `frontend/src/services/`).
7. **Docs travel with the change**: update the nearest `README.md`/`AGENTS.md`; add an ADR under
   `docs/architecture/adr/` for any decision that changes structure, contracts or infrastructure.
8. **Never edit generated files by hand**: `frontend/src/types/generated/`, `docs/api/*.openapi.json`, `uv.lock`, lockfiles.

## Conventions

- Python 3.12, `uv` workspace at `backend/` (one lockfile), ruff (line length 88, rules E4/E7/E9/F).
- TypeScript strict, Tailwind v4 (CSS custom properties, no `tailwind.config.js`), Vitest, Playwright.
- Commits: conventional prefixes (`feat`, `fix`, `refactor`, `build`, `ci`, `docs`, `infra`, `test`).
- Branches: `feat/TRA-123-short-title` (Linear issue key when there is one).
- PRs follow `.github/pull_request_template.md`; CI is `.github/workflows/pr.yml` (path-filtered jobs).

## Where things live

- Auth flow, chat flow, service-to-service calls → `docs/architecture/overview.md`
- Local dev, Docker, deploy, release → `docs/runbooks/`
- API contracts (generated) → `docs/api/*.openapi.json` and `frontend/src/types/generated/`
- Design file `ideas.pen` → only through Pencil MCP tools (Claude); never open with file tools.
