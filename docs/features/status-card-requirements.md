# Status Card — Requirements

Numbered requirements for the `feature/status-card-improvements` work, derived from the reviewed plan in
`docs/features/status-card.md` (read that first for rationale/context — this doc is the traceable,
testable checklist version). IDs are stable once assigned: don't renumber, mark superseded requirements
as such instead.

Scope: `frontend/src/components/StatusTimelineCard.tsx` and the backend fields it depends on. Same
out-of-scope boundary as the plan doc — live map, history chart, and airport panels are separate, except
where a requirement below explicitly touches shared airport-identity display.

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
  - **SC-A4.3 (blocked on research)**: Before A4.1/A4.2 can be implemented, confirm what AeroAPI actually
    returns for a diverted flight — whether the original destination remains available alongside a new
    diversion airport, or whether `destination` simply mutates and the original is lost. Requires a real
    diverted-flight sample or AeroAPI documentation; not verifiable from fixture data alone.
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
  a detailed weather view is a candidate follow-up, not part of this requirement.
- **SC-D3**: The product MUST support generating a shareable "card" image/preview from this component's
  data (e.g. for sharing into messaging apps).
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
  (`backend/app/clients/fixtures.py` has no diverted-flight scenario) — either extend the fixtures with a
  diverted case once SC-A4.3's research is resolved, or treat it as manual-verification-only.
