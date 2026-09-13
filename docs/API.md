# API Reference

Base URL (local dev): `http://localhost:8000`. All responses are JSON. No authentication — see
[`adr/0003-no-auth-mvp.md`](adr/0003-no-auth-mvp.md).

## `GET /api/flights/search`

Resolve a flight number + date to an internal flight ID.

**Query params**
| Param | Type | Required | Notes |
|---|---|---|---|
| `ident` | string | yes | Flight number, IATA or ICAO form (e.g. `UA123` or `UAL123`) |
| `date` | string | yes | ISO date, `YYYY-MM-DD`, the scheduled departure date local to the origin |

**Response `200`**
```json
{
  "flight_id": "UAL123-2026-09-12",
  "ident": "UAL123",
  "origin": "SFO",
  "destination": "ORD",
  "scheduled_departure": "2026-09-12T14:30:00-07:00"
}
```

**Response `404`** — no matching flight found for that ident/date.

## `GET /api/flights/{flight_id}`

Full current status.

**Response `200`**
```json
{
  "flight_id": "UAL123-2026-09-12",
  "ident": "UAL123",
  "status": "active",
  "origin": {
    "code": "KSFO", "iata": "SFO", "name": "San Francisco International Airport",
    "city": "San Francisco", "timezone": "America/Los_Angeles", "gate": "A12", "terminal": "2"
  },
  "destination": {
    "code": "KORD", "iata": "ORD", "name": "O'Hare International Airport",
    "city": "Chicago", "timezone": "America/Chicago", "gate": null, "terminal": "1"
  },
  "scheduled_departure": "2026-09-12T14:30:00-07:00",
  "estimated_departure": "2026-09-12T14:45:00-07:00",
  "actual_departure": "2026-09-12T14:47:00-07:00",
  "scheduled_arrival": "2026-09-12T20:10:00-05:00",
  "estimated_arrival": "2026-09-12T20:22:00-05:00",
  "actual_arrival": null,
  "delay_minutes": 12,
  "aircraft": { "registration": "N12345", "type": "B738" },
  "operator": { "icao": "RPA", "iata": "YX", "name": "Republic Airways" },
  "progress_percent": 42,
  "flight_duration_minutes": 330,
  "route_distance": 1846,
  "diverted": null
}
```

`status` is one of `scheduled | active | landed | cancelled | diverted`. Any field AeroAPI hasn't populated
yet (e.g. `actual_arrival` before landing) is `null` — the frontend renders this as "not yet available," not
as an error.

`origin`/`destination`'s `code` is the ICAO code (e.g. `KSFO`); `iata` is the code travelers actually
recognize (e.g. `SFO`) — see `docs/features/status-card-requirements.md#SC-E2` for why both are exposed.
Both stay as the **originally filed** route even if the flight diverts — see `diverted` below.

`operator` is `null` when AeroAPI doesn't report an operator code for this flight; `operator.name` is
`null` when the code isn't in the small static lookup table (`app/services/operator_names.py`) — always
show `operator.icao`/`operator.iata` as a fallback in that case.

`progress_percent`, `flight_duration_minutes` (derived from AeroAPI's `filed_ete`), and `route_distance`
are `null` when AeroAPI doesn't report them (uncommon, but happens for some flight types).

`diverted` is `null` unless `status = "diverted"`, in which case it holds the **actual** landing airport
(distinct from `destination` above, which stays the original plan) plus that airport's arrival times:
```json
{
  "airport": {
    "code": "KCRW", "iata": "CRW", "name": "West Virginia Intl Yeager",
    "city": "Charleston", "timezone": "America/New_York", "gate": "D4", "terminal": null
  },
  "scheduled_arrival": null,
  "estimated_arrival": null,
  "actual_arrival": "2026-09-13T01:31:45Z"
}
```
This requires a second AeroAPI call the backend makes automatically when it detects `diverted: true` —
see `docs/features/status-card-requirements.md#SC-A4.3` for why a single call can't return this.

## `GET /api/flights/{flight_id}/history`

Past occurrences of the same flight number/route.

**Query params**
| Param | Type | Required | Notes |
|---|---|---|---|
| `limit` | integer | no | Number of past occurrences to return, default 10 |

**Response `200`**
```json
{
  "flight_id": "UAL123-2026-09-12",
  "on_time_percentage": 80.0,
  "average_delay_minutes": 14.5,
  "trend": "improving",
  "occurrences": [
    { "date": "2026-09-05", "delay_minutes": 5, "on_time": true },
    { "date": "2026-08-29", "delay_minutes": 32, "on_time": false }
  ]
}
```

`trend` is one of `improving | worsening | stable`, computed by comparing the first and second half of the
returned occurrence window.

## `GET /api/flights/{flight_id}/card.png`

Shareable "card" image for casual sharing into a chat app (docs/features/status-card-requirements.md
#SC-D3). A from-scratch server-side rendering of the flight's key fields — ident, status, route, times,
delay, gate/terminal, operator, duration/distance, aircraft — NOT a screenshot of the web card. Uses the
same cached `FlightSnapshot` the JSON status endpoint serves, so it introduces no new external API call
and no new cache.

**Response `200`**: `image/png`, 1200x630 (the OpenGraph standard size, chosen so a future auto-generated
link-preview image — see `docs/PLANNED_WORK.md` — can reuse this endpoint without a resize).

**Response `404`** — unknown `flight_id`.

## `GET /api/flights/{flight_id}/track`

Latest live position, if available.

**Response `200` (airborne, tracked)**
```json
{
  "state": "tracking",
  "position": {
    "lat": 41.9786,
    "lon": -87.9048,
    "altitude_ft": 34000,
    "ground_speed_kt": 480,
    "heading_deg": 92,
    "on_ground": false,
    "recorded_at": "2026-09-12T15:02:10Z"
  },
  "resolution": { "method": "registration_lookup", "confidence": "high" }
}
```

**Response `200` (not yet airborne / landed / unresolved)**
```json
{ "state": "not_airborne", "position": null, "resolution": null }
```

`state` is one of `tracking | not_airborne | landed | unavailable`. The frontend must render each of these as
a distinct UI state — never fall back to showing a stale `position` as if it were current.

## `GET /api/airports/{code}`

**Path params**: `code` — IATA or ICAO airport code.

**Response `200`**
```json
{
  "code": "SFO",
  "name": "San Francisco International Airport",
  "city": "San Francisco",
  "country": "US",
  "timezone": "America/Los_Angeles",
  "local_time": "2026-09-12T14:30:00-07:00"
}
```

## `GET /api/airports/{code}/weather`

Compact weather glyph data for one airport (docs/features/status-card-requirements.md#SC-D2) — "now"
(current conditions) plus an "outlook" (forecast for the hour nearest a target time, e.g. a leg's
scheduled/estimated departure or arrival). Sourced from Open-Meteo (free, no key) — see
`docs/DATA_SOURCES.md#open-meteo`.

**Path params**: `code` — IATA or ICAO airport code.

**Query params**
| Param | Type | Required | Notes |
|---|---|---|---|
| `at` | ISO 8601 datetime | no | Target time for the `outlook` glyph. Defaults to now. |

**Response `200`**
```json
{
  "code": "SFO",
  "now": { "bucket": "partly_cloudy", "temp_f": 68.0, "at": "2026-09-12T14:05:00Z" },
  "outlook": { "bucket": "rain", "temp_f": 55.0, "at": "2026-09-12T20:00:00Z" }
}
```

`bucket` is one of `clear | partly_cloudy | overcast | fog | rain | snow | thunderstorm | null` (mapped
server-side from Open-Meteo's WMO weather codes — see `app/services/wmo_weather_codes.py`). `outlook` is
`null` when no cached forecast hour falls within ~3 hours of `at` (e.g. a flight booked far enough out
that it's past Open-Meteo's forecast horizon).

**Response `404`** — unknown airport code, or the airport has no known coordinates.

## Error shape

All error responses follow FastAPI's default shape:
```json
{ "detail": "human-readable message" }
```

## Changing this API

If you change a response shape, update this doc, the Pydantic schema in `backend/app/schemas/`, and the
frontend types in `frontend/src/api/client.ts` in the same PR — see [`CONTRIBUTING.md`](../CONTRIBUTING.md).
