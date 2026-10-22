import { test, expect, type Page } from "@playwright/test";
import { TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from "../src/services/session";
import { DRAFT_VERSION, PLANNER_DRAFT_KEY } from "../src/services/plannerDraft";
import { demoEventsFor } from "../src/services/plannerDemo";
import {
  BRIEF_COMPLETE,
  FIRST_ITINERARY_OPS,
  toSseBody,
} from "../src/data/planner-demo/session";
import { applyItineraryOps, EMPTY_ITINERARY } from "../src/hooks/plannerReducer";
import type { PlannerTurn } from "../src/types/planner";

/**
 * "Undo changes": a typed ask that changes the itinerary is taken back with one tap.
 * No backend: the recorded demo (`services/plannerDemo.ts`) answers, in the browser or through the
 * route mock below; "a thermal afternoon" swaps day 3's afternoon synagogue for Széchenyi.
 */

function fakeToken(sub: string, email: string): string {
  const b64url = (value: object) => Buffer.from(JSON.stringify(value)).toString("base64url");
  const exp = Math.floor(Date.now() / 1000) + 24 * 60 * 60;
  return `${b64url({ alg: "none", typ: "JWT" })}.${b64url({ sub, email, exp })}.`;
}

function seedTab(page: Page) {
  const email = process.env.E2E_EMAIL ?? "planner-undo@example.com";
  const token = process.env.E2E_TOKEN ?? fakeToken("planner-undo-e2e", email);
  const draft = {
    version: DRAFT_VERSION,
    sessionId: "planner-undo-e2e-session",
    draft: {
      messages: [
        {
          id: "m1",
          kind: "text",
          role: "assistant",
          content: "Done. I've put together a first 3-day itinerary.",
        },
      ],
      groups: {},
      brief: BRIEF_COMPLETE,
      missing: [],
      itinerary: applyItineraryOps(EMPTY_ITINERARY, FIRST_ITINERARY_OPS),
      shortlist: [],
    },
  };
  return page.addInitScript(
    ({ keys, session, stored }) => {
      window.localStorage.setItem(keys.user, JSON.stringify(session.user));
      window.localStorage.setItem(keys.token, session.token);
      if (window.sessionStorage.getItem("e2e_seeded")) return;
      window.sessionStorage.setItem("e2e_seeded", "1");
      window.sessionStorage.setItem(keys.draft, JSON.stringify(stored));
    },
    {
      keys: { token: TOKEN_STORAGE_KEY, user: USER_STORAGE_KEY, draft: PLANNER_DRAFT_KEY },
      session: { token, user: { id: "planner-undo-e2e", email, name: "Undo" } },
      stored: draft,
    }
  );
}

test.describe("Planner — undo what Kiri changed", () => {
  test.beforeEach(async ({ page }) => {
    await seedTab(page);
    await page.route("**/api/v1/ai/planner", async (route) => {
      const turn = route.request().postDataJSON() as PlannerTurn;
      await route.fulfill({
        status: 200,
        headers: { "content-type": "text/event-stream" },
        body: toSseBody(demoEventsFor(turn)),
      });
    });
    await page.route("**/tiles.openfreemap.org/**", (route) => route.abort());
  });

  test("a typed ask takes an activity out, and one tap puts it back", async ({ page }) => {
    await page.goto("/plan/");
    await page.getByRole("button", { name: /Open day 3/ }).click();
    const synagogue = page.getByRole("button", { name: "Change: Dohány Street Synagogue" });
    await expect(synagogue).toBeVisible();

    await page.getByPlaceholder("Ask for a change or search for something…").fill(
      "A thermal afternoon on day 3, please"
    );
    await page.getByRole("button", { name: "Send" }).click();

    await expect(page.getByRole("button", { name: "Change: Széchenyi Baths" })).toBeVisible({
      timeout: 15_000,
    });
    await expect(synagogue).toHaveCount(0);

    const undo = page.getByRole("button", { name: "Undo changes" });
    await expect(undo).toBeEnabled({ timeout: 15_000 });
    await undo.click();

    await expect(synagogue).toBeVisible();
    await expect(page.getByRole("button", { name: "Change: Széchenyi Baths" })).toHaveCount(0);
    await expect(undo).toHaveCount(0);
    await expect(page.getByText("Changes undone")).toBeAttached();
  });
});
