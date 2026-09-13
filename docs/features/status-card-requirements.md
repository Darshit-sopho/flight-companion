# Status Card — Requirements

Numbered requirements for the `feature/status-card-improvements` work, derived from the reviewed plan in
`docs/features/status-card.md` (read that first for rationale/context — this doc is the traceable,
testable checklist version). IDs are stable once assigned: don't renumber, mark superseded requirements
as such instead.

Scope: `frontend/src/components/StatusTimelineCard.tsx` and the backend fields it depends on. Same
out-of-scope boundary as the plan doc — live map, history chart, and airport panels are separate, except
where a requirement below explicitly touches shared airport-identity display.

**Implementation status**: SC-A1 through SC-A7, SC-B1 through SC-B3, SC-C1 through SC-C3, SC-E1 through
SC-E3, SC-X1 through SC-X3, SC-D1, and SC-D4 are all **implemented and tested** (see
`backend/tests/unit/test_aeroapi_client.py`, `test_flight_lookup_service.py`, `test_operator_names.py`,
`backend/tests/integration/test_flights_api.py`, and `frontend/tests/components/StatusTimelineCard.test.tsx`).
**SC-D2** (weather glyph, via Open-Meteo) is now **implemented and tested** (see
`backend/tests/unit/test_openmeteo_client.py`, `test_wmo_weather_codes.py`, `test_weather_service.py`,
`backend/tests/integration/test_airports_api.py`, and `StatusTimelineCard.test.tsx`'s "weather glyphs"
tests). **SC-D3** (shareable card image, server-side PNG via Pillow) is now **implemented and tested**
too (see `backend/tests/unit/test_card_image_service.py`, `test_flights_api.py`'s card-image tests, and
`frontend/tests/components/ShareImageButton.test.tsx`) — scoped to casual share-to-chat only; the
OpenGraph link-preview reuse (SC-D3.2) remains deferred per `docs/BACKLOG.md`.

## Phase A — Visual polish + progress indicator

- **SC-A1**: The card MUST show a visual progress indicator (e.g. a progress bar) positioned between the
  origin and destination legs, reflecting AeroAPI's `progress_percent` (0-100).
  - **SC-A1.1**: For `status = scheduled`, the indicator MUST show 0% (or be visually indicated as "not
    started"), not a stale/undefined value.
  - **SC-A1.2**: For `status = landed`, the indicator MUST show 100%.
  - **SC-A1.3**: For `status = cancelled` or `status = diverted`, the indicator's display state is an
    open question — resolve during implementation (candidates: hide it, or show last-known percent with
    a visual "interrupted" treatment).
- **SC-A2**: The card MUST show exactly two time rows per leg: **Scheduled**, and a second row that
  displays **Estimated** until AeroAPI reports an actual time, then displays **Actual** in its place (same
  row, label and value both update — not an added third row). The previous three-row
  Scheduled/Estimated/Actual layout is replaced by this.
- **SC-A3**: If `status = cancelled`, the second (dynamic) row MUST show "Cancelled" instead of a time.
- **SC-A4**: If `status = diverted`:
  - **SC-A4.1**: The original destination column MUST remain visible but visually de-emphasized (e.g.
    grayed out) rather than removed.
  - **SC-A4.2**: A third column MUST be added showing the diverted-to destination's info (code/name,
    times, gate/terminal), in the same shape as a normal leg column.
  - **SC-A4.3 (RESOLVED — see finding below)**: Confirmed against a real diverted flight
    (EJA532, KIAD → KUNI, diverted to KCRW, 2026-09-13). AeroAPI does **not** mutate a single record in
    place; it produces **two separate flight records that share the same `fa_flight_id`**:
    - One with `diverted: true, cancelled: true, status: "Diverted"`, `destination` = the
      **originally filed** airport (KUNI), `actual_off`/`actual_on` = null.
    - One with `diverted: false, cancelled: false, status: "Arrived"`, `destination` = the
      **actual landing** airport (KCRW), `actual_off`/`actual_on` populated with real times.

    Critically, **searching by ident + date only surfaces the first (original/diverted) record** — the
    corrected "Arrived at KCRW" record is only returned when querying `/flights/{fa_flight_id}` with the
    *specific* `fa_flight_id` (obtained from the first record). This changes SC-A4's implementation
    shape: on detecting `diverted: true` from the normal ident+date lookup, the backend must issue a
    **second AeroAPI call** keyed on that flight's `fa_flight_id` to retrieve the actual-outcome record
    before SC-A4.1/SC-A4.2 can be populated correctly. This needs its own `AeroAPIClient` method (e.g.
    `get_flight_by_id(fa_flight_id)`) and is an extra cost-control consideration for
    `docs/DATA_SOURCES.md` — but only triggers for the rare diverted case, not on every lookup.
- **SC-A5**: Gate, terminal, and delay MUST each have an icon shown alongside their existing text label
  (icons supplement, not replace, the text).
- **SC-A6**: The delay badge thresholds remain: on-time/ok for delay ≤ 15 minutes, warn for ≤ 45 minutes,
  bad for > 45 minutes. (Unchanged from current behavior — recorded here so a future change is a
  deliberate diff against a stated requirement, not a silent drift.)
- **SC-A7**: The card MUST remain fully usable at ~360-400px viewport width after the Phase A redesign
  (no horizontal overflow, no truncated/overlapping content).

## Phase B — Time zone clarity

- **SC-B1**: By default, each leg's times MUST be displayed in that leg's own airport's local timezone
  (origin times in the origin airport's zone, destination times in the destination airport's zone).
- **SC-B2**: The card MUST provide a control to override the display to a single uniform timezone for
  both legs, with the following selectable modes:
  - **SC-B2.1**: Origin airport's timezone (applied to both legs).
  - **SC-B2.2**: Destination airport's timezone (applied to both legs).
  - **SC-B2.3**: UTC (applied to both legs).
  - **SC-B2.4**: The default (no override) MUST be per-leg airport-local time (SC-B1), selectable again
    from whichever override mode is active.
- **SC-B3**: Every displayed time MUST carry an explicit timezone indicator (abbreviation or UTC offset)
  so the active mode is never ambiguous.
- **Deferred — SC-F1** (see Phase F below): showing the viewer's own local time is explicitly out of
  scope for this phase.

## Phase C — Richer flight information

- **SC-C1**: The card MUST show an "operated by" line when the operating carrier differs from (or adds
  useful context to) the marketing ident, derived from AeroAPI's `operator` / `operator_icao` /
  `operator_iata`, resolved to a friendly airline name via a small static lookup table (AeroAPI does not
  provide a display name for the operator directly).
- **SC-C2**: The card MUST show the flight's duration, derived from AeroAPI's `filed_ete` (filed estimated
  time en route, in seconds). This is the same underlying data point used by SC-E1 (visible placement) and
  SC-D1 (live countdown) — implement the field once, present it in each of those places.
- **SC-C3**: The card MUST show the trip distance, derived from AeroAPI's `route_distance`.
- **Out of scope (explicitly skipped, not deferred)**: `baggage_claim`, `seats_cabin_business` /
  `_coach` / `_first`, `codeshares` / `codeshares_iata`. Not worth the backend plumbing right now; revisit
  only if real demand shows up later.

## Phase E — Traveler-experience essentials

- **SC-E1**: The card MUST display the flight's estimated journey duration (see SC-C2) in a visible,
  non-buried location on the card (not just implemented in the backend and never surfaced).
- **SC-E2**: Airport identity on the card MUST lead with the airport's common name and/or the IATA code
  travelers actually recognize (e.g. the code printed on a boarding pass — `EWR`, `BOS`, `DEL`), not the
  ICAO code (e.g. `KEWR`) currently shown.
  - **SC-E2.1**: ICAO (and/or IATA, if not already primary) codes MAY still be shown secondarily (smaller
    text, tooltip, etc.) where useful, but must not be the primary/most prominent label.
  - **SC-E2.2 (implementation note, not a behavioral requirement)**: AeroAPI's flight-status response
    already embeds `code_iata`, `code_icao`, `name`, and `city` on the `origin`/`destination` sub-objects
    of the *same response* already fetched for status — capturing these may satisfy SC-E2 without an
    additional AeroAPI call. Confirm this holds for both scheduled and fully-elapsed flights before
    depending on it exclusively in place of the existing `/airports/{code}` lookup.
- **SC-E3**: The card MUST provide a map link (Google Maps, Apple Maps, or a platform-generic maps search
  URL) for both the departure and arrival airport.
  - **SC-E3.1**: When a terminal is known for that leg, the link SHOULD target that terminal specifically
    (in practice: a text-based maps search query naming the terminal and airport, not a precise geocoded
    terminal pin — no terminal-level coordinate data is available).
  - **SC-E3.2**: When no terminal is known, the link MUST still be provided, targeting the airport itself.

## Phase D — Further polish

- **SC-D1**: The card MUST show a live, client-side-ticking countdown (e.g. "boards in 42m" /
  time-remaining-in-flight) that updates between `useFlightStatus` polls, not only on each poll.
- **SC-D2**: The card MUST show a compact/inline weather glyph per airport. A future click-to-expand into
  a detailed weather view is a candidate follow-up, not part of this requirement (tracked in
  `docs/BACKLOG.md`).
  - **SC-D2.1 (RESOLVED)**: A "Now" glyph shows current conditions at that airport (icon + °F), sourced
    from Open-Meteo and shown regardless of flight status — it's airport weather, not flight weather, so
    it stays useful context even for a landed/cancelled flight.
  - **SC-D2.2 (RESOLVED)**: A second glyph, visibly labeled **"At departure"** (origin leg) or **"At
    arrival"** (destination/diverted leg) — not a vague "Outlook" — shows the forecast for the hour
    nearest that leg's scheduled/estimated time. The label must be visible text on the card, not only a
    hover tooltip, since a bare icon+temp pair gives no clue what it represents. Omitted when no cached
    forecast hour falls within ~3 hours of that target (e.g. a flight booked beyond Open-Meteo's forecast
    horizon) rather than showing a misleadingly stale match.
  - **SC-D2.3 (implementation note)**: Open-Meteo's ~30 WMO weather codes are bucketed server-side
    (`backend/app/services/wmo_weather_codes.py`) into 7 icon buckets before reaching the frontend, so the
    frontend never needs its own copy of that table.
- **SC-D3**: The product MUST support generating a shareable "card" image/preview from this component's
  data (e.g. for sharing into messaging apps).
  - **SC-D3.1 (RESOLVED)**: Server-side PNG rendering via Pillow (`backend/app/services/
    card_image_service.py`), scoped to casual share-to-chat only for this pass — a from-scratch draw of
    the flight's key fields at 1200x630, not a screenshot of the web card. Served from
    `GET /api/flights/{flight_id}/card.png`, reusing the same cached `FlightSnapshot` the JSON status
    endpoint already serves; introduces no new external call or cache.
  - **SC-D3.2 (implementation note)**: Reusing the render endpoint for an auto-generated OpenGraph
    link-preview image is deferred to `docs/BACKLOG.md`, not part of this requirement.
- **SC-D4**: The delay/status badges MUST convey their meaning (ok/warn/bad) through a non-color signal
  in addition to color (icon, shape, or text), so the distinction isn't color-only.

## Phase F — Deferred (family/friends-tracking focus)

Not in scope for the current pass; the current priority is the traveler-facing experience.

- **SC-F1 (deferred)**: Show the viewer's own local time as a small annotation alongside airport-local
  times (built on top of SC-B1/SC-B2). Revisit after Phases A, B, C, E, and D are complete.

## Cross-cutting implementation requirements

- **SC-X1**: Any new backend-sourced field introduced by the requirements above MUST update, together:
  `backend/app/db/models.py` (+ Alembic migration if a new column), `backend/app/schemas/flight.py`,
  `backend/app/services/flight_lookup_service.py` (AeroAPI → snapshot mapping), `docs/API.md`, and
  `frontend/src/api/client.ts` — per `CONTRIBUTING.md`.
- **SC-X2**: Each requirement above needs test coverage appropriate to its layer before being considered
  done: backend unit tests for new mapping/aggregation logic, frontend component tests for new UI states
  (including the diverted 3-column layout, each of the four Phase B display modes, and both "estimated"
  and "actual" states of the SC-A2 dynamic row), and one manual check against a real flight per
  `docs/TESTING.md`.
- **SC-X3**: SC-A4 (diverted-flight handling) cannot be verified against the existing fixture data
  (`backend/app/clients/fixtures.py` has no diverted-flight scenario). Now that SC-A4.3 is resolved, add a
  third fixture ident (e.g. `FIX300`) whose `get_flight` returns the two-record diverted/arrived pair
  matching the shape confirmed in SC-A4.3 (real example on file: EJA532, KIAD → KUNI, diverted to KCRW,
  2026-09-13) — including a `FixtureAeroAPIClient.get_flight_by_id` counterpart once that method exists
  (see SC-A4.3) — so this path has real unit/e2e coverage, not manual-only.
- **SC-X4 (RESOLVED)**: A new, independently-cached external data source that is NOT derived from
  AeroAPI's flight-status payload (e.g. SC-D2's weather, from Open-Meteo) gets its own table + service +
  TTL — never columns bolted onto `FlightSnapshot`, and does not go through the SC-X1 AeroAPI→snapshot
  mapping. This is why SC-D2's implementation touches neither `FlightSnapshot`,
  `flight_lookup_service.py`, nor `AirportRef`/`FlightStatusResponse`: it has its own freshness policy
  (30 min TTL, no `last_viewed_at` gating) on a completely separate, free API, and coupling it to
  AeroAPI's paid, gated cache would let a slow/down third-party API affect the core status fetch.
