# Flight Companion

A one-stop flight companion for travelers (and the people waiting for them): look up a flight and see its recent
on-time history, live position while it's in the air, and the trip details that actually matter — delays, gate,
terminal, and airport info. No account needed: search a flight number and date, get a shareable link, done. That
also makes it usable by family/friends who just want to watch a loved one's flight.

This is a personal/friends-and-family project, not a commercial product. It runs locally for now.

## Features (MVP)

- **Flight search** by flight number + date → a shareable detail page (`/flight/:ident/:date`).
- **Status card** — scheduled/estimated/actual times, delay, gate, terminal.
- **History & trend** — the same flight number's recent occurrences, on-time %, average delay.
- **Live map** — real-time position, altitude, speed, and heading while the flight is airborne.
- **Airport info** — name, city, timezone for departure/arrival airports.
- **Installable PWA** — add it to your phone's home screen, no app store required.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for what's intentionally deferred (ATC radio capture, accounts, push
notifications, native app).

## Architecture at a glance

```
frontend/   React + Vite + TypeScript PWA — talks only to the backend, never to third-party APIs directly
backend/    Python + FastAPI — owns API keys, caching, and the AeroAPI/OpenSky integration
docs/       Architecture, requirements, API reference, test plan, roadmap, ADRs
e2e/        Playwright end-to-end workflow tests spanning frontend + backend
```

Two external data sources power it:
- **FlightAware AeroAPI** — flight identification, schedule/status, delay, gate/terminal, and history.
- **OpenSky Network** — free, live ADS-B position data for the map view.

Full details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md).

## Quickstart

Prerequisites: Python 3.12+, Node 20+, Docker (for local Postgres).

```bash
# 1. Copy env template and fill in your AeroAPI key + OpenSky client credentials
cp .env.example .env

# 2. Start Postgres
docker compose up -d db

# 3. Backend
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 4. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

For subproject-specific details see [`backend/README.md`](backend/README.md) and
[`frontend/README.md`](frontend/README.md).

## Testing

Three layers: backend unit/integration tests (pytest), frontend unit tests (Vitest), and end-to-end workflow tests
(Playwright). Test strategy and how to run each layer is in [`docs/TESTING.md`](docs/TESTING.md).

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test

# End-to-end (starts backend in fixture mode + frontend automatically)
cd e2e && npm install && npx playwright test
```

## Contributing

New to the project? Start with [`CLAUDE.md`](CLAUDE.md) for a fast orientation (also directly usable as context
in a Claude Code session), then [`CONTRIBUTING.md`](CONTRIBUTING.md) for dev workflow and conventions.

## Docs index

| Doc | Purpose |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Fast orientation for an AI coding session or a new contributor |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Dev setup, branch/PR conventions, code style |
| [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) | Functional & non-functional requirements |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design, data flow, the AeroAPI↔OpenSky linking problem |
| [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) | AeroAPI/OpenSky specifics, cost control, credentials |
| [`docs/API.md`](docs/API.md) | REST endpoint reference |
| [`docs/TESTING.md`](docs/TESTING.md) | Test strategy across unit/integration/e2e |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | MVP vs near-term vs future phases |
| [`docs/adr/`](docs/adr/) | Architecture decision records |
