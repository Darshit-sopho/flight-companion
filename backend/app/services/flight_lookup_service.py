"""Resolves a flight number + date into a stable internal flight_id, and owns the AeroAPI-response ->
FlightSnapshot mapping used by both search and status refresh.
"""

from __future__ import annotations

from datetime import date as date_cls

from sqlalchemy.orm import Session

from app.clients.aeroapi_client import AeroAPIClient, AeroAPINotFoundError
from app.config import get_settings
from app.core.cache import ttl_from_now
from app.core.time import ensure_aware, utcnow
from app.db.models import FlightSnapshot
from app.services.utils import compute_delay_minutes, map_status, parse_dt

_SECONDS_PER_MINUTE = 60


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
    return upsert_snapshot_from_aeroapi(db, aeroapi, flight_id, ident, date_str, raw)


def _airport_fields(airport: dict | None) -> dict:
    airport = airport or {}
    return {
        "code": airport.get("code"),
        "iata": airport.get("code_iata"),
        "name": airport.get("name"),
        "city": airport.get("city"),
        "timezone": airport.get("timezone"),
    }


def _apply_diverted_info(snapshot: FlightSnapshot, aeroapi: AeroAPIClient, raw: dict) -> None:
    """Populate the diverted_* columns from a SECOND AeroAPI call keyed on fa_flight_id — see
    docs/features/status-card-requirements.md#SC-A4.3 for why a second call is unavoidable: querying by
    ident+date only ever returns the originally-filed record, never the actual outcome.
    """
    fa_flight_id = raw.get("fa_flight_id")
    if not fa_flight_id:
        return
    try:
        actual = aeroapi.get_flight_by_id(fa_flight_id)
    except AeroAPINotFoundError:
        return

    diverted_destination = _airport_fields(actual.get("destination"))
    snapshot.diverted_destination_code = diverted_destination["code"]
    snapshot.diverted_destination_iata = diverted_destination["iata"]
    snapshot.diverted_destination_name = diverted_destination["name"]
    snapshot.diverted_destination_city = diverted_destination["city"]
    snapshot.diverted_destination_timezone = diverted_destination["timezone"]
    snapshot.diverted_scheduled_arrival = parse_dt(actual.get("scheduled_in") or actual.get("scheduled_on"))
    snapshot.diverted_estimated_arrival = parse_dt(actual.get("estimated_in") or actual.get("estimated_on"))
    snapshot.diverted_actual_arrival = parse_dt(actual.get("actual_in") or actual.get("actual_on"))
    snapshot.diverted_arrival_gate = actual.get("gate_destination")
    snapshot.diverted_arrival_terminal = actual.get("terminal_destination")


def upsert_snapshot_from_aeroapi(
    db: Session, aeroapi: AeroAPIClient, flight_id: str, ident: str, date_str: str, raw: dict
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
    origin = _airport_fields(raw.get("origin"))
    destination = _airport_fields(raw.get("destination"))
    filed_ete_seconds = raw.get("filed_ete")

    snapshot.ident = ident.upper()
    snapshot.fa_flight_id = raw.get("fa_flight_id")
    snapshot.operator_icao = raw.get("operator_icao")
    snapshot.operator_iata = raw.get("operator_iata")
    snapshot.operating_ident_icao = raw.get("ident_icao")
    snapshot.scheduled_date = scheduled_date

    snapshot.origin_code = origin["code"]
    snapshot.origin_iata = origin["iata"]
    snapshot.origin_name = origin["name"]
    snapshot.origin_city = origin["city"]
    snapshot.origin_timezone = origin["timezone"]

    snapshot.destination_code = destination["code"]
    snapshot.destination_iata = destination["iata"]
    snapshot.destination_name = destination["name"]
    snapshot.destination_city = destination["city"]
    snapshot.destination_timezone = destination["timezone"]

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
    snapshot.progress_percent = raw.get("progress_percent")
    snapshot.flight_duration_minutes = (
        round(filed_ete_seconds / _SECONDS_PER_MINUTE) if filed_ete_seconds is not None else None
    )
    snapshot.route_distance = raw.get("route_distance")
    snapshot.fetched_at = utcnow()
    snapshot.expires_at = ttl_from_now(ttl_seconds)

    if raw.get("diverted"):
        _apply_diverted_info(snapshot, aeroapi, raw)

    db.commit()
    db.refresh(snapshot)
    return snapshot
