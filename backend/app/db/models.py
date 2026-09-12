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
    operator_icao: Mapped[str | None] = mapped_column(String(8))
    scheduled_date: Mapped[date] = mapped_column(Date)

    origin_code: Mapped[str | None] = mapped_column(String(8))
    destination_code: Mapped[str | None] = mapped_column(String(8))

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
