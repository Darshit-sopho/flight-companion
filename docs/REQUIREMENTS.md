# Requirements

## Purpose

A personal, non-commercial flight companion tool. Primary user: the traveler themselves, wanting one place to
see everything relevant to a flight they're on. Secondary user: a family member/friend who wants to check on
someone else's flight without needing an account.

## Functional requirements

### FR1 — Flight lookup
- FR1.1: A user can look up a flight by flight number (IATA or ICAO ident) + date.
- FR1.2: A successful lookup produces a stable, shareable URL (`/flight/:ident/:date`) that anyone can open
  without logging in.
- FR1.3: An invalid/unknown flight number+date combination shows a clear "not found" state, not an error page.

### FR2 — Current status
- FR2.1: Show scheduled, estimated, and actual departure/arrival times.
- FR2.2: Show current delay (if any), in minutes, with a clear visual indicator.
- FR2.3: Show departure and arrival gate + terminal, when available.
- FR2.4: Show flight status (scheduled / active / landed / cancelled / diverted).
- FR2.5: If AeroAPI has no data for a field (e.g. gate not yet assigned), show "not yet available" rather than
  a blank or zero value.

### FR3 — History & trend
- FR3.1: Show the flight's past N (default 10) occurrences of the same flight number/route.
- FR3.2: Compute and display on-time percentage and average delay across that history.
- FR3.3: Indicate trend direction (improving/worsening/stable) over the shown history.
- FR3.4: Historical data for a fully-elapsed flight is treated as immutable once fetched.

### FR4 — Live tracking
- FR4.1: While a flight is airborne, show its live position (lat/lon), altitude, ground speed, and heading on
  a map.
- FR4.2: The map updates on a polling interval (target: every 10–15s) while the page is visible.
- FR4.3: Distinguish three states clearly in the UI: not yet airborne, currently tracked, and
  landed/tracking-ended — never show a stale position as if it were live.
- FR4.4: If the aircraft isn't broadcasting ADS-B (or resolution fails), show "live tracking unavailable for
  this aircraft" instead of an empty/broken map.

### FR5 — Airport info
- FR5.1: For both departure and arrival airports, show name, city, and local time (computed from timezone).

### FR6 — Sharing / family use case
- FR6.1: No login is required to look up or view any flight — this is how the "family watches a loved one's
  flight" case is satisfied for the MVP.
- FR6.2: A one-click "copy link" action for the current flight's detail page.

### FR7 — Installability
- FR7.1: The app is installable as a PWA on both iOS and Android (add to home screen), with a standalone
  display mode and an app icon.

## Non-functional requirements

- **NFR1 — Cost control**: The app must not make an AeroAPI call for data that's still within its cache TTL,
  and must not background-poll AeroAPI for flights nobody is currently viewing. See
  [`DATA_SOURCES.md`](DATA_SOURCES.md#cost-control).
- **NFR2 — No accounts in MVP**: No authentication, sessions, or user-specific storage in this phase (see
  [`adr/0003-no-auth-mvp.md`](adr/0003-no-auth-mvp.md)).
- **NFR3 — Local-first**: Must run entirely on a local machine (Docker Postgres + local backend/frontend dev
  servers) without requiring any cloud infrastructure.
- **NFR4 — Test coverage**: Core business logic (icao24 resolution, caching decisions, history aggregation)
  must have unit tests using mocked external APIs; the full workflow must have at least one end-to-end test.
  See [`TESTING.md`](TESTING.md).
- **NFR5 — Graceful degradation**: A failure or rate-limit from either external API must degrade a specific
  feature (e.g. live map) without breaking the rest of the page.
- **NFR6 — Mobile-first**: The UI must be fully usable at phone width, since that's the primary expected form
  factor (both for the traveler and for family checking from their phone).

## Out of scope for this phase

See [`ROADMAP.md`](ROADMAP.md) for the full phased breakdown. Explicitly out of scope right now: user accounts,
saved/favorited flights server-side, push notifications, ATC radio capture/playback/transcription, a native
mobile app, and any paid FlightRadar24 API usage.

## Success criteria for the MVP

- A real, currently-scheduled flight can be looked up and its detail page shows correct status/history.
- A currently-airborne real flight shows a moving position on the map within a couple of polling cycles.
- The app installs to a phone home screen and opens in standalone mode.
- All three test layers (unit, integration, e2e) pass without requiring real AeroAPI/OpenSky network calls.
