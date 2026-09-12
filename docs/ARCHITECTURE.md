# Architecture

## System overview

```
┌─────────────────┐        ┌──────────────────────┐        ┌─────────────────┐
│  React PWA       │  HTTP  │  FastAPI backend      │  HTTP  │  FlightAware     │
│  (frontend/)      │◄──────►│  (backend/)           │◄──────►│  AeroAPI         │
│                  │  JSON  │                      │        │  (status/history)│
└─────────────────┘        │  ┌────────────────┐  │        └─────────────────┘
                            │  │  Postgres       │  │        ┌─────────────────┐
                            │  │  (cache + data) │  │◄──────►│  OpenSky Network │
                            │  └────────────────┘  │  HTTP  │  (live position) │
                            └──────────────────────┘        └─────────────────┘
```

The frontend never talks to AeroAPI or OpenSky directly, and never holds their credentials — only the backend
does. This keeps API keys server-side and gives one place to enforce caching/cost-control rules.

## Backend module layout

```
backend/app/
  clients/      raw HTTP wrappers — auth headers, base URLs, error handling. No caching or business logic.
  services/     all business logic: caching decisions, aggregation, the icao24 resolver.
  routers/      thin FastAPI route handlers that call into services.
  db/models.py  SQLAlchemy ORM models.
  schemas/      Pydantic request/response DTOs (kept separate from ORM models).
  core/         cache TTL helper, dev-time AeroAPI call-budget guard.
```

## Request flow (example: viewing a flight)

1. Frontend calls `GET /api/flights/search?ident=UAL123&date=2026-09-12`.
2. `flight_lookup_service` normalizes the input, checks `flight_snapshot` for a fresh cached row; if missing/
   stale, calls `aeroapi_client` and upserts the row. Returns a synthetic `flight_id`.
3. Frontend navigates to `/flight/UAL123/2026-09-12`, which fetches `/api/flights/{flight_id}`,
   `/api/flights/{flight_id}/history`, and (if the flight is active) starts polling
   `/api/flights/{flight_id}/track`.
4. `flight_status_service` serves the cached snapshot if still fresh, else refreshes from AeroAPI and updates
   `last_viewed_at` — this timestamp is what future background-refresh logic (if ever added) would key off of.
5. `live_tracking_service` resolves the flight's `icao24` (see below), throttles actual OpenSky calls to at
   most one per `OPENSKY_MIN_POLL_INTERVAL_SECONDS`, and returns the latest known position.

## AeroAPI ↔ OpenSky linking

The hardest problem in this system: AeroAPI and OpenSky have no shared identifier, and the link between a
flight number and a physical aircraft changes daily.

**Resolution pipeline** (implemented in `backend/app/services/icao24_resolver.py`):

1. Read the aircraft **registration** (tail number, e.g. `N12345`) from the AeroAPI flight-instance data
   already fetched by `flight_lookup_service`.
2. Look up `registration → icao24` in the local `aircraft_registry` table, which is periodically synced from
   OpenSky's public aircraft database dump (a batch job, not a live per-request call).
3. **Fallback** if the registration is missing or not found locally: query OpenSky `/states/all` and match on
   normalized `callsign` (whitespace-stripped, case-insensitive). This path is noisier — callsigns aren't
   always populated — so results from it are marked with lower `resolution_confidence`.
4. Store the resolved `icao24` (and resolution method/confidence) on the `tracked_flight` row, keyed by
   `flight_id` — **never** keyed by bare flight number, since the same number flies a different tail tomorrow.
5. If a later AeroAPI refresh reports a *different* registration than the one originally resolved (aircraft
   swap), re-run resolution rather than trusting the cached `icao24`.

**Edge cases the resolver must handle:**
- Codeshare flights: the marketing ident (what the user searched) may differ from the operating carrier's
  broadcast callsign. Try both idents when doing callsign fallback matching.
- Aircraft not transmitting ADS-B (older regional equipment, or simply out of coverage): return an explicit
  "unresolved" state, not an error — the frontend shows "live tracking unavailable."
- On-ground vs. airborne: OpenSky's `on_ground` flag must be surfaced so the frontend doesn't imply mid-flight
  motion from stale/zero-speed ground data.

## Cost control

AeroAPI is billed per query; OpenSky is free. See [`DATA_SOURCES.md`](DATA_SOURCES.md#cost-control) for the
full caching-TTL table. The short version: status/gate/delay data is cached with a 5–15 minute TTL and only
refreshed while a flight is actively being viewed; historical data is cached for days to indefinitely; live
position never touches AeroAPI at all.

## Data model

See `backend/app/db/models.py` for the source of truth. Summary:

| Table | Purpose |
|---|---|
| `airport` | Static reference data: code, name, city, lat/lon, timezone |
| `aircraft_registry` | `icao24 ↔ registration` mapping, synced from OpenSky's aircraft DB |
| `flight_snapshot` | Current status/times/gate/delay per flight instance, with cache timestamps |
| `flight_history_record` | One row per past occurrence of a flight number/route |
| `live_position` | Append-only position log per flight instance (also drives the map's breadcrumb trail) |
| `tracked_flight` | icao24 resolution state: method, confidence, last-polled time |

No user/session/auth tables exist in this phase — see [`adr/0003-no-auth-mvp.md`](adr/0003-no-auth-mvp.md).

## Frontend architecture

- `pages/SearchPage.tsx` and `pages/FlightDetailPage.tsx` are the two routes.
- `hooks/useFlightStatus.ts` and `hooks/useLiveTrack.ts` own polling: interval timing, pausing via the Page
  Visibility API when the tab is backgrounded, and stopping once a flight lands/cancels.
- `api/client.ts` is the only module that calls the backend; components never call `fetch` directly.
- The service worker (via `vite-plugin-pwa`) precaches the app shell for installability but explicitly does
  **not** cache `/api/*` responses for status/track — live data must never be served stale from the SW cache.

## Why these specific technology choices

See [`adr/0001-tech-stack.md`](adr/0001-tech-stack.md) and [`adr/0002-data-sources.md`](adr/0002-data-sources.md)
for the reasoning and alternatives considered.
