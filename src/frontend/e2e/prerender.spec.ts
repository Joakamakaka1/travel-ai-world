import { test, expect } from "@playwright/test";

test.describe("Static export — HTML as served, before any JS runs", () => {
  test("landing page arrives prerendered, not as a shell filled in on hydration", async ({
    request,
  }) => {
    const response = await request.get("/");
    expect(response.status()).toBe(200);

    const html = await response.text();

    expect(html).toContain("<header");
    expect(html).toContain("<footer");
    // in the served HTML because the landing reads `?redirect=` from `window`, not `useSearchParams`
    expect(html).toMatch(/Where to\?/);
    expect(html).toContain("<textarea");
  });
});

test.describe("The signed-in home — /dashboard/", () => {
  test("the shell is served; the trips are the browser's to fetch", async ({ request }) => {
    const response = await request.get("/dashboard/");
    expect(response.status()).toBe(200);

    const html = await response.text();
    // the shell prerenders; what is behind the guard can't, the session lives in the browser
    expect(html).toContain("<header");
    expect(html).not.toMatch(/3 days in Budapest/);
  });
});

test.describe("The planner — one static shell for every trip (/plan/?trip=)", () => {
  test("the shell is served for any id; the trip itself is fetched by the browser", async ({
    request,
  }) => {
    const response = await request.get("/plan/?trip=00000000-0000-0000-0000-000000000000");
    expect(response.status()).toBe(200);

    const html = await response.text();
    // the signed-in shell (header) is prerendered; trip content can't be, it is per user
    expect(html).toContain("<header");
    expect(html).not.toMatch(/3 days in Budapest/);
  });

  test("the old viewer's shell is still served, and still says nothing about a trip", async ({
    request,
  }) => {
    const response = await request.get("/trip/?id=00000000-0000-0000-0000-000000000000");
    expect(response.status()).toBe(200);
    expect(await response.text()).not.toMatch(/3 days in Budapest/);
  });

  test("the old per-id folders are gone: /trip/<id>/ is a 404", async ({ request }) => {
    const response = await request.get("/trip/trip_japan_2026/");
    expect(response.status()).toBe(404);
  });
});
