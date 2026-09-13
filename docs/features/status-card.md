# Status Card Improvements — Plan

Working doc for `feature/status-card-improvements`. This is a draft to edit, not a spec handed down —
trim, reorder, or add to it as you see fit. Each phase is meant to be a mergeable chunk of work on its
own, roughly in priority order, but they don't strictly depend on each other except where noted.

**Scope**: the top card on the flight detail page (`frontend/src/components/StatusTimelineCard.tsx`) —
ident, status, delay, the two-leg scheduled/estimated/actual/gate/terminal layout, aircraft line. Not the
live map, history chart, or airport panels (separate components, separate concerns).

## Current state (for reference)

Shows: ident + status badge, delay badge, per-leg (origin/destination) scheduled/estimated/actual times
and gate/terminal, and an aircraft registration/type line. Times are formatted with the *viewer's* browser
timezone (no explicit zone). Backend (`FlightStatusResponse`) currently exposes: times, delay_minutes,
gate/terminal, aircraft registration/type — nothing about flight progress, operator, cabin/baggage info,
or codeshare relationships, even though AeroAPI already returns a lot of this (see Phase C).

---

## Phase A — Visual polish + flight progress indicator

**Goal**: same information, presented better; the one new element is a progress bar/indicator, since
AeroAPI already gives us this for free.

- [ ] Add a progress bar (or similar visual) between the origin and destination legs, driven by AeroAPI's
      `progress_percent` field (0-100, not currently captured anywhere — needs `FlightSnapshot` column +
      `FlightStatusResponse` field + `upsert_snapshot_from_aeroapi` mapping on the backend first).
  - Open question: what should it show for `scheduled` (not yet departed, 0%) vs `landed` (100%) vs
    `cancelled`/`diverted` (hide it? show last-known %?) states.
- [ ] General layout/spacing/typography pass — this was built functionally-first, not designed.
- [ ] Icons for gate/terminal/delay instead of (or alongside) text labels, if that reads better at a
      glance than the current `dt`/`dd` list style.
- [ ] Re-examine the delay badge's color thresholds (currently: ≤15m ok, ≤45m warn, >45m bad) — still the
      right cutoffs?
- [ ] Mobile-width pass specifically for this card once the above lands (check at ~360-400px).

**Backend work**: `progress_percent` column + schema field + mapping (small, self-contained).
**Frontend work**: the component itself + `docs/API.md` + `frontend/src/api/client.ts` types updated to
match (see `CONTRIBUTING.md`'s rule on changing the API contract).

## Phase B — Time zone clarity

**Goal**: make it unambiguous which clock a displayed time is in, especially for someone checking a
flight from a third time zone (neither departure nor arrival).

- [ ] Decide the default: origin leg's times in the *origin airport's* local time, destination leg's
      times in the *destination airport's* local time (matches how airport departure boards actually
      display things) — vs. today's behavior (everything in the viewer's browser time).
  - This needs no backend change: `FlightDetailContent` already fetches both airports' `AirportResponse`
    (which includes `timezone`) in parallel with the status — just needs to pass each leg's timezone down
    into `StatusTimelineCard`, the same fix already applied to `AirportInfoPanel`
    (see `frontend/src/components/AirportInfoPanel.tsx` and its regression test for the pattern).
- [ ] Decide whether to *also* show the viewer's local time somewhere (e.g. a small "(your time: ...)"
      annotation), or keep it airport-local only with no toggle. A toggle is more flexible but is real
      added UI complexity for a feature most users may not need.
- [ ] Whatever's decided, label it explicitly (e.g. a small timezone abbreviation or UTC offset next to
      each time) so it's never ambiguous which clock is being shown.

**Backend work**: none expected.
**Frontend work**: `StatusTimelineCard.tsx`, `FlightDetailPage.tsx` (prop plumbing), tests.

## Phase C — Richer flight information

**Goal**: surface real AeroAPI fields we already pay for but don't show. Captured from a real response
during manual testing (UA3513/RPA3513) — field names as AeroAPI actually returns them:

| AeroAPI field | Idea | Notes |
|---|---|---|
| `operator`, `operator_icao`, `operator_iata` | "Operated by Republic Airways (RPA) as United Express" style line | We already resolve the *operating* ident internally for live-tracking (`operating_ident_icao`) — this is the natural place to also surface it to the user. Needs a small carrier-code → name lookup (static table, since AeroAPI doesn't hand us a friendly name directly) |
| `filed_ete` (seconds) | Flight duration, and/or a live countdown ("2h 14m to departure" / "1h 03m remaining") | `filed_ete` is the *filed* duration; a live remaining-time countdown would derive from `progress_percent` + `filed_ete`, or from now vs. `estimated_in` |
| `baggage_claim` | Baggage claim number at arrival | Often `null` in practice — needs a graceful "not yet assigned" state, same pattern as gate |
| `seats_cabin_business` / `_coach` / `_first` | Cabin configuration | Often `null`; low priority unless it turns out to be populated more often than our one sample flight |
| `route_distance` (a number, likely miles) | "651 mi" style trip-distance line | Cosmetic, cheap to add once `progress_percent` plumbing (Phase A) exists |
| `codeshares` / `codeshares_iata` | "Also sold as: AC4481, ..." | Nice-to-have; lower priority than the operator line above, which covers the main "why does this say a different airline" confusion |

- [ ] Pick which of the above are worth the backend plumbing (each needs: `FlightSnapshot` column(s) →
      `FlightStatusResponse` field(s) → `upsert_snapshot_from_aeroapi` mapping → frontend type + UI).
      Recommend starting with the operator/"operated by" line — it's the highest-value one and reuses
      data we already fetch for a different purpose.
- [ ] For any field that's frequently `null` in practice (baggage claim, cabin seats), decide the
      "not available" UX once, consistently, rather than per-field.

**Backend work**: schema + mapping changes per field chosen.
**Frontend work**: new sub-sections/lines in the card, new tests per field.

## Phase D — Further ideas / parking lot

Lower-confidence or more speculative ideas raised alongside the above — worth a look once A-C are done,
but not scoped in detail yet:

- [ ] Live countdown timer that ticks client-side between polls (e.g. "boards in 42m") rather than only
      updating on each `useFlightStatus` poll — cosmetic but makes the card feel more "alive."
- [ ] Small inline weather glyph per airport (already on the roadmap as a near-term item for the airport
      panels in `docs/ROADMAP.md` — if it lands there first, consider whether the status card should
      also show a compact version).
- [ ] A shareable "card" image/preview (e.g. for messaging apps) generated from this component's data —
      speculative, would need real demand before scoping further.
- [ ] Accessibility pass specifically for the delay/status badges (color alone currently carries meaning
      for the ok/warn/bad tones — should not rely on color alone).

---

## Notes for whoever picks this up

- Any change to `FlightStatusResponse` must update, together: `backend/app/schemas/flight.py`,
  `backend/app/services/flight_lookup_service.py` (the AeroAPI → snapshot mapping),
  `backend/app/db/models.py` (+ an Alembic migration if a new column), `docs/API.md`, and
  `frontend/src/api/client.ts` — see `CONTRIBUTING.md`.
- `map_status()` in `backend/app/services/utils.py` already has to cope with AeroAPI's real free-text
  compound status strings (e.g. `"En Route / On Time"`) — keep that in mind if any new field needs
  similar string-parsing (e.g. codeshare lists come as arrays, not free text, so should be simpler).
- Test each phase the same way the rest of the project is tested: backend unit tests for any new
  mapping/aggregation logic, frontend component tests for new UI states, and a manual check against a
  real flight (per `docs/TESTING.md`'s one manual smoke-test step) before merging.
