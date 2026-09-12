import { defineConfig } from "@playwright/test";

// Runs the real frontend against the real backend, but the backend runs with FIXTURE_MODE=true (canned
// AeroAPI/OpenSky responses — see backend/app/clients/fixtures.py) so these tests are deterministic, free,
// and don't depend on any real flight being airborne. Requires `docker compose up -d db` from the repo
// root first (fixture mode still uses the real Postgres cache tables). See docs/TESTING.md#layer-4.
export default defineConfig({
  testDir: "./tests",
  timeout: 45_000,
  fullyParallel: true,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "python -m uvicorn app.main:app --port 8000",
      cwd: "../backend",
      url: "http://localhost:8000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: { FIXTURE_MODE: "true" },
    },
    {
      command: "npm run dev",
      cwd: "../frontend",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
});
