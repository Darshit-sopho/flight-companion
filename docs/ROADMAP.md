# Roadmap

## MVP (this build)

- Flight search by ident+date → shareable detail page.
- Status card: scheduled/estimated/actual times, delay, gate, terminal.
- History/trend: past-N occurrences, on-time %, average delay, trend direction.
- Live map via OpenSky, with resolved icao24 per flight instance.
- Airport reference panel (name/city/timezone).
- Installable PWA (manifest + app-shell service worker).
- Local dev setup: docker-compose Postgres + uvicorn + Vite dev server.
- Full test suite: backend unit + integration, frontend unit, e2e workflow.

## Near-term (still no accounts)

- Airport weather (e.g. via Open-Meteo, keyed by airport lat/lon) in `AirportInfoPanel`.
- A combined `/api/flights/{flight_id}/detail` endpoint to cut frontend round-trips (optimization, not a
  correctness fix — keep the split endpoints working either way).
- Client-side-only "recent searches" (localStorage, no backend change).
- Multiple-aircraft overlay for someone tracking connecting flights side by side.
- Visibility into AeroAPI call counts (even just a debug endpoint) for cost transparency during real use.

## Phase 2 — explicitly future, not started

These are real intentions, not rejected ideas — architecture decisions above try not to preclude them:

- **ATC radio capture/playback/transcription.** Likely shape: a new `services/atc_audio_service.py` pulling
  from LiveATC.net streams (and/or local RTL-SDR hardware decoding) keyed by airport + time window, with a new
  `atc_recording` table. Transcription (e.g. via Whisper) would layer on top of stored audio as a further
  sub-phase. Decoupled from flight tracking — an airport's ATC feed isn't flight-specific.
- **User accounts, saved trips, family dashboards with login.** Would introduce `users`/`sessions` tables and
  auth middleware, currently absent by design (see `adr/0003-no-auth-mvp.md`). Only worth doing if the
  no-login sharable-link model turns out to be insufficient in practice.
- **Push notifications** (delay/gate-change alerts). Needs a notification-subscription table and a background
  worker/scheduler — neither exists yet since nothing currently runs outside the request/response cycle.
- **Native app wrapper** (Capacitor or similar), if the PWA's background-tracking limitations ever become a
  real problem for how people actually use it.

## Explicitly rejected (for now)

- **Paying for the FlightRadar24 API.** Redundant with free OpenSky data for this project's live-tracking
  need; revisit only if OpenSky's ADS-B coverage proves insufficient for a specific route/region. See
  `adr/0002-data-sources.md`.
