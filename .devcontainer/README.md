# `.devcontainer` — Development Container

A reproducible VS Code environment for the monorepo: Node 24, Python 3.12 (via `uv`), `just`,
`gh`, ripgrep/fd/jq, Claude Code (plus optional agent CLIs), Playwright's Chromium, and a
PostgreSQL 16 container. **It does not run the application**: you start the services yourself
with the same `just` recipes everyone uses.

## What starts

| Service | Notes |
|---|---|
| `devcontainer` | your terminal; the repo is mounted at `/workspace` |
| `db` | PostgreSQL 16, `postgres`/`postgres`, database `travel_ai_world`, forwarded to `localhost:5432` |

`backend/.venv`, `frontend/node_modules` and `frontend/.next` are named Docker volumes, so the
host's copies (with their platform-specific binaries) are never touched.

On first creation `post-create.sh` runs `just setup` (creates the `.env` files, `uv sync`,
`npm install`), `just migrate` and installs Chromium for `just test-e2e`.

## Database wiring

The `devcontainer` service exports `DB_SERVER=db`, `DB_USER`, `DB_PASSWORD` and `DB_NAME`
as environment variables, which take precedence over `backend/services/core_api/.env`.
`just dev-core`, `just migrate` and `just test-core` therefore hit the `db` container with no
edits to the `.env`. The remaining keys (`SECRET_KEY`, `GOOGLE_*`, `NVIDIA_API_KEY`) still have
to be filled in the `.env` files, as in the [local-dev runbook](../docs/runbooks/local-dev.md).

## Use

1. VS Code → "Dev Containers: Reopen in Container" and wait for `post-create.sh` to finish.
2. Fill in the secrets in `backend/services/core_api/.env`, `backend/services/ai_api/.env`
   and `frontend/.env.local`.
3. In three terminals: `just dev-core`, `just dev-ai`, `just dev-frontend`. Ports 8000, 8001
   and 3000 are forwarded; open <http://localhost:3000>.
4. `just lint`, `just test`, `just test-e2e`, `just contracts` work as documented.

Closing the VS Code window stops the compose stack (`shutdownAction: stopCompose`); the
PostgreSQL data and the dependency volumes persist between sessions. To wipe them:
`docker compose -f .devcontainer/docker-compose.yml down -v` on the host.

If `postCreate` fails at `just migrate` with `password authentication failed for user
"postgres"`, the `postgres_data` volume was initialised by an older compose file with other
credentials (`POSTGRES_*` only apply on first init). Wipe the volumes as above and rebuild, or,
inside the container, create the missing role with the old credentials
(`psql -h db -U <old-user> -c "CREATE ROLE postgres LOGIN SUPERUSER PASSWORD 'postgres'"`) and
re-run `bash .devcontainer/post-create.sh`.

## Coding agents

| CLI | Installed | Config volume |
|---|---|---|
| Claude Code (`claude`) | always, native installer (self-updating) | `agent_claude` → `~/.claude` (`CLAUDE_CONFIG_DIR`) |
| Codex (`codex`) | default, via `EXTRA_AGENT_CLIS` | `agent_codex` → `~/.codex` |
| Gemini CLI (`gemini`) | default, via `EXTRA_AGENT_CLIS` | `agent_gemini` → `~/.gemini` |
| Copilot CLI (`copilot`) | default, via `EXTRA_AGENT_CLIS` | `agent_copilot` → `~/.copilot` |

Log in once inside the container (`claude`, `codex login`, `gemini`, `copilot`, `gh auth login`);
the credentials live in the named volumes above, so they survive "Rebuild Container". Shell
history is persisted the same way (`shell_history` → `/commandhistory`).

To change the optional set, export `DEVCONTAINER_EXTRA_AGENT_CLIS` on the host **before**
launching VS Code (it is a Compose build arg):

```bash
DEVCONTAINER_EXTRA_AGENT_CLIS="@openai/codex" code .   # Codex only
DEVCONTAINER_EXTRA_AGENT_CLIS="" code .                # Claude Code only
```

Then "Rebuild Container". Cursor, Antigravity and Jules run on the host or in the cloud and need
nothing here.

## VS Code extensions

`devcontainer.json` installs only extensions tied to the project's tooling: Claude Code, Python +
Pylance + Ruff, ESLint + Prettier + Tailwind, Vitest + Playwright, Terraform, TOML/YAML,
GitHub Actions, `just` syntax and Mermaid preview. Personal ones (Copilot, Gemini Code Assist,
GitLens, ...) go in **your** VS Code user settings so they follow you into every devcontainer:

```jsonc
// settings.json (user)
"dev.containers.defaultExtensions": ["github.copilot", "github.copilot-chat", "eamodio.gitlens"]
```

## Production-like stack

`backend/docker-compose.yml` (`just docker-up`: built images + nginx on `:8080`) is meant to run
**on the host**, not from inside the devcontainer, because it bind-mounts paths relative to
the host filesystem.
