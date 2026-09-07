# /check-site — Verify the site looks and works correctly

Use after UI or content changes. Two modes.

## Mode 1: automated smoke tests (Playwright)

```bash
just test-e2e                      # starts `next dev` on :3000 and runs src/frontend/e2e/smoke.spec.ts
cd src/frontend && npx playwright show-report
PLAYWRIGHT_BASE_URL=https://manupm87.github.io/travel-ai-world npx playwright test   # against the live site
```

CI runs the same suite plus `e2e/prerender.spec.ts` against the static export
(`npm run test:e2e:static`, served on :3100).

## Mode 2: live browser inspection (Playwright MCP)

With `just dev-frontend` running, drive the browser through the Playwright MCP server:

- "Navigate to <http://localhost:3000> and take a screenshot"
- "Open the language menu, choose ES and confirm the nav reads 'Cómo Funciona'"
- "Scroll to #features and confirm the feature cards are visible"
- "Go to /dashboard and check the planner card accepts a prompt"

## What the smoke tests cover

| Test | What it checks |
|---|---|
| Page title | `<title>` contains "Travel AI World" |
| Hero headline | "Your Dream Trip" visible on load |
| Nav links | Logo and primary links present |
| Language switcher | 🇬🇧 by default; switching to ES translates the nav and back |
| Features section | "Hyper-Personalized AI" card visible |
| Social proof | "50,000+" and "190+" stats visible |
| CTA | "Plan My Trip Free" link visible |
| Planner | the prompt input renders and accepts text |
| Prerender (static config only) | `/` arrives as full HTML before hydration |
