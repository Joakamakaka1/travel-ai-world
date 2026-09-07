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

The server is declared in the repo's `.mcp.json` (`@playwright/mcp`, a frontend devDependency,
headless Chromium, isolated profile). It needs `npm install` in `src/frontend` and Chromium
(`npx playwright install --with-deps chromium`, done by the devcontainer's post-create). Claude
Code asks once to trust the project server; `/mcp` shows whether `playwright` is connected.
Tools are `mcp__playwright__browser_*` (`navigate`, `snapshot`, `click`, `type`,
`take_screenshot`, `console_messages`, `network_requests`, ...). Prefer `browser_snapshot`
(accessibility tree, cheap) over screenshots unless the check is visual.

`.mcp.json` also declares `playwright-host`: the same server attached over the Chrome DevTools
Protocol to a browser running on the **host** (`host.docker.internal:9222`). Use it from the
devcontainer when a visible, logged-in browser is wanted. The "Claude in Chrome" extension
(`claude --chrome`) is not supported in WSL or containers. On the host, start Chrome with a
dedicated profile (Chrome refuses remote debugging on the default one):

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="$env:LOCALAPPDATA\chrome-claude"
```

With `just dev-frontend` running, drive the browser through it:

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
