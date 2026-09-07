# Claude Code — Travel AI World

@../AGENTS.md

Everything about the project, its commands and its rules lives in `AGENTS.md` (imported above).
This file adds only what is specific to Claude Code.

## Claude-specific

- **Slash commands** in `.claude/commands/`: `/backend-dev`, `/backend-test`, `/backend-lint`,
  `/backend-db-migrate`, `/check-site`, `/add-i18n-key`, `/add-language`, `/new-section`.
  They are thin wrappers over `just` recipes; prefer them when they exist.
- **Design file** `ideas.pen`: read or edit **only** with the Pencil MCP tools (`mcp_pencil_*`).
- **Browser checks**: use the Playwright MCP (or `just test-e2e`) as described in `/check-site`.
- When a task changes architecture, contracts or infrastructure, draft the ADR in
  `docs/architecture/adr/` in the same PR (template in that folder's README).
