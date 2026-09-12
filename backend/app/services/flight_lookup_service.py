"""Resolves a flight number + date into a stable internal flight_id, and owns the AeroAPI-response ->
FlightSnapshot mapping used by both search and status refresh.
"""

from __future__ import annotations

from datetime import date as date_cls

from sqlalchemy.orm import Session

from app.clients.aeroapi_client import AeroAPIClient
from app.config import get_settings
from app.core.cache import ttl_from_now
from app.core.time import ensure_aware, utcnow
from app.db.models import FlightSnapshot
from app.services.utils import compute_delay_minutes, map_status, parse_dt


def make_flight_id(ident: str, date_str: str) -> str:
    return f"{ident.upper()}-{date_str}"


def search_flight(db: Session, aeroapi: AeroAPIClient, ident: str, date_str: str) -> FlightSnapshot:
    """Entry point for GET /api/flights/search. Raises AeroAPINotFoundError via the client if AeroAPI
    has no matching flight — callers (routers) translate that into a 404.
    """
    flight_id = make_flight_id(ident, date_str)
    existing = db.get(FlightSnapshot, flight_id)
    if existing is not None and ensure_aware(existing.expires_at) > utcnow():
        return existing

    raw = aeroapi.get_flight(ident, date_str)
    return upsert_snapshot_from_aeroapi(db, flight_id, ident, date_str, raw)


def upsert_snapshot_from_aeroapi(
    db: Session, flight_id: str, ident: str, date_str: str, raw: dict
) -> FlightSnapshot:
    settings = get_settings()
    scheduled_date = date_cls.fromisoformat(date_str)
    is_fully_elapsed = scheduled_date < date_cls.today()
    ttl_seconds = (
        settings.aeroapi_history_cache_ttl_seconds * 52  # effectively "forever" for elapsed flights
        if is_fully_elapsed
        else settings.aeroapi_status_cache_ttl_seconds
    )

    snapshot = db.get(FlightSnapshot, flight_id)
    if snapshot is None:
        snapshot = FlightSnapshot(flight_id=flight_id)
        db.add(snapshot)

    scheduled_departure = parse_dt(raw.get("scheduled_out"))
    actual_or_estimated_departure = parse_dt(raw.get("actual_out")) or parse_dt(raw.get("estimated_out"))

    snapshot.ident = ident.upper()
    snapshot.scheduled_date = scheduled_date
    snapshot.origin_code = (raw.get("origin") or {}).get("code")
    snapshot.destination_code = (raw.get("destination") or {}).get("code")
    snapshot.registration = raw.get("registration")
    snapshot.aircraft_type = raw.get("aircraft_type")
    snapshot.scheduled_departure = scheduled_departure
    snapshot.estimated_departure = parse_dt(raw.get("estimated_out"))
    snapshot.actual_departure = parse_dt(raw.get("actual_out"))
    snapshot.scheduled_arrival = parse_dt(raw.get("scheduled_in"))
    snapshot.estimated_arrival = parse_dt(raw.get("estimated_in"))
    snapshot.actual_arrival = parse_dt(raw.get("actual_in"))
    snapshot.departure_gate = raw.get("gate_origin")
    snapshot.departure_terminal = raw.get("terminal_origin")
    snapshot.arrival_gate = raw.get("gate_destination")
    snapshot.arrival_terminal = raw.get("terminal_destination")
    snapshot.status = map_status(raw.get("status"))
    snapshot.delay_minutes = compute_delay_minutes(scheduled_departure, actual_or_estimated_departure)
    snapshot.fetched_at = utcnow()
    snapshot.expires_at = ttl_from_now(ttl_seconds)

    db.commit()
    db.refresh(snapshot)
    return snapshot
