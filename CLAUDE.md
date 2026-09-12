# CLAUDE.md

Orientation doc for an AI coding session (or a new human contributor) picking up this project. Read this first;
it links to the deeper docs instead of repeating them.

## What this project is

Flight Companion: a personal (non-commercial) web app for looking up a specific flight and seeing its recent
on-time history, live position while airborne, and trip details (delay/gate/terminal/airport). Lookup is by
flight number + date, no accounts — this is deliberate, see [`docs/adr/0003-no-auth-mvp.md`](docs/adr/0003-no-auth-mvp.md).
Full requirements: [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md).

## Stack

- **Frontend**: `frontend/` — React + Vite + TypeScript, built as an installable PWA.
- **Backend**: `backend/` — Python + FastAPI, SQLAlchemy + Alembic, Postgres.
- **E2E**: `e2e/` — Playwright, drives frontend + backend together.
- Full rationale for these choices: [`docs/adr/0001-tech-stack.md`](docs/adr/0001-tech-stack.md).

## The two things you must understand before touching backend code

1. **The AeroAPI ↔ OpenSky linking problem.** AeroAPI (flight schedule/status/history) and OpenSky (live ADS-B
   position) don't share an identifier. The same flight number flies a different tail number on different days,
   so the link between them can never be cached long-term — it's resolved fresh per flight instance. This logic
   lives entirely in `backend/app/services/icao24_resolver.py`. If live tracking is broken, start there.
   Full explanation: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#aeroapi--opensky-linking).

2. **AeroAPI is billed per query; OpenSky is free.** Anything that touches AeroAPI must go through the caching
   logic in `backend/app/services/flight_status_service.py` (TTL + "only refresh what's actively being viewed").
   Never add a code path that polls AeroAPI on a background timer — that's how the free-tier budget disappears.
   Live position must always come from `opensky_client.py`, never AeroAPI's `/track` endpoint. Details:
   [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md#cost-control).

## Where things live

```
backend/app/
  clients/       # raw HTTP wrappers for AeroAPI + OpenSky — no caching/business logic here
  services/       # all business logic, including caching decisions and the icao24 resolver
  routers/        # FastAPI route handlers — thin, delegate to services
  db/models.py    # SQLAlchemy models — the schema everything depends on
  schemas/        # Pydantic request/response DTOs (kept separate from ORM models)
  core/           # cache TTL helper, dev-time AeroAPI call-budget guard

frontend/src/
  pages/          # SearchPage, FlightDetailPage — route-level composition
  components/     # StatusTimelineCard, DelayTrendChart, LiveFlightMap, AirportInfoPanel, ShareLinkButton
  hooks/          # useFlightStatus, useLiveTrack — own the polling intervals + Page Visibility pause logic
  api/client.ts   # typed fetch wrappers matching backend schemas — the only place that calls the backend
```

The frontend never calls AeroAPI/OpenSky directly or holds API keys — only the backend does.

## Running it

See the root [`README.md`](README.md) Quickstart. Short version: `docker compose up -d db`, then run backend
(`uvicorn app.main:app --reload`) and frontend (`npm run dev`) in separate terminals.

## Testing conventions

Three layers, see [`docs/TESTING.md`](docs/TESTING.md) for the full strategy:
- `backend/tests/unit/` — mocked AeroAPI/OpenSky clients, no network, no DB. `icao24_resolver` tests are the
  highest-value tests in the repo — cover them first if you touch that file.
- `backend/tests/integration/` — FastAPI `TestClient` + a real (test) Postgres, HTTP clients still mocked.
- `e2e/tests/` — Playwright, runs frontend + backend with the backend in **fixture mode**
  (`FIXTURE_MODE=true`, see `docs/TESTING.md`) so tests don't spend real AeroAPI credit or depend on a flight
  actually being in the air.

Never write a test that calls the real AeroAPI or OpenSky APIs in the default test run — fixtures/mocks only.
The one exception is the manual smoke test described in `docs/TESTING.md`, which is intentionally not automated.

## Conventions

- Backend: type-annotated Python, Pydantic v2 schemas separate from SQLAlchemy models, service layer owns all
  business logic (routers stay thin), `ruff` for lint/format.
- Frontend: function components + hooks, TypeScript strict mode, no direct `fetch` calls outside `api/client.ts`.
- Commits/PRs: see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## What's deliberately not built yet

No user accounts, no push notifications, no ATC radio capture/playback, no native app wrapper. These are
real future phases (not rejected ideas) — see [`docs/ROADMAP.md`](docs/ROADMAP.md) before assuming a gap is a bug.
