# Frontend

React + Vite + TypeScript PWA. Talks only to the backend (`../backend`) — never directly to AeroAPI or
OpenSky, and never holds API keys. See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md#frontend-architecture).

## Setup

```bash
npm install
npm run dev
```

Requires the backend running at `http://localhost:8000` (the dev server proxies `/api` there — see
`vite.config.ts`). See [`../backend/README.md`](../backend/README.md), or set `FIXTURE_MODE=true` on the
backend to explore the UI without real API keys — try flight `FIX100` (airborne) or `FIX200` (landed) for
any date.

## Layout

```
src/
  pages/       SearchPage, FlightDetailPage — the two routes
  components/  StatusTimelineCard, DelayTrendChart, LiveFlightMap, AirportInfoPanel, ShareLinkButton
  hooks/       useFlightStatus, useLiveTrack — own polling intervals + Page Visibility pausing
  api/client.ts  typed fetch wrappers — the only module that calls the backend
```

## Tests

```bash
npm test         # Vitest + React Testing Library, see ../docs/TESTING.md
npm run typecheck
npm run lint
```

## Building

```bash
npm run build     # tsc -b && vite build, output in dist/
npm run preview   # serve the production build locally
```

## PWA notes

`vite-plugin-pwa` generates the manifest and service worker from `vite.config.ts`. The service worker is
configured to never cache `/api/*` responses (status/track data must always be live) — see
`docs/ARCHITECTURE.md` for why. Icons in `public/icons/` are solid-color placeholders; swap them for real
branding before sharing the installed app more widely.
