# End-to-end tests

Playwright tests driving the real frontend against the real backend, with the backend running in
`FIXTURE_MODE=true` (see `../backend/app/clients/fixtures.py`) so runs are deterministic and free. See
[`../docs/TESTING.md`](../docs/TESTING.md#layer-4-end-to-end-workflow-tests).

```bash
docker compose -f ../docker-compose.yml up -d db   # fixture mode still uses the real Postgres cache tables
npm install
npx playwright install --with-deps chromium

# playwright.config.ts just runs `python`, so activate the backend venv first (Playwright inherits
# whatever's on PATH — there's no portable way to hardcode a venv path across OSes in the config):
#   Windows:      ..\backend\.venv\Scripts\activate
#   macOS/Linux:  source ../backend/.venv/bin/activate
npx playwright test
```

`playwright.config.ts` starts both dev servers automatically (`webServer`), so you don't need to run them
yourself first.
