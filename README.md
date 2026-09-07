# Travel AI World ✈️

> AI-powered travel planning. Tell us where you want to go — our AI crafts a personalized, day-by-day itinerary in seconds.

## Project Overview

Travel AI World is a full-stack web application where users input their destination, dates, budget, group size, and travel style, and an AI generates a complete itinerary for them via real-time streaming.

The project is split into independent services:

| Service | Stack | Status |
|---|---|---|
| **`frontend/`** | Next.js 16 · Tailwind CSS v4 · TypeScript | ✅ Active |
| **`backend/services/core_api/`** | FastAPI · SQLAlchemy 2 · PostgreSQL · Google OAuth | ✅ Active |
| **`backend/services/ai_api/`** | FastAPI · NVIDIA chat models · SSE streaming | ✅ Active |
| **`backend/libs/travel_common/`** | Shared kernel (identity, settings, errors, JWT) | ✅ Active |
| **`Scraper/`** | Python · Playwright · httpx | 🔧 In development |
| **`infra_terraform_gcp/`** | Terraform · Google Cloud · Cloud Run · Cloud SQL | ✅ Ready |
| **`infra_terraform_aws/`** | Terraform · AWS · ECS Fargate · RDS | ✅ Ready |

---

## Repository Structure

```text
travel-ai-world/
├── frontend/          # Next.js web app (browser client)
├── backend/           # uv workspace: libs/travel_common + services/{core_api,ai_api}
├── docs/              # Architecture overview, ADRs, runbooks, generated OpenAPI docs
├── infra_terraform_gcp/ # GCP infrastructure (Cloud Run + Cloud SQL)
├── infra_terraform_aws/ # AWS infrastructure (ECS Fargate + RDS)
├── Scraper/           # City data scrapers (Madrid, Berlin)
│   ├── Madrid/
│   └── Madrid2.0/
├── .github/workflows/ # CI/CD (PR checks + GitHub Pages deploy)
├── justfile           # Task runner (setup, dev, lint, test, contracts, docker, release)
├── tasks.ps1          # Windows wrapper around the justfile
├── AGENTS.md          # Instructions for coding agents (CLAUDE.md imports it)
├── scripts/           # Automation scripts (versioning, releases)
├── ideas.pen          # Pencil design file — landing page mockup & design system
├── images/            # Design assets and generated images
└── README.md          # ← You are here
```

---

## Cloud Infrastructure

The repository includes Terraform configurations for both supported cloud providers:

- **[GCP infrastructure](infra_terraform_gcp/README.md)** — Cloud Run, Cloud SQL, Artifact Registry, VPC and Secret Manager.
- **[AWS infrastructure](infra_terraform_aws/README.md)** — ECS Fargate, RDS PostgreSQL, ECR, Application Load Balancer and Secrets Manager.

These are alternative deployment paths. Choose one provider for the project and apply only its Terraform configuration. Neither folder creates resources until `terraform apply` is explicitly executed.

Each infrastructure folder contains its own README with prerequisites, secret configuration, Docker image workflow and deployment commands.

---

## Quick Start

### Prerequisites

- **Node.js ≥ 20** — Frontend
- **Python 3.12 + [uv](https://github.com/astral-sh/uv)** — Backend
- **[just](https://just.systems)** — task runner (`winget install Casey.Just` / `brew install just`)
- **PostgreSQL** — for `core_api` (local, Docker or the devcontainer)
- A **Google Cloud OAuth Client ID** — for authentication; an **NVIDIA API key** for the chat

### Using the Task Runner (Recommended)

The `justfile` is the single interface for humans, CI and coding agents (`just` alone lists everything):

```bash
just setup          # .env files + all dependencies (frontend + backend)
just migrate        # core_api database migrations
just dev-core       # core_api on :8000
just dev-ai         # ai_api on :8001
just dev-frontend   # Next.js on :3000
just lint           # ruff + eslint
just test           # backend packages + frontend unit tests
just contracts      # OpenAPI docs → frontend TypeScript types
just docker-up      # proxy :8080 + core_api + ai_api + PostgreSQL
```

On Windows without `just`, `.\tasks.ps1 <recipe>` forwards to it. Full guide: [docs/runbooks/local-dev.md](docs/runbooks/local-dev.md).

### Manual Setup

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). See [`frontend/README.md`](./frontend/README.md) for full details.

#### Backend

```bash
cd backend
uv sync                                        # whole workspace
cp services/core_api/.env.example services/core_api/.env
cp services/ai_api/.env.example services/ai_api/.env   # same SECRET_KEY in both
cd services/core_api && uv run alembic upgrade head && uv run uvicorn core_api.main:app --reload --port 8000
cd services/ai_api   && uv run uvicorn ai_api.main:app --reload --port 8001
```

API docs at [http://localhost:8000/docs](http://localhost:8000/docs) and [http://localhost:8001/api/v1/ai/docs](http://localhost:8001/api/v1/ai/docs). See [`backend/README.md`](./backend/README.md).

### Environment Variables

#### core_api (`backend/services/core_api/.env`)

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | JWT signing secret — **identical** in `ai_api` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | ✅ | Google OAuth credentials |
| `DB_ENGINE`, `DB_SERVER`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | ✅ | PostgreSQL (SQLite possible for quick tests) |
| `BACKEND_CORS_ORIGINS`, `FRONTEND_URL` | | Frontend origins for CORS |

#### ai_api (`backend/services/ai_api/.env`)

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Same value as `core_api` — verifies its tokens |
| `NVIDIA_API_KEY` | ✅ | NVIDIA API key for the chat |
| `NVIDIA_CHAT_MODEL` | | Model id (default `moonshotai/kimi-k2.6`) |
| `CORE_API_URL` | | Where `core_api` lives (default `http://localhost:8000`) |

#### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | ✅ | Same Google Client ID as backend |
| `NEXT_PUBLIC_API_URL` | | `core_api` URL; omit for the static GitHub Pages build |
| `NEXT_PUBLIC_AI_API_URL` | | `ai_api` URL; defaults to `NEXT_PUBLIC_API_URL` (single-origin setups) |

---

## Authentication

Travel AI World uses **Google OAuth 2.0 exclusively** — there is no password-based login.

**Flow:**

1. User clicks "Sign in with Google" → Google returns an ID token
2. Frontend sends the token to `POST /api/v1/auth/google`
3. Backend verifies the token with Google, creates/updates the user in DB
4. Backend returns a JWT for subsequent authenticated API calls

---

## AI Chat

The trip planner (`PlannerCard`) streams AI-generated itineraries in real-time:

- **Backend**: `POST /api/v1/ai/chat` on `ai_api` — SSE streaming through an `LLMProvider` port (NVIDIA adapter today)
- **Frontend**: `streamChat()` in `services/chat.ts` consumes SSE chunks
- **Fallback**: when no API URL is set, the UI shows a static "coming soon" mode (GitHub Pages)

---

## API Endpoints

Generated contracts: [`docs/api/core-api.openapi.json`](docs/api/core-api.openapi.json) · [`docs/api/ai-api.openapi.json`](docs/api/ai-api.openapi.json).

| Method | Path | Service | Auth | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/google` | core | — | Google OAuth login → JWT |
| `POST` | `/api/v1/ai/chat` | ai | Bearer | AI chat streaming (SSE) |
| `GET` | `/api/v1/ai/health/` | ai | — | ai_api health |
| `GET` | `/api/v1/users/me` | core | Bearer | Current user profile |
| `GET` | `/api/v1/health/` | core | — | core_api health |
| `CRUD` | `/api/v1/trips/` | core | Bearer | The caller's trips |
| `CRUD` | `/api/v1/destinations/`, `/itinerary-days/`, `/activities/`, `/meals/`, `/accommodations/`, `/transportations/` | core | Bearer | Trip children |

---

## CI/CD

### PR Checks (`.github/workflows/pr.yml`)

Path-filtered jobs, so a frontend change does not start PostgreSQL:

| Job | Runs |
|---|---|
| `backend-lint` | `ruff check` + `ruff format --check` on the workspace |
| `backend-common` / `backend-core` / `backend-ai` | each package's tests; `core_api` also `alembic upgrade head` + `alembic check` |
| `docker-build` | builds both images, smoke-tests `ai_api`'s health route |
| `contracts` | OpenAPI documents and generated TypeScript types must match the code |
| `frontend` | eslint, Vitest, Playwright (static export), `next build` |
| `docs` | markdownlint, link check, `scripts/check_docs.py` |

### Backend images (`.github/workflows/backend-images.yml`)

Every push to `main` touching `backend/` publishes `ghcr.io/manupm87/travel-ai-world/core-api` and `.../ai-api` (tags: commit SHA, `latest`).

### Backend deploy (`.github/workflows/deploy-backend.yml`)

Manual: promotes the GHCR images to GCP or AWS and runs Terraform (plan by default). See [docs/runbooks/deploy.md](docs/runbooks/deploy.md).

### GitHub Pages Deploy (`.github/workflows/deploy.yml`)

Every push to `main`:

1. **Build** — `npm run build` with `NEXT_PUBLIC_BASE_PATH=/travel-ai-world`
2. **SPA fallback** — copies `out/index.html` → `out/404.html`
3. **Deploy** — uploads `out/` to GitHub Pages

Live at: 👉 `https://manupm87.github.io/travel-ai-world/`

---

## Docker

One parameterized `backend/Dockerfile` builds both images; `docker compose` runs them behind nginx:

```bash
just docker-up               # proxy :8080 → core_api / ai_api, PostgreSQL
just docker-logs ai_api
just docker-down
```

- **Multi-stage build** — dependency layer from the lockfile, packages installed non-editable, slim runtime, non-root user
- **Migrations** run on start only in the image that owns them (`core_api`)
- **SSE-safe proxy** — nginx buffering off for `/api/v1/ai/*`

Details: [docs/runbooks/docker.md](docs/runbooks/docker.md).

---

## Branding & Assets

- **Logo:** White airplane silhouette on a rounded indigo square (#4F6EF7)
- **Custom Favicon:** Dedicated `icon.png` for browser tabs
- **Iconography:** Professional SVG icons from [Lucide](https://lucide.dev/)

---

## Roadmap

- [x] Landing page (`/`)
- [x] EN 🇬🇧 / ES 🇪🇸 i18n
- [x] AI trip planner form (`/plan`)
- [x] Trip itinerary viewer (`/trip/[id]`)
- [x] FastAPI backend split into `core_api` (CRUD) and `ai_api` (LLM), one shared library
- [x] Google OAuth 2.0 authentication
- [x] AI chat streaming through an `LLMProvider` port (NVIDIA adapter)
- [x] CI/CD pipeline (path-filtered PR checks, contract checks, image publishing, GitHub Pages)
- [x] Dev tooling (`justfile`, devcontainer, docs hygiene)
- [ ] RAG over the scraped city data (`ai_api` `Retriever` port)
- [ ] User saved trips & dashboard
- [ ] PDF Export for itineraries
- [ ] Dark mode toggle customization
