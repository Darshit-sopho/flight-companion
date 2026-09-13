# Backlog

A flat, unscheduled list of "not now but not forgotten" ideas raised while building a specific feature —
as distinct from [`ROADMAP.md`](ROADMAP.md), which is the small set of decided, sequenced, product-level
phases (MVP / near-term / Phase 2). This doc is the overflow list, not a second roadmap: when an item here
gets scheduled, move/link it into `ROADMAP.md` and delete it from here.

## From SC-D2 (airport weather glyph)

- Click-to-expand into a detailed/hourly weather view, beyond the compact Now/Outlook glyphs. The backend
  already caches a multi-day hourly forecast per airport, so this would mostly be new frontend UI, not new
  backend data.
- Day/night icon variants (Open-Meteo exposes an `is_day` field) — skipped in the initial weather-icon set
  to keep it small; revisit if it's missed in practice.

## From SC-D3 (shareable card image)

- Auto-generated OpenGraph `<meta property="og:image">` link previews, reusing the card-image render
  endpoint as the image source, so a flight link pasted (not clicked) into a chat app shows a rich preview
  automatically. This needs server-injected `<head>` content on what's currently a pure client-rendered
  SPA with no per-flight `<head>` — a bigger change than SC-D3 itself. The card image's dimensions were
  chosen up front to match the OpenGraph standard size, so this reuse won't need a resize/rework later.
- Icons (weather glyphs, gate/terminal icons) inside the generated share image — skipped in the first
  pass (the chosen image-rendering approach can't reuse the existing inline SVG icons without adding a
  new rendering dependency); text-only labels for v1.

## Live tracking gaps (found while manually testing SC-D2 against a real flight)

Tried a real flight (KLM248, KATL → EHAM) and its live map showed "Live tracking is unavailable" while
genuinely airborne. Root-caused (not a regression from this session's work — both pre-existing):

- **`aircraft_registry` was never actually populated.** The schema/resolver code for "registration ->
  icao24 via a locally-synced table" (`backend/app/services/icao24_resolver.py`,
  `backend/app/db/models.py`'s `AircraftRegistry`) exists, but the sync job that's supposed to populate it
  from OpenSky's public aircraft database dump was never implemented — the table is empty, so resolution
  always falls through to the noisier live-callsign fallback.
- **OpenSky has no oceanic coverage.** It's a crowdsourced ground-receiver network, so a transatlantic/
  transpacific flight goes dark for the ocean-crossing portion of the trip regardless of registry state —
  this specific flight was ~45% through a KATL->AMS crossing, i.e. likely mid-Atlantic.

**Future direction (explicitly wanted, not scoped yet)**: get closer to FR24-style continuous tracking,
including over oceans. FR24's own oceanic coverage comes from paid satellite ADS-B data (e.g. Aireon) —
free OpenSky fundamentally can't do this. Implementing the `aircraft_registry` sync would still be worth
doing on its own (more reliable resolution for ordinary domestic/coastal flights), but genuine
ocean-spanning coverage needs a different (likely paid) data source decision — no provider chosen, not
in scope until picked up as its own pass.

## Carried over from `docs/features/status-card.md` Phase F

- **SC-F1** (see [`status-card-requirements.md`](features/status-card-requirements.md) for the canonical
  requirement text — IDs are stable and not renumbered): show the viewer's own local time as a small
  annotation alongside airport-local times, on top of SC-B1/SC-B2. Deferred pending real demand from
  someone tracking a flight across timezones.
