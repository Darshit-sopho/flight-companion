"""SQLAlchemy ORM models — the schema of record. See docs/ARCHITECTURE.md#data-model for the rationale
behind each table, and docs/adr/0003-no-auth-mvp.md for why there are no user/session tables.
"""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.db.base import Base


class FlightStatus(enum.StrEnum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    LANDED = "landed"
    CANCELLED = "cancelled"
    DIVERTED = "diverted"


class ResolutionMethod(enum.StrEnum):
    REGISTRATION_LOOKUP = "registration_lookup"
    CALLSIGN_FALLBACK = "callsign_fallback"
    UNRESOLVED = "unresolved"


class ResolutionConfidence(enum.StrEnum):
    HIGH = "high"
    LOW = "low"
    NONE = "none"


class Airport(Base):
    """Static reference data. Effectively permanent cache — see docs/DATA_SOURCES.md#cost-control."""

    __tablename__ = "airport"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(4))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    timezone: Mapped[str | None] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AircraftRegistry(Base):
    """icao24 <-> registration mapping, synced from OpenSky's public aircraft database dump.

    This is what lets icao24_resolver avoid a live reverse-lookup call on every resolution.
    """

    __tablename__ = "aircraft_registry"

    icao24: Mapped[str] = mapped_column(String(6), primary_key=True)
    registration: Mapped[str | None] = mapped_column(String(16), index=True)
    model: Mapped[str | None] = mapped_column(String(64))
    manufacturer: Mapped[str | None] = mapped_column(String(64))
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FlightSnapshot(Base):
    """Cached current status for one flight instance (one ident + one scheduled date).

    fetched_at/expires_at drive the AeroAPI cache-TTL logic in flight_status_service; last_viewed_at
    drives the "only refresh what's actively being looked at" rule — see docs/DATA_SOURCES.md#cost-control.
    """

    __tablename__ = "flight_snapshot"

    flight_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ident: Mapped[str] = mapped_column(String(16), index=True)
    # AeroAPI's own flight-instance identifier — needed to make the second, diverted-flight-specific
    # lookup in live_tracking's sibling, flight_lookup_service (see diverted_* fields below and
    # docs/features/status-card-requirements.md#SC-A4.3).
    fa_flight_id: Mapped[str | None] = mapped_column(String(64))
    operator_icao: Mapped[str | None] = mapped_column(String(8))
    operator_iata: Mapped[str | None] = mapped_column(String(8))
    # The operating carrier's full ICAO flight ident (AeroAPI's `ident_icao`, e.g. "RPA3513"), distinct
    # from `ident` (what the user searched, e.g. the marketing/codeshare number "UA3513"). This is what
    # actually gets broadcast over ADS-B as the callsign, so icao24_resolver's callsign fallback must
    # try this too, not just `ident` — see docs/ARCHITECTURE.md#aeroapi--opensky-linking.
    operating_ident_icao: Mapped[str | None] = mapped_column(String(16))
    scheduled_date: Mapped[date] = mapped_column(Date)

    # AeroAPI's flight-status response already embeds iata/name/city/timezone directly on the
    # origin/destination sub-objects of the same response we already fetch for status — capturing them
    # here means the status card can show traveler-friendly airport identity (docs/features/
    # status-card-requirements.md#SC-E2) and per-leg local times (#SC-B1) without any extra AeroAPI call.
    origin_code: Mapped[str | None] = mapped_column(String(8))
    origin_iata: Mapped[str | None] = mapped_column(String(4))
    origin_name: Mapped[str | None] = mapped_column(String(200))
    origin_city: Mapped[str | None] = mapped_column(String(100))
    origin_timezone: Mapped[str | None] = mapped_column(String(64))

    destination_code: Mapped[str | None] = mapped_column(String(8))
    destination_iata: Mapped[str | None] = mapped_column(String(4))
    destination_name: Mapped[str | None] = mapped_column(String(200))
    destination_city: Mapped[str | None] = mapped_column(String(100))
    destination_timezone: Mapped[str | None] = mapped_column(String(64))

    registration: Mapped[str | None] = mapped_column(String(16))
    aircraft_type: Mapped[str | None] = mapped_column(String(16))

    scheduled_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scheduled_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    departure_gate: Mapped[str | None] = mapped_column(String(16))
    departure_terminal: Mapped[str | None] = mapped_column(String(8))
    arrival_gate: Mapped[str | None] = mapped_column(String(16))
    arrival_terminal: Mapped[str | None] = mapped_column(String(8))

    status: Mapped[FlightStatus] = mapped_column(SAEnum(FlightStatus), default=FlightStatus.SCHEDULED)
    delay_minutes: Mapped[int | None] = mapped_column(Integer)

    # Phase A: flight progress (docs/features/status-card-requirements.md#SC-A1).
    progress_percent: Mapped[int | None] = mapped_column(Integer)
    # Phase C: richer flight info (#SC-C1-C3). filed_ete arrives from AeroAPI in seconds; stored here
    # already converted to minutes since nothing downstream needs the raw seconds value.
    flight_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    route_distance: Mapped[int | None] = mapped_column(Integer)

    # Phase A: diverted-flight support (#SC-A4). Populated only when `status = diverted`, from a SECOND
    # AeroAPI call keyed on fa_flight_id — see flight_lookup_service.py and SC-A4.3 for why a second call
    # is unavoidable here. The origin_*/destination_* columns above stay as the ORIGINALLY FILED route;
    # these columns hold the actual diverted-to destination, kept deliberately separate rather than
    # overwriting destination_* so the UI can show both (grayed-out original + new column).
    diverted_destination_code: Mapped[str | None] = mapped_column(String(8))
    diverted_destination_iata: Mapped[str | None] = mapped_column(String(4))
    diverted_destination_name: Mapped[str | None] = mapped_column(String(200))
    diverted_destination_city: Mapped[str | None] = mapped_column(String(100))
    diverted_destination_timezone: Mapped[str | None] = mapped_column(String(64))
    diverted_scheduled_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    diverted_estimated_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    diverted_actual_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    diverted_arrival_gate: Mapped[str | None] = mapped_column(String(16))
    diverted_arrival_terminal: Mapped[str | None] = mapped_column(String(8))

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FlightHistoryRecord(Base):
    """One row per past occurrence of a flight number/route. Long-lived cache — see
    docs/DATA_SOURCES.md#cost-control (a fully-elapsed occurrence never needs re-fetching).
    """

    __tablename__ = "flight_history_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ident: Mapped[str] = mapped_column(String(16), index=True)
    route_origin: Mapped[str | None] = mapped_column(String(8))
    route_destination: Mapped[str | None] = mapped_column(String(8))
    flight_date: Mapped[date] = mapped_column(Date, index=True)
    scheduled_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delay_minutes: Mapped[int | None] = mapped_column(Integer)
    on_time: Mapped[bool | None] = mapped_column(Boolean)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LivePosition(Base):
    """Append-only live position log per flight instance, sourced exclusively from OpenSky.
    Also usable as a breadcrumb trail for the map.
    """

    __tablename__ = "live_position"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flight_id: Mapped[str] = mapped_column(ForeignKey("flight_snapshot.flight_id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    altitude_ft: Mapped[float | None] = mapped_column(Float)
    ground_speed_kt: Mapped[float | None] = mapped_column(Float)
    heading_deg: Mapped[float | None] = mapped_column(Float)
    on_ground: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(16), default="opensky")


class TrackedFlight(Base):
    """icao24 resolution state for one flight instance, kept separate from FlightSnapshot so the
    AeroAPI-derived status data and the OpenSky-linking state machine don't get tangled together.
    """

    __tablename__ = "tracked_flight"

    flight_id: Mapped[str] = mapped_column(ForeignKey("flight_snapshot.flight_id"), primary_key=True)
    resolved_icao24: Mapped[str | None] = mapped_column(String(6))
    resolution_method: Mapped[str | None] = mapped_column(String(32))
    resolution_confidence: Mapped[str | None] = mapped_column(String(8))
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    polling_active: Mapped[bool] = mapped_column(Boolean, default=True)
