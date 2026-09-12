# Contributing

## Getting set up

Follow the root [`README.md`](README.md) Quickstart. If you get stuck on backend setup specifically, see
[`backend/README.md`](backend/README.md); for frontend, [`frontend/README.md`](frontend/README.md).

You'll need your own FlightAware AeroAPI key and OpenSky Network OAuth client credentials (both free to obtain
for personal/low-volume use) — see [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) for how to get them.

## Branching & commits

- Branch off `main`: `feature/<short-description>` or `fix/<short-description>`.
- Small, focused commits. Write commit messages that explain *why*, not just what changed.
- Rebase on `main` before opening a PR rather than merging `main` in, when practical.

## Before opening a PR

Run the relevant test layers for what you touched:

```bash
# Touched backend/
cd backend && ruff check . && pytest

# Touched frontend/
cd frontend && npm run typecheck && npm run lint && npm test

# Touched both, or changed an API contract
cd e2e && npx playwright test
```

If you change a backend response shape, update:
1. The Pydantic schema in `backend/app/schemas/`.
2. `docs/API.md`.
3. The frontend's `frontend/src/api/client.ts` types and any component that consumes them.

## Code style

- **Backend**: type hints everywhere, `ruff` for linting/formatting (config in `backend/pyproject.toml`).
  Business logic belongs in `services/`, not in `routers/` — route handlers should be thin (parse request,
  call a service, return the response).
- **Frontend**: TypeScript strict mode, function components + hooks, no inline `fetch`/`axios` calls outside
  `api/client.ts`.
- Don't add comments that restate what the code does — only comment non-obvious *why* (see `CLAUDE.md`'s note
  on the icao24 resolver and cost-control logic for examples of things worth explaining).

## Adding a new external data field

If you're pulling something new from AeroAPI or OpenSky (e.g. airport weather):
1. Add it to the relevant `clients/*.py` wrapper first, with a unit test using a recorded/mocked fixture.
2. Decide its cache TTL in the owning service and document the reasoning in `docs/DATA_SOURCES.md`.
3. Extend the Pydantic schema, then the frontend type + component.

## Scope discipline

Check [`docs/ROADMAP.md`](docs/ROADMAP.md) before adding accounts, notifications, or ATC radio features — these
are intentionally deferred, not oversights. If you want to start on one, open an issue/discussion first so the
architecture implications (see the relevant ADR) get considered before code lands.

## Questions

If something in the docs is stale or wrong, fix the doc in the same PR as the code change that made it stale —
don't leave that for later.
