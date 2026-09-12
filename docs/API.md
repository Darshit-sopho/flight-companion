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
  "origin": { "code": "SFO", "gate": "A12", "terminal": "2" },
  "destination": { "code": "ORD", "gate": null, "terminal": "1" },
  "scheduled_departure": "2026-09-12T14:30:00-07:00",
  "estimated_departure": "2026-09-12T14:45:00-07:00",
  "actual_departure": "2026-09-12T14:47:00-07:00",
  "scheduled_arrival": "2026-09-12T20:10:00-05:00",
  "estimated_arrival": "2026-09-12T20:22:00-05:00",
  "actual_arrival": null,
  "delay_minutes": 12,
  "aircraft": { "registration": "N12345", "type": "B738" }
}
```

`status` is one of `scheduled | active | landed | cancelled | diverted`. Any field AeroAPI hasn't populated
yet (e.g. `actual_arrival` before landing) is `null` — the frontend renders this as "not yet available," not
as an error.

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

## Error shape

All error responses follow FastAPI's default shape:
```json
{ "detail": "human-readable message" }
```

## Changing this API

If you change a response shape, update this doc, the Pydantic schema in `backend/app/schemas/`, and the
frontend types in `frontend/src/api/client.ts` in the same PR — see [`CONTRIBUTING.md`](../CONTRIBUTING.md).
