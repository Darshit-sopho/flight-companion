"""Pydantic response DTOs. Kept separate from the SQLAlchemy models in app/db/models.py so the API
contract (docs/API.md) can evolve independently of storage shape. If you change one of these, update
docs/API.md and frontend/src/api/client.ts in the same change — see CONTRIBUTING.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.services.operator_names import get_operator_name


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
    # IATA code (e.g. "EWR") and common name/city — the identity travelers actually recognize, per
    # docs/features/status-card-requirements.md#SC-E2. `code` remains the ICAO code (e.g. "KEWR") for
    # secondary/technical display.
    iata: str | None = None
    name: str | None = None
    city: str | None = None
    timezone: str | None = None
    gate: str | None = None
    terminal: str | None = None


class AircraftRef(BaseModel):
    registration: str | None = None
    type: str | None = None


class OperatorRef(BaseModel):
    """The operating carrier — may differ from the searched ident for codeshares (see
    docs/ARCHITECTURE.md#aeroapi--opensky-linking and SC-C1). `name` is best-effort from a small static
    lookup table (app/services/operator_names.py); `None` when the code isn't in that table.
    """

    icao: str | None = None
    iata: str | None = None
    name: str | None = None


class DivertedInfo(BaseModel):
    """Present only when `status = diverted` — see SC-A4. `airport` is the actual landing airport
    (distinct from `FlightStatusResponse.destination`, which stays the originally-filed destination so
    the frontend can show both).
    """

    airport: AirportRef
    scheduled_arrival: datetime | None
    estimated_arrival: datetime | None
    actual_arrival: datetime | None


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
    operator: OperatorRef | None = None
    progress_percent: int | None = None
    flight_duration_minutes: int | None = None
    route_distance: int | None = None
    diverted: DivertedInfo | None = None

    @classmethod
    def from_snapshot(cls, s) -> FlightStatusResponse:
        operator = None
        if s.operator_icao or s.operator_iata:
            operator = OperatorRef(
                icao=s.operator_icao,
                iata=s.operator_iata,
                name=get_operator_name(s.operator_icao),
            )

        diverted = None
        if s.status == "diverted" and s.diverted_destination_code:
            diverted = DivertedInfo(
                airport=AirportRef(
                    code=s.diverted_destination_code,
                    iata=s.diverted_destination_iata,
                    name=s.diverted_destination_name,
                    city=s.diverted_destination_city,
                    timezone=s.diverted_destination_timezone,
                    gate=s.diverted_arrival_gate,
                    terminal=s.diverted_arrival_terminal,
                ),
                scheduled_arrival=s.diverted_scheduled_arrival,
                estimated_arrival=s.diverted_estimated_arrival,
                actual_arrival=s.diverted_actual_arrival,
            )

        return cls(
            flight_id=s.flight_id,
            ident=s.ident,
            status=s.status.value if hasattr(s.status, "value") else s.status,
            origin=AirportRef(
                code=s.origin_code,
                iata=s.origin_iata,
                name=s.origin_name,
                city=s.origin_city,
                timezone=s.origin_timezone,
                gate=s.departure_gate,
                terminal=s.departure_terminal,
            ),
            destination=AirportRef(
                code=s.destination_code,
                iata=s.destination_iata,
                name=s.destination_name,
                city=s.destination_city,
                timezone=s.destination_timezone,
                gate=s.arrival_gate,
                terminal=s.arrival_terminal,
            ),
            scheduled_departure=s.scheduled_departure,
            estimated_departure=s.estimated_departure,
            actual_departure=s.actual_departure,
            scheduled_arrival=s.scheduled_arrival,
            estimated_arrival=s.estimated_arrival,
            actual_arrival=s.actual_arrival,
            delay_minutes=s.delay_minutes,
            aircraft=AircraftRef(registration=s.registration, type=s.aircraft_type),
            operator=operator,
            progress_percent=s.progress_percent,
            flight_duration_minutes=s.flight_duration_minutes,
            route_distance=s.route_distance,
            diverted=diverted,
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
