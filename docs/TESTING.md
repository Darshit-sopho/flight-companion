# Test Plan

Three layers. The guiding rule: **no automated test run should spend real AeroAPI credit or depend on a real
flight being in the air.** External calls are mocked or replaced with recorded fixtures everywhere except one
deliberate manual smoke test.

## Layer 1 — Backend unit tests (`backend/tests/unit/`)

**Tooling**: `pytest`, `pytest-mock`/dependency injection for fakes, `respx` (or `httpx`'s mock transport) for
HTTP-level mocking of `httpx` calls made by `clients/aeroapi_client.py` and `clients/opensky_client.py`.

**What's covered**:
- `icao24_resolver.py` — the highest-value test target in the repo. Cases: registration found in local
  registry → resolves directly; registration missing/unregistered → falls back to callsign matching;
  callsign match ambiguous/absent → returns `unresolved` with no exception; a later status refresh reports a
  changed registration → resolver re-runs rather than trusting the cached icao24.
- `flight_status_service.py` — cache-hit vs. cache-expired vs. never-fetched decision logic; verifies AeroAPI
  is *not* called when a fresh cached row exists, and *is* called (once) when the TTL has expired.
- `flight_history_service.py` — on-time percentage, average delay, and trend-direction computation against
  synthetic occurrence data (including edge cases: zero history, all on-time, all delayed).
- `rate_limit.py` — the dev-safety AeroAPI call-budget guard trips at the configured threshold.

**Fixtures**: `backend/tests/fixtures/aeroapi/*.json` and `backend/tests/fixtures/opensky/*.json` hold
recorded (hand-built, based on real response shapes) payloads. When AeroAPI or OpenSky change their response
shape, update the fixture and the Pydantic schema together.

Run: `cd backend && pytest tests/unit`

## Layer 2 — Backend integration tests (`backend/tests/integration/`)

**Tooling**: `pytest` + FastAPI `TestClient`, against a real (ephemeral) test Postgres database — either a
`docker compose` service or `pytest-postgresql` — with HTTP calls to AeroAPI/OpenSky still mocked at the
`httpx` transport level (never mock at the service layer here — the point is to exercise the real service +
DB + router wiring together).

**What's covered**:
- Full request/response cycle for each router in `docs/API.md`: search → 200 with correct shape, unknown
  flight → 404, status/history/track endpoints against a seeded `flight_snapshot` row.
- Cache persistence across requests (second call within TTL hits the DB cache, not the mocked HTTP client —
  assert the mock was called exactly once).
- Migrations apply cleanly to a fresh database (`alembic upgrade head` as a fixture setup step).

Run: `cd backend && pytest tests/integration` (requires `docker compose up -d db` or the test-DB fixture
running).

## Layer 3 — Frontend unit tests (`frontend/tests/`)

**Tooling**: Vitest + React Testing Library.

**What's covered**:
- `useFlightStatus` / `useLiveTrack` hooks: polling starts/stops correctly, pauses on `visibilitychange`,
  stops once status is `landed`/`cancelled` — using a mocked `api/client.ts`.
- `StatusTimelineCard`, `DelayTrendChart`, `AirportInfoPanel`: render correctly given representative props,
  including the "not yet available" / empty-history / zero-occurrence edge cases.
- `LiveFlightMap`: renders each of the four `track` states (`tracking`, `not_airborne`, `landed`,
  `unavailable`) with visibly distinct content — this directly checks FR4.3/FR4.4 from
  [`REQUIREMENTS.md`](REQUIREMENTS.md).

Run: `cd frontend && npm test`

## Layer 4 — End-to-end workflow tests (`e2e/tests/`)

**Tooling**: Playwright, driving the real frontend against the real backend — but the backend runs with
`FIXTURE_MODE=true`, which swaps `aeroapi_client`/`opensky_client` for canned responses (same fixtures as
Layer 1/2) instead of live network calls. This makes e2e runs deterministic, free, and independent of whether
any real flight happens to be airborne.

**Covered workflow** (`e2e/tests/flight-lookup.spec.ts`):
1. Load the search page, submit a known fixture flight number + date.
2. Land on the detail page; assert status card, history chart, and airport panels render with the expected
   fixture values.
3. Assert the live map shows a "tracking" state with a visible marker (fixture flight is airborne in the
   canned data) and that position updates across two polling cycles (fixture server advances position on
   each successive call).
4. Assert a second fixture flight (landed) shows the map's "landed" state instead.

Run: `cd e2e && npm install && npx playwright test` (starts both dev servers automatically via Playwright's
`webServer` config, backend launched with `FIXTURE_MODE=true`).

## The one manual, non-automated test

Documented here rather than automated, since it deliberately spends real AeroAPI credit and depends on a real
flight's schedule: pick a real, currently-scheduled or airborne flight, run it through search → status →
history → live map by hand, and confirm icao24 resolution succeeds and the map shows genuine movement across
a couple of polling cycles. Budget: a small handful of AeroAPI calls, well within the $5/month free tier. Do
this after any change to `icao24_resolver.py`, `aeroapi_client.py`, or `opensky_client.py` before merging.

## Coverage expectations

Not chasing a specific percentage, but: every function in `services/` should have at least one unit test
covering its main path and its main failure/edge path; every router should have at least one integration test
per status code it can return; the core workflow must have e2e coverage before it's considered "done."

## CI

`.github/workflows/ci.yml` runs on every pull request (and on push to `main`), as three jobs mirroring the
layers above:

| Job | Runs |
|---|---|
| `backend` | `ruff check`, `alembic upgrade head`, `pytest` (unit + integration) against a real Postgres service container |
| `frontend` | typecheck, lint, Vitest unit tests, production build |
| `e2e` | Playwright, backend in `FIXTURE_MODE=true` — no real AeroAPI/OpenSky credentials needed in CI at all |

The Postgres service container in CI uses the same credentials as `docker-compose.yml`/the app's default
`DATABASE_URL`, so no extra secrets or environment configuration were needed to wire this up. `e2e` runs after
`backend`/`frontend` pass, since it's the slowest job (Playwright browser install + both dev servers) and
isn't worth running against a build that's already broken elsewhere.
