import { expect, test } from "@playwright/test";

// Fixture idents served by the backend's FIXTURE_MODE clients — see
// backend/app/clients/fixtures.py and docs/TESTING.md#layer-4-end-to-end-workflow-tests.
const AIRBORNE_IDENT = "FIX100";
const LANDED_IDENT = "FIX200";
const TODAY = new Date().toISOString().slice(0, 10);

test.describe("flight lookup workflow", () => {
  test("search -> status -> history -> live map for an airborne fixture flight", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Flight number").fill(AIRBORNE_IDENT);
    await page.getByLabel("Date").fill(TODAY);
    await page.getByRole("button", { name: /Track flight/ }).click();

    await expect(page).toHaveURL(new RegExp(`/flight/${AIRBORNE_IDENT}/${TODAY}`));
    await expect(page.getByRole("heading", { name: new RegExp(AIRBORNE_IDENT) })).toBeVisible();

    // Status card: both legs' airport codes and a delay badge. Match the code heading specifically --
    // the IATA/ICAO line underneath (e.g. "SFO · SFO") also contains the same text otherwise.
    const statusCard = page.locator(".status-card");
    await expect(statusCard.getByRole("heading", { name: "SFO", exact: true })).toBeVisible();
    await expect(statusCard.getByRole("heading", { name: "ORD", exact: true })).toBeVisible();
    await expect(statusCard.locator(".badge")).toBeVisible();

    // History/trend chart with computed stats.
    await expect(page.locator(".history-stats")).toBeVisible();

    // Live map: reaches the "tracking" state with a rendered marker.
    const mapCard = page.locator(".map-card");
    await expect(mapCard.getByRole("heading", { name: "Live map" })).toBeVisible();
    await expect(page.locator(".leaflet-container")).toBeVisible({ timeout: 15_000 });
    const marker = page.locator(".plane-icon").first();
    await expect(marker).toBeVisible();

    // Position should move across polling cycles (the fixture OpenSky client advances it each poll —
    // see FixtureOpenSkyClient in backend/app/clients/fixtures.py).
    const positionBefore = await marker.evaluate((el) => (el as HTMLElement).style.transform);
    await page.waitForTimeout(13_000);
    const positionAfter = await marker.evaluate((el) => (el as HTMLElement).style.transform);
    expect(positionAfter).not.toBe(positionBefore);

    // Airport reference panels for both ends.
    await expect(page.locator(".airport-panels")).toContainText("San Francisco");
    await expect(page.locator(".airport-panels")).toContainText("Chicago");
  });

  test("a landed fixture flight shows the landed state, never a live map", async ({ page }) => {
    await page.goto(`/flight/${LANDED_IDENT}/${TODAY}`);

    await expect(page.getByRole("heading", { name: new RegExp(LANDED_IDENT) })).toBeVisible();
    await expect(page.locator(".map-card")).toContainText(/has landed/);
    await expect(page.locator(".leaflet-container")).toHaveCount(0);
  });

  test("an unknown flight shows a clear not-found state, not an error page", async ({ page }) => {
    await page.goto(`/flight/ZZZ999/${TODAY}`);

    await expect(page.getByRole("alert")).toContainText(/No flight found/);
  });
});
