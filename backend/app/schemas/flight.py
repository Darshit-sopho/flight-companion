"""Pydantic response DTOs. Kept separate from the SQLAlchemy models in app/db/models.py so the API
contract (docs/API.md) can evolve independently of storage shape. If you change one of these, update
docs/API.md and frontend/src/api/client.ts in the same change — see CONTRIBUTING.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class FlightSearchResponse(BaseModel):
    flight_id: str
    ident: str
    origin: str | None
    destination: str | None
    scheduled_departure: datetime | None

    @classmethod
    def from_snapshot(cls, snapshot) -> FlightSearchResponse:
        return cls(
            flight_id=snapshot.flight_id,
            ident=snapshot.ident,
            origin=snapshot.origin_code,
            destination=snapshot.destination_code,
            scheduled_departure=snapshot.scheduled_departure,
        )


class AirportRef(BaseModel):
    code: str | None
    gate: str | None = None
    terminal: str | None = None


class AircraftRef(BaseModel):
    registration: str | None = None
    type: str | None = None


class FlightStatusResponse(BaseModel):
    flight_id: str
    ident: str
    status: Literal["scheduled", "active", "landed", "cancelled", "diverted"]
    origin: AirportRef
    destination: AirportRef
    scheduled_departure: datetime | None
    estimated_departure: datetime | None
    actual_departure: datetime | None
    scheduled_arrival: datetime | None
    estimated_arrival: datetime | None
    actual_arrival: datetime | None
    delay_minutes: int | None
    aircraft: AircraftRef

    @classmethod
    def from_snapshot(cls, s) -> FlightStatusResponse:
        return cls(
            flight_id=s.flight_id,
            ident=s.ident,
            status=s.status.value if hasattr(s.status, "value") else s.status,
            origin=AirportRef(code=s.origin_code, gate=s.departure_gate, terminal=s.departure_terminal),
            destination=AirportRef(code=s.destination_code, gate=s.arrival_gate, terminal=s.arrival_terminal),
            scheduled_departure=s.scheduled_departure,
            estimated_departure=s.estimated_departure,
            actual_departure=s.actual_departure,
            scheduled_arrival=s.scheduled_arrival,
            estimated_arrival=s.estimated_arrival,
            actual_arrival=s.actual_arrival,
            delay_minutes=s.delay_minutes,
            aircraft=AircraftRef(registration=s.registration, type=s.aircraft_type),
        )


class HistoryOccurrence(BaseModel):
    date: str | None
    delay_minutes: int | None
    on_time: bool | None


class FlightHistoryResponse(BaseModel):
    flight_id: str
    on_time_percentage: float | None
    average_delay_minutes: float | None
    trend: Literal["improving", "worsening", "stable"]
    occurrences: list[HistoryOccurrence]


class Position(BaseModel):
    lat: float
    lon: float
    altitude_ft: float | None
    ground_speed_kt: float | None
    heading_deg: float | None
    on_ground: bool
    recorded_at: str


class Resolution(BaseModel):
    method: str | None
    confidence: str | None


class TrackResponse(BaseModel):
    state: Literal["tracking", "not_airborne", "landed", "unavailable"]
    position: Position | None = None
    resolution: Resolution | None = None


class AirportResponse(BaseModel):
    code: str
    name: str | None
    city: str | None
    country: str | None
    timezone: str | None
    local_time: str | None

    @classmethod
    def from_model(cls, airport) -> AirportResponse:
        local_time = None
        if airport.timezone:
            from zoneinfo import ZoneInfo

            local_time = datetime.now(ZoneInfo(airport.timezone)).isoformat()
        return cls(
            code=airport.code,
            name=airport.name,
            city=airport.city,
            country=airport.country,
            timezone=airport.timezone,
            local_time=local_time,
        )
