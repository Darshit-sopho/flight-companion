# Data Sources

## FlightAware AeroAPI

- **Used for**: flight identification, scheduled/estimated/actual times, delay, gate/terminal, flight status,
  past-occurrence history, airport reference info.
- **Not used for**: live position tracking (its `/track` endpoint exists but is deliberately excluded from any
  polling loop — see cost control below).
- **Auth**: API key in an `x-apikey` header (or per current AeroAPI docs), set via `AEROAPI_KEY` in `.env`.
- **Pricing model**: usage-based, billed per query (queries returning multiple pages are billed per
  15-result page). Personal tier: $5/month free credit, no monthly minimum, then pay-per-query.
- **Getting a key**: https://www.flightaware.com/commercial/aeroapi/ — sign up for the Personal tier.

## OpenSky Network

- **Used for**: live ADS-B position (lat/lon, altitude, ground speed, heading, on-ground flag) via
  `/states/all`, filterable by `icao24`. Also provides a downloadable aircraft database dump used to build the
  local `aircraft_registry` table (registration ↔ icao24).
- **Auth**: OAuth2 client-credentials grant for registered accounts (recommended — much better rate limits
  than anonymous use). Set `OPENSKY_CLIENT_ID` / `OPENSKY_CLIENT_SECRET` in `.env`.
- **Getting credentials**: free registration at https://opensky-network.org/my-opensky/account, create an API
  client under your account.
- **Rate limits**: registered accounts get a daily credit allowance (currently ~8000 credits/day); anonymous
  access is far more limited and only returns current-second-resolution data. The backend throttles its own
  call rate independent of this (`OPENSKY_MIN_POLL_INTERVAL_SECONDS`) so a burst of frontend polling can never
  translate into a burst of upstream calls.

## Why not FlightRadar24's API

FR24's consumer "Gold" subscription (a personal account tier for their app/website) does **not** include API
access — that's a separate commercial product (`fr24api.flightradar24.com`, plans starting at $9/mo). Since
OpenSky already provides free live position data sufficient for this project's map view, paying for FR24 API
access was judged unnecessary. See [`adr/0002-data-sources.md`](adr/0002-data-sources.md) for the full
reasoning, and reconsider only if OpenSky's ADS-B coverage proves insufficient for a specific route/region.

## Cost control

AeroAPI is the only paid dependency. Caching rules (implemented in the relevant `services/*.py` file, enforced
via `fetched_at`/`expires_at` columns on the caching tables):

| Data | Table | TTL / refresh rule |
|---|---|---|
| Flight identification/search result | `flight_snapshot` | Indefinite once the flight date has fully passed; ~15 min if today/future |
| Current status (times, gate, terminal, delay) | `flight_snapshot` | 5–15 min TTL, **and only refreshed while the flight is actively being viewed** (tracked via `last_viewed_at`) |
| Historical past-occurrence data | `flight_history_record` | Days to weeks; a fully-elapsed occurrence is cached forever |
| Airport reference info | `airport` | Effectively permanent; refreshed only via manual reseed |
| Live position | *(never cached from AeroAPI)* | Exclusively from OpenSky; polled at most once per `OPENSKY_MIN_POLL_INTERVAL_SECONDS` per flight |

A dev-time safety net (`backend/app/core/rate_limit.py`) tracks AeroAPI calls per day and warns/blocks past a
configurable `AEROAPI_DAILY_CALL_BUDGET` — this exists to catch bugs (e.g. an accidental polling loop) during
development, not as a production billing system.

## Fixture / offline mode

For tests and local development without spending real AeroAPI credit, the backend supports `FIXTURE_MODE=true`
(see [`TESTING.md`](TESTING.md)), which swaps both clients for canned responses recorded under
`backend/tests/fixtures/`. This is what the e2e suite runs against by default.
