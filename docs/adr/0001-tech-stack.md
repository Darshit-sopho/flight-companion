# ADR 0001: Tech stack — React/Vite PWA + Python/FastAPI

## Status
Accepted

## Context
Building a flight companion app to share informally with friends/family, not a commercial product. Needed to
decide: native mobile app vs. web app, and what backend language to pair with it (with an eye toward a future
phase involving ATC radio capture/decoding).

## Decision
- **Frontend**: React + Vite + TypeScript, built as an installable PWA. Not a native app.
- **Backend**: Python + FastAPI.
- **Database**: Postgres.

## Rationale

**PWA over native app**: distributing to a handful of friends doesn't justify App Store review/TestFlight
overhead (Apple Developer account, 90-day TestFlight re-invites, separate iOS/Android builds). A PWA installs
from a URL, works cross-platform, and supports push notifications on both iOS (16.4+) and Android if that's
ever added. The tradeoff — weaker background tracking when the app is fully closed — was judged acceptable
for an MVP; a Capacitor/React Native wrapper remains an option later without a rewrite.

**Python backend over a Node/TypeScript backend**: the user explicitly wants to keep the door open for a
future phase capturing/decoding ATC radio communications (audio processing, potentially RTL-SDR hardware
integration, speech-to-text). Python has materially better tooling in that space than Node. FastAPI specifically
was chosen for its async support (useful for concurrent AeroAPI/OpenSky calls), Pydantic-based schema
validation (pairs naturally with typed frontend contracts), and low ceremony for a small project.

**Postgres**: relational data (flights, history, airports, aircraft registry) with clear foreign-key
relationships; no need for anything more exotic at this scale.

## Alternatives considered
- **React + Node/Express backend**: simpler single-language stack, but weaker fit for the future ATC-audio
  phase; rejected mainly for that reason.
- **Native app (Swift/Kotlin or React Native)**: rejected for MVP due to distribution overhead disproportionate
  to a friends-and-family tool; may be revisited later, see `docs/ROADMAP.md`.

## Consequences
- Two languages in the repo (TypeScript frontend, Python backend) — acceptable for a small project, but means
  contributors need both toolchains for full-stack changes.
- PWA background-tracking limitations mean live tracking effectively requires the tab/app to stay open/visible.
