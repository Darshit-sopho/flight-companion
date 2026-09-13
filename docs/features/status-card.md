# Status Card Improvements — Plan

Working doc for `feature/status-card-improvements`. Reviewed once already — decisions below are marked
**Decided**; anything still open is marked **Open**. See `docs/features/status-card-requirements.md` for
the same scope written up as numbered requirements (SC-A1, SC-B1, ...) to implement/test against.

**Scope**: the top card on the flight detail page (`frontend/src/components/StatusTimelineCard.tsx`) —
ident, status, delay, the per-leg time/gate/terminal layout, aircraft line. Not the live map, history
chart, or airport panels (separate components, separate concerns) — though Phase E touches how airport
identity is displayed, which does overlap slightly with `AirportInfoPanel`.

**Priority ordering across phases** (traveler experience first): A → B → C → E → D. Phase F is explicitly
deferred — it's aimed at the family/friends-tracking use case, and the current push is improving the
webapp for the traveler first.

## Current state (for reference)

Shows: ident + status badge, delay badge, per-leg (origin/destination) scheduled/estimated/actual times
and gate/terminal, and an aircraft registration/type line. Times are formatted with the *viewer's* browser
timezone (no explicit zone). Airport identity is shown as whatever AeroAPI's generic `code` field returns
per leg — in practice this is the **ICAO** code (e.g. `KEWR`), not the IATA code travelers actually
recognize from boarding passes (`EWR`) — see Phase E. Backend (`FlightStatusResponse`) currently exposes:
times, delay_minutes, gate/terminal, aircraft registration/type — nothing about flight progress, operator,
duration, or airport identity/geo beyond the bare code.

---

## Phase A — Visual polish + flight progress indicator

- [x] **Implemented.** Add a progress bar between the origin and destination legs, driven by AeroAPI's
      `progress_percent` field (0-100, not currently captured — needs `FlightSnapshot` column +
      `FlightStatusResponse` field + `upsert_snapshot_from_aeroapi` mapping).
- [x] **Implemented.** Collapse the current three time rows (Scheduled/Estimated/Actual) to two:
      **Scheduled** and a second dynamic row that shows **Estimated** until the real value is known, then
      **swaps in place** to **Actual** once AeroAPI reports it (i.e. the row's *label* changes from
      "Estimated" to "Actual" the moment `actual_out`/`actual_in` is non-null — it's the same row, not an
      added third one).
- [x] **Implemented.** If the flight is `cancelled`, that dynamic row shows "Cancelled" instead of a time.
- [x] **Implemented.** If the flight is `diverted`: gray out the original destination column (its times/gate
      stay visible but visually muted), and add a **third column** showing the diverted-to destination's
      info (code/name, times, gate/terminal — same shape as a normal leg).
  - **Research resolved** (checked against a real diverted flight: EJA532, KIAD → KUNI, diverted to
    KCRW, 2026-09-13). AeroAPI does not mutate one record — it returns **two flight records sharing the
    same `fa_flight_id`**: one with `diverted: true`/`status: "Diverted"` whose `destination` is the
    *originally filed* airport (KUNI), and a separate one with `diverted: false`/`status: "Arrived"` whose
    `destination` is the *actual landing* airport (KCRW), with real `actual_off`/`actual_on` times.
    The catch: **searching by ident + date only ever returns the first (original/diverted) record** — the
    corrected "arrived at KCRW" record only appears when querying AeroAPI by that specific `fa_flight_id`.
    So implementing this needs a second AeroAPI call (by `fa_flight_id`) whenever `diverted: true` is
    seen, to fetch the actual-outcome record before the grayed-out-original + new-column UI can be
    populated. See `docs/features/status-card-requirements.md`'s SC-A4.3 for the full write-up, and
    SC-X3 for the fixture this needs before it's testable in CI.
- [x] **Implemented.** General layout/spacing/typography pass.
- [x] **Implemented.** Icons alongside the existing text labels (not replacing them) for gate/terminal/delay.
- [x] **Implemented.** Keep the current delay badge thresholds (≤15m ok, ≤45m warn, >45m bad).
- [x] **Implemented.** Mobile-width pass (~360-400px) once the above lands.

**Backend work**: `progress_percent` column + schema field + mapping.
**Frontend work**: the component, the Scheduled/dynamic-row time logic, the diverted 3-column layout,
`docs/API.md` + `frontend/src/api/client.ts` kept in sync (see `CONTRIBUTING.md`).

## Phase B — Time zone clarity

- [x] **Implemented.** Default: each leg's times shown in *that airport's own* local time (origin leg in
      origin's zone, destination leg in destination's zone) — matches how airport departure boards work.
      No backend change needed: `FlightDetailContent` already fetches both airports' `AirportResponse`
      (with `timezone`) alongside the status; pass each leg's timezone down into `StatusTimelineCard`,
      same fix already applied to `AirportInfoPanel` (see that component + its regression test for the
      pattern to reuse).
- [x] **Implemented.** Add a control (button/dropdown/segmented control — implementation detail, pick
      whatever fits the redesigned layout from Phase A) to switch the *whole card* to a single uniform
      timezone, with three selectable modes in addition to the default:
  - **Origin airport's timezone** for both legs (so destination time is shown converted into origin's zone).
  - **Destination airport's timezone** for both legs.
  - **UTC** for both legs.
  - Default stays **per-leg airport-local** (no override) unless the user picks one of the above.
- [x] **Implemented.** Whichever mode is active, label times explicitly (timezone abbreviation or UTC offset)
      so it's never ambiguous which clock is shown — matters more once multiple modes exist.
- [ ] **Deferred to Phase F** (not this phase): a small "(your time: ...)" viewer-local-time annotation.
      Wanted eventually, but it's aimed at the family/friends-tracking use case; traveler-facing work
      comes first.

**Backend work**: none expected.
**Frontend work**: `StatusTimelineCard.tsx`, a small timezone-mode selector component/control,
`FlightDetailPage.tsx` (prop plumbing), tests for all four display modes.

## Phase C — Richer flight information

**Decided fields** (see `docs/features/status-card-requirements.md` for exact field mapping):
- **Operator / "operated by"** line (e.g. "Operated by Republic Airways (RPA) as United Express"), from
  `operator` / `operator_icao` / `operator_iata`. Reuses the operating-ident concept already resolved
  internally for live-tracking (`operating_ident_icao`) — natural place to also surface it to the user.
  Needs a small carrier-code → friendly-name lookup table (AeroAPI doesn't hand us a display name).
- **Flight duration**, from `filed_ete` (seconds). Ties into Phase E's journey-duration ask and Phase D's
  live countdown — one piece of underlying data, several presentations (filed duration up front, a live
  remaining-time countdown once airborne).
- **Trip distance**, from `route_distance` (e.g. "651 mi").

**Explicitly skipped for now**: `baggage_claim`, `seats_cabin_business/coach/first`, `codeshares` /
`codeshares_iata`. Not worth the plumbing right now — revisit later if there's real demand.

**Backend work**: `FlightSnapshot` columns + `FlightStatusResponse` fields + mapping for the three
decided fields; a small static operator-code → name table.
**Frontend work**: new lines/sections in the card, tests per field.

## Phase E — Traveler-experience essentials (new, from review)

Raised in review as must-haves for the traveler-facing experience, ranked alongside A-C in priority.

- [x] **Implemented.** Show **estimated journey duration / flight time** on the card. Shares its underlying
      data with Phase C's `filed_ete` — implement together with that field; this item is the "make sure
      it's actually visible on the card, not buried" requirement.
- [x] **Implemented.** Airport identity should lead with the **common name and the code most travelers
      actually recognize** (the IATA code printed on boarding passes/departure boards, e.g. `EWR`, `BOS`,
      `DEL`) rather than the ICAO code we currently store and display (e.g. `KEWR`). Show IATA/ICAO
      codes secondarily (e.g. smaller text, a tooltip) where useful, not as the primary label.
  - **Implementation note**: AeroAPI's flight-status response already embeds `code_iata`, `code_icao`,
    `name`, and `city` directly on the `origin`/`destination` sub-objects in the *same* response we
    already fetch for status — we're currently only reading the generic `code` field (which resolves to
    ICAO) and discarding the rest. Capturing what's already in that response may mean this needs **no
    extra AeroAPI call** at all (cost-control win, not just a display fix) - only worth confirming this
    holds for both scheduled and elapsed flights before relying on it exclusively instead of the separate
    `/airports/{code}` lookup.
- [x] **Implemented.** Provide a map link (Google Maps / Apple Maps - platform-appropriate, or a generic maps
      search URL that both can open) for departure and arrival, one per leg. Link to the specific
      terminal when known, else fall back to the airport itself.
  - **Implementation note**: we have airport lat/lon (`Airport.lat`/`lon`), but not terminal-level
    geocoordinates from any source currently in use - "link to the terminal" in practice means a
    *text-based* maps search query (e.g. "Terminal C, Newark Liberty International Airport"), not a
    precise terminal pin. Good enough for "get me there," not a precision requirement.

**Backend work**: capture IATA code (and ideally name/city, replacing or supplementing the separate
airport lookup - see implementation note above) in the flight-status mapping.
**Frontend work**: airport identity display change (also touches `AirportInfoPanel` for consistency), a
"open in maps" link/icon per leg.

## Phase D — Further polish (all approved)

- [x] **Implemented.** Live countdown timer that ticks client-side between polls (e.g. "boards in 42m"),
      rather than only updating on each `useFlightStatus` poll.
- [ ] **Decided, not yet implemented.** Small **inline/compact** weather glyph per airport for now; a
      later click-to-expand into a more detailed weather view is a good follow-on idea but not in scope
      yet. **Deferred**: needs a weather API provider chosen first (none picked yet) — separate
      implementation pass.
- [ ] **Decided, not yet implemented.** A shareable "card" image/preview (e.g. for messaging apps)
      generated from this component's data. **Deferred**: needs an image-generation approach chosen
      first — separate implementation pass.
- [x] **Implemented.** Accessibility pass on the delay/status badges — the delay badge already pairs an
      icon with an explicit text label ("On time (5m)" / "Delayed 60m"), so tone is never color-only.

## Phase F — Deferred (family/friends-tracking focus, not now)

Moved to [`docs/BACKLOG.md`](../BACKLOG.md). The requirement itself stays canonical (SC-F1) in
`docs/features/status-card-requirements.md` — IDs are never renumbered.

---

## Notes for whoever picks this up

- Any change to `FlightStatusResponse` must update, together: `backend/app/schemas/flight.py`,
  `backend/app/services/flight_lookup_service.py` (the AeroAPI → snapshot mapping),
  `backend/app/db/models.py` (+ an Alembic migration if a new column), `docs/API.md`, and
  `frontend/src/api/client.ts` — see `CONTRIBUTING.md`.
- `map_status()` in `backend/app/services/utils.py` already has to cope with AeroAPI's real free-text
  compound status strings (e.g. `"En Route / On Time"`) — keep that in mind if any new field needs
  similar string-parsing.
- Test each phase the same way the rest of the project is tested: backend unit tests for any new
  mapping/aggregation logic, frontend component tests for new UI states, and a manual check against a
  real flight (per `docs/TESTING.md`'s one manual smoke-test step) before merging. Phase A's diverted-flight
  handling now has a real confirmed AeroAPI response shape to build a fixture from (see the Phase A
  diverted-flight note above and SC-X3) — build that fixture as part of implementing SC-A4, don't leave
  it manual-only now that the shape is known.
