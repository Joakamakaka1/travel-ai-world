# 0003 — Frontend supports two base URLs; a reverse proxy is optional

**Status:** Accepted
**Date:** 2026-09-07

## Context

With two services the frontend must reach both. A single public origin needs a reverse proxy or
gateway in front of them. Locally that is a 20-line nginx config; on AWS the existing ALB does it
with a path rule; on GCP it would require a global Load Balancer (~18 USD/month fixed) that the
Terraform did not have. A full API gateway (Kong, APISIX) is disproportionate for two services.

## Decision

- `frontend/src/services/http.ts` is the only module that knows URLs. It reads
  `NEXT_PUBLIC_API_URL` (core) and `NEXT_PUBLIC_AI_API_URL` (ai). The second **defaults to the
  first**, so single-origin deployments configure one variable and two-origin deployments two.
- `ai_api` routes live under `/api/v1/ai/*`; every proxy rule is that one prefix.
- Docker Compose ships nginx (`backend/docker/nginx.conf`) with SSE buffering off; AWS uses an ALB
  listener rule; GCP uses two Cloud Run URLs with no proxy.
- A real gateway is adopted only when we need rate limiting, per-user AI quotas or edge auth.

## Consequences

- No infrastructure is required just to make the frontend work; each environment picks the
  cheapest shape.
- CORS is configured per service (`BACKEND_CORS_ORIGINS`), not at the proxy.
- The static GitHub Pages build sets neither variable; backend features degrade via
  `isApiAvailable()` / `isAiAvailable()`.
