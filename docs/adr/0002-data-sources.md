# ADR 0002: Data sources — AeroAPI + OpenSky, not FlightRadar24

## Status
Accepted

## Context
Three candidate flight-data sources were on the table: FlightAware AeroAPI (already have a key), FlightRadar24
(already have a consumer "Gold" subscription), and OpenSky Network (free, open ADS-B data). Needed a data
strategy covering: flight identification/status/delay/gate/history, and live position tracking.

## Decision
- **FlightAware AeroAPI** for flight identification, scheduled/estimated/actual times, delay, gate/terminal,
  status, and historical flight occurrences.
- **OpenSky Network** for live position (lat/lon/altitude/speed/heading) during the flight.
- **Not using FlightRadar24's API.**

## Rationale

**FR24 Gold ≠ FR24 API access.** This was the key discovery driving the decision: FlightRadar24's consumer
"Gold" subscription is a feature tier of their own app/website and does **not** include API access. Their API
is a separate commercial product (`fr24api.flightradar24.com`), with its own paid plans starting at $9/month
(Explorer tier: 30k credits, 30 days of history). Since the user's existing FR24 subscription grants nothing
usable here, adopting FR24 would mean a *new* paid commitment.

**OpenSky covers the live-tracking need for free.** OpenSky Network provides the same category of data
(ADS-B-derived position, altitude, speed, heading) FR24 would provide for live tracking, at no cost for
registered low-volume use. Since that's the only piece FR24 would have uniquely provided, paying for FR24 API
access became unnecessary.

**AeroAPI for everything schedule/status/history-related**, since OpenSky has no concept of gates, terminals,
delays, or scheduled times — that's airline/airport schedule data, not ADS-B telemetry. AeroAPI's Personal
tier ($5/month free credit, no minimum) comfortably covers a small friend group's casual usage if calls are
cached properly (see `docs/DATA_SOURCES.md#cost-control`).

**Splitting status (AeroAPI) from position (OpenSky) is also a cost-control decision**, not just a data-
availability one: AeroAPI's own `/track` endpoint could technically provide position data too, but polling it
every 10-15 seconds during a flight would burn through the free credit tier quickly since it's billed per
query. OpenSky's free tier is built for exactly this kind of frequent-polling use case.

## Alternatives considered
- **FR24 API (paid tier)**: rejected — redundant with free OpenSky for this project's needs; would only be
  worth reconsidering if OpenSky's coverage proves insufficient for a specific route/region in practice.
- **AeroAPI for live tracking too** (skip OpenSky entirely): rejected due to cost — frequent polling on a
  per-query-billed API doesn't fit a "casual, friends-and-family, free-tier-if-possible" budget.

## Consequences
- Two external HTTP dependencies instead of one, each with its own client wrapper, auth model (API key vs.
  OAuth2 client-credentials), and failure mode — both must degrade gracefully and independently (NFR5 in
  `docs/REQUIREMENTS.md`).
- The AeroAPI↔OpenSky identifier-linking problem (see `docs/ARCHITECTURE.md`) exists specifically because two
  separate providers are used instead of one; this is the direct cost of the cost savings.
