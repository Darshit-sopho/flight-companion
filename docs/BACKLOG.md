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

## Carried over from `docs/features/status-card.md` Phase F

- **SC-F1** (see [`status-card-requirements.md`](features/status-card-requirements.md) for the canonical
  requirement text — IDs are stable and not renumbered): show the viewer's own local time as a small
  annotation alongside airport-local times, on top of SC-B1/SC-B2. Deferred pending real demand from
  someone tracking a flight across timezones.
