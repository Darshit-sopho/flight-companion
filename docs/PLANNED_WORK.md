# Planned Work

Everything that's been thought of but isn't scheduled yet — as distinct from [`ROADMAP.md`](ROADMAP.md),
which is the small set of *decided, sequenced* product-level phases (MVP / near-term / Phase 2). This doc
is the working overflow list: bigger initiatives that need their own design pass before they're ready to
schedule, and smaller ideas/polish raised while building something else. When an item here gets scheduled,
move/link it into `ROADMAP.md` and delete it from here — this doc should only ever hold *unscheduled* work.

Keep it organized as it grows: a major initiative gets its own entry with enough context to pick back up
cold (why it matters, what it'd touch, open questions) — not just a one-liner. A minor item can stay a
one- or two-line bullet grouped under whatever prompted it.

## Major initiatives

Bigger efforts that need their own design/planning pass before they're scheduled — not small enough to
just pick up and do.

### Modularize into a real multi-page app

Right now `FlightDetailPage.tsx` composes everything (status card, live map, history chart, airport
panels, share actions) onto one long scrollable page. Idea: restructure into a proper multi-view app —
separate routes/screens for status, live tracking, history, airport details — so each can be visited
directly and developed independently, rather than every feature competing for space on one page.

**Why it matters**: this is explicitly what unlocks expanding the status card into a much more detailed
view (more fields, richer weather, expanded diverted-flight info, etc.) without it becoming an unusably
long single-page card — the detail lives on its own screen, and the main page keeps a minimal summary.

**Open questions, not yet decided**: what the minimal "summary" view should show vs. what moves to a
detail screen; whether this is client-side routing only (still one SPA, just more routes under
`/flight/:ident/:date/...`) or a deeper restructuring; how this interacts with the PWA app-shell caching
strategy (`docs/ARCHITECTURE.md`) and with the still-unbuilt OpenGraph link-preview idea below, which also
wants per-route `<head>` content.

### Flexible, FR24-style flight search

Today's search (`SearchPage.tsx` → `GET /api/flights/search?ident=&date=`) requires an exact, precise
flight number + date — no partial matches, no autocomplete, no searching by airline name or route. Idea:
support the kind of loose search FlightRadar24 offers (partial ident, airline name, maybe route/airport),
with suggestions as you type, rather than requiring the user to already know the exact ident.

**Why it matters**: this app is meant for casual/family use — someone tracking a relative's flight often
doesn't have the exact flight number memorized, just "mom's United flight to Chicago this afternoon" or
similar. Precise-match-only search is a real usability wall for that use case.

**Open questions, not yet decided**: what backend search capability this needs (AeroAPI's schedule search
endpoints may support some of this — needs investigation, not assumed), whether this needs a local
airline-name lookup table (similar precedent: `operator_names.py`), and how much of this is feasible
without new AeroAPI cost (search-as-you-type against a paid, per-query API needs its own cost-control
thinking, similar to `docs/DATA_SOURCES.md#cost-control`).

### `aircraft_registry` sync (more reliable live tracking)

Found while testing SC-D2 against a real flight (KLM248, KATL → EHAM): `aircraft_registry` (registration →
icao24, meant to be synced from OpenSky's public aircraft database dump) was never actually populated, so
icao24 resolution always falls through to the noisier live-callsign fallback
(`backend/app/services/icao24_resolver.py`). Implementing the actual sync job would make resolution
reliable for ordinary domestic/coastal flights instead of depending on OpenSky's live callsign feed every
time.

### Oceanic/continuous live tracking (FR24-style coverage)

Same investigation as above surfaced a separate, more fundamental gap: OpenSky is a crowdsourced
ground-receiver network with no coverage over open ocean, so a transatlantic/transpacific flight goes dark
for the ocean-crossing portion of the trip regardless of registry state (that KLM248 flight was ~45%
through its KATL→AMS crossing, i.e. likely mid-Atlantic, when tracking failed). Getting closer to FR24's
continuous coverage needs a satellite ADS-B data source (e.g. Aireon) — free OpenSky fundamentally can't
do this. No provider chosen; this needs its own cost/provider decision before it's scoped, and is
independent of the `aircraft_registry` fix above (that fix doesn't help mid-ocean, since there's no ADS-B
signal reaching any ground receiver at all out there).

## Smaller ideas / polish

### From SC-D2 (airport weather glyph)

- Click-to-expand into a detailed/hourly weather view, beyond the compact Now/Outlook glyphs. The backend
  already caches a multi-day hourly forecast per airport, so this would mostly be new frontend UI, not new
  backend data.
- Day/night icon variants (Open-Meteo exposes an `is_day` field) — skipped in the initial weather-icon set
  to keep it small; revisit if it's missed in practice.

### From SC-D3 (shareable card image)

- Auto-generated OpenGraph `<meta property="og:image">` link previews, reusing the card-image render
  endpoint as the image source, so a flight link pasted (not clicked) into a chat app shows a rich preview
  automatically. This needs server-injected `<head>` content on what's currently a pure client-rendered
  SPA with no per-flight `<head>` — a bigger change than SC-D3 itself, and shares the same "per-route head
  content" need as the modularization initiative above. The card image's dimensions were chosen up front to
  match the OpenGraph standard size, so this reuse won't need a resize/rework later.
- Icons (weather glyphs, gate/terminal icons) inside the generated share image — skipped in the first
  pass (the chosen image-rendering approach can't reuse the existing inline SVG icons without adding a
  new rendering dependency); text-only labels for v1.

### Carried over from `docs/features/status-card.md` Phase F

- **SC-F1** (see [`status-card-requirements.md`](features/status-card-requirements.md) for the canonical
  requirement text — IDs are stable and not renumbered): show the viewer's own local time as a small
  annotation alongside airport-local times, on top of SC-B1/SC-B2. Deferred pending real demand from
  someone tracking a flight across timezones.
