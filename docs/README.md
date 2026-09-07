# Documentation

| Where | What |
|---|---|
| [architecture/overview.md](architecture/overview.md) | System diagram, request flows, service boundaries |
| [architecture/adr/](architecture/adr/README.md) | Architecture Decision Records (why things are the way they are) |
| [runbooks/](runbooks/local-dev.md) | How to run, ship and release: [local-dev](runbooks/local-dev.md), [docker](runbooks/docker.md), [deploy](runbooks/deploy.md), [release](runbooks/release.md) |
| [api/](api/) | Generated OpenAPI documents (`core-api`, `ai-api`) — source of the frontend's types |
| [superpowers/](superpowers/) | Feature specs and implementation plans |

Conventions: `README.md` files are for people (what it is, how to run it); `AGENTS.md` files are for
coding agents (rules, commands, where things live). Both live next to the code they describe.
Decisions go in ADRs, not in chat threads. `just docs-check` verifies the mechanical parts.
